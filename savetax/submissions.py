"""공식 fact와 실측 가격으로 점수 본문을 만들고 preview 뒤 제출한다."""
from datetime import datetime
from decimal import Decimal, ROUND_CEILING
import json
import re

import requests

from .client import SaveTaxClient, SaveTaxError, TOKEN_PATTERN, _redact
from .evidence import _source_valid

BASE = 'https://hackathon.savetax.now/v1/events/current'


def canonical_model(value):
    """카탈로그 원산지 접두사만 분리한다. 모델 suffix는 보존한다."""
    return re.sub(r'^\((?:CN|VN|KR|US|TW|JP|MY|TH|PH|ID|DE|GB)\)\s*', '', value).strip()


def build_submission(item, offer, event):
    if item.get('availability',{}).get('state') != 'available':
        raise ValueError('미등록 available 물품만 신규 점수 대상입니다')
    kind = offer.get('comparison_kind','identical')
    if kind not in ('identical','equivalent'):
        raise ValueError('비교 유형은 identical 또는 equivalent여야 합니다')
    equivalent = kind == 'equivalent'
    model_check = 'retail_model_verified' if equivalent else 'model_verified'
    if offer.get('price_verified') is not True or offer.get(model_check) is not True:
        raise ValueError('실측 판매가와 실제 판매 모델 확인이 필요합니다')
    model = canonical_model(item.get('snapshot',{}).get('model',''))
    retail_model = canonical_model(offer.get('model',''))
    if not model or not retail_model:
        raise ValueError('조달 모델과 실제 판매 모델이 필요합니다')
    if equivalent:
        mapping = offer.get('spec_mapping')
        sources = offer.get('spec_source_urls')
        if (offer.get('comparison_reviewed') is not True
                or canonical_model(offer.get('procurement_model','')) != model
                or not isinstance(mapping,list) or not 1 <= len(mapping) <= 30
                or any(not isinstance(row,dict) or any(not isinstance(row.get(k),str)
                    or not row[k].strip() for k in ('attribute','original','alternative')) for row in mapping)
                or not isinstance(sources,list) or not 1 <= len(sources) <= 20
                or any(not _source_valid(url) for url in sources)
                or not isinstance(offer.get('differences'),str) or not offer['differences'].strip()):
            raise ValueError('대체 비교는 원모델·사양 대응·공개 출처·차이와 비교 검토가 필요합니다')
        assessment = offer.get('comparison_assessment')
        if not isinstance(assessment,dict):
            raise ValueError('대체 비교의 핵심 용도·완제품 구성 검토 근거가 필요합니다')
        assessment_notes = []
        for key,label in (('core_purpose','핵심 용도'),('complete_product','완제품 구성')):
            check = assessment.get(key)
            if (not isinstance(check,dict) or check.get('status') != 'verified'
                    or not isinstance(check.get('basis'),str) or not check['basis'].strip()):
                raise ValueError(f'대체 비교의 {label} 대응이 미확인입니다')
            assessment_notes.append(label + ': ' + check['basis'].strip())
    elif retail_model != model:
        raise ValueError('조달 모델과 실제 판매 모델이 다릅니다')
    if not _source_valid(offer.get('url')) or not isinstance(offer.get('quote'),str) or not 1 <= len(offer['quote']) <= 2000:
        raise ValueError('공개 HTTPS 판매 페이지와 직접 확인한 인용이 필요합니다')
    if any(type(offer.get(key)) is not bool for key in ('vat_included','shipping_included')):
        raise ValueError('세금·배송 기준을 명시해야 합니다')
    price = str(offer.get('unit_price',''))
    if not re.fullmatch(r'[0-9]+',price) or Decimal(price) <= 0:
        raise ValueError('관측가는 양의 정수 원화여야 합니다')
    pack = offer.get('pack_quantity',1)
    if type(pack) is not int or not 1 <= pack <= 1000000:
        raise ValueError('판매 포장 수량은 양의 정수여야 합니다')
    if pack > 1 and offer.get('pack_quantity_verified') is not True:
        raise ValueError('포장 안의 공식 비교 단위 수량을 실제로 확인해야 합니다')
    unit_price = (Decimal(price)/pack).quantize(Decimal('0.000001'),rounding=ROUND_CEILING)
    normalized = format(unit_price,'f').rstrip('0').rstrip('.')
    benchmark = str(offer.get('benchmark_unit_price_krw',normalized))
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',benchmark) or Decimal(benchmark) < unit_price:
        raise ValueError('비교 단가는 포장 수량으로 환산한 관측가 이상이어야 합니다')
    try:
        observed_at = datetime.fromisoformat(offer['observed_at'].replace('Z','+00:00')).date().isoformat()
    except (ValueError,KeyError,AttributeError):
        raise ValueError('가격 관측일이 필요합니다') from None
    lines, seen = [], set()
    for fact in item.get('facts',[]):
        if not fact.get('scorable') or fact['fact_id'] in seen:
            continue
        if Decimal(fact['comparable_amount_krw']) <= Decimal(benchmark)*Decimal(fact['quantity']):
            continue
        if fact.get('period_kind') not in (None,'none'):
            raise ValueError('기간형 물품은 별도 기간 검증이 필요합니다')
        if fact.get('tax_basis') != ('vat_included' if offer['vat_included'] else 'vat_excluded'):
            raise ValueError('공식 fact와 판매가의 세금 기준이 다릅니다')
        if any(not str(fact.get(key,'')) for key in ('contract_no','request_no','line_no')):
            raise ValueError('계약번호·납품요구번호·라인 번호가 필요합니다')
        seen.add(fact['fact_id'])
        lines.append({'fact_id':fact['fact_id'], 'benchmark_unit_price_krw':benchmark,
            'comparison_basis_id':fact['basis_id'], 'unit':fact['unit'], 'tax_basis':fact['tax_basis'], 'period':None,
            'price_evidence':[{'kind':'price_page','source_url':offer['url'],'quote':offer['quote'],
                'observed_price_krw':price,'observed_at':observed_at,'vat_included':offer['vat_included'],
                'shipping_included':offer['shipping_included'],
                'note':f'표시가 {price}원/{pack}개 구성. 공식 비교 단위 1{fact["unit"]}당 {benchmark}원으로 비교.'}],
            'fulfillment_evidence':[{'kind':'text','text':f"계약 {fact['contract_no']}, 납품요구 {fact['request_no']}, 라인 {fact['line_no']}. 공식 fact {fact['fact_id']}, 수량 {fact['quantity']}, 비교금액 {fact['comparable_amount_krw']}원."}]})
    if not lines:
        raise ValueError('양의 절감액이 있는 공식 fact가 없습니다')
    body = {'dataset_release_id':event['dataset_release_id'],'ruleset_version':event['ruleset_version'],
        'canonical_product_id':item['item_id'], 'title':f'{model} 국내 실판매가 {price}원 비교'[:200],
        'claim':'실제 판매 상세의 동일 모델·구성과 일반 구매 가격을 확인했다.',
        'comparison_scope':offer.get('comparison_scope',f'동일 모델 신품, 판매 포장 {pack}개 구성을 공식 fact 1개 단위·세금 기준으로 환산'),
        'reproduction_notes':'공식 fact별 floor(max(C-B×Q,0))를 합산. 각 라인 근거에 계약·납품요구·라인 번호를 기재. 가격 시점 차이는 사용자 지정 대회 조사 기준에서 제외한다.',
        'lines':lines}
    if equivalent:
        body['title'] = f'{model} → {retail_model} 대체품 {price}원 비교'[:200]
        body['claim'] = f'조달 {model}과 실제 판매 {retail_model}의 핵심사양 대체 비교다. 제조사·모델 동일성을 주장하지 않는다. {offer["differences"]}'
        scope = offer.get('comparison_scope','핵심사양 대체품의 제품 취득가격 비교')
        identity = f' 원품 {model}, 대체품 {retail_model}.'
        detailed = scope + identity + f' 차이·제한: {offer["differences"]}'
        # 차이를 자르지 않는다. 긴 설명은 claim에 온전히 보존하고 짧은 범위와 분리한다.
        body['comparison_scope'] = (detailed if len(detailed) <= 1000
            else scope + identity + ' 세부 차이·제한은 주장과 재현 방법에 기재했다.')
        body['reproduction_notes'] += (' 사양 대응: '
            + '; '.join(f'{r["attribute"]}: {r["original"]} → {r["alternative"]}' for r in mapping)
            + '. 사양 출처: ' + ' '.join(sources)
            + '. 비교 검토: ' + '; '.join(assessment_notes))
        for line in lines:
            line['price_evidence'][0]['note'] += f' 실제 판매모델 {retail_model}; 원품 {model}과 다른 대체품 비교.'
    for field, limit in (('title',200),('claim',2000),('comparison_scope',1000),('reproduction_notes',4000)):
        if not isinstance(body[field],str) or not body[field].strip() or len(body[field]) > limit:
            raise ValueError(f'{field}는 비어 있지 않은 {limit}자 이하 문자열이어야 합니다. 근거를 자르지 말고 요약·분리하세요')
    if any(len(e['note']) > 500 for line in lines for e in line['price_evidence']):
        raise ValueError('가격 근거 note는 500자 이하로 요약해야 합니다')
    if len(json.dumps(body,ensure_ascii=False).encode()) > 1048576:
        raise ValueError('점수 본문 1MiB 초과; 명시적 fact 범위 분리가 필요합니다')
    return body


class ScoreClient:
    def __init__(self, client: SaveTaxClient):
        self.client = client

    @staticmethod
    def _validate_key(key):
        if not isinstance(key,str) or not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',key):
            raise ValueError('안정된 멱등 키가 필요합니다')

    @staticmethod
    def _require_receipt(result):
        submission_id = result.get('submission_id') if isinstance(result,dict) else None
        if (not isinstance(submission_id,str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',submission_id)
                or TOKEN_PATTERN.search(submission_id)):
            raise SaveTaxError('점수 접수 영수증 미확인; 같은 멱등 키로 결과를 확인하세요',stage='decode')
        return result

    def recover_request(self, idempotency_key):
        """HTTP 202는 접수 성공이 아니다. 같은 요청의 최종 결과만 복구한다."""
        self._validate_key(idempotency_key)
        try:
            response = self.client._get(BASE+'/submission-requests/'+idempotency_key)
        except SaveTaxError as error:
            if error.status == 404:
                return {'state':'not_found'}
            raise
        error, result = None, None
        try:
            if response.status_code == 202:
                return {'state':'pending'}
            if response.status_code != 200:
                error = SaveTaxError('점수 접수 결과 상태 미확인',status=response.status_code,stage='http')
            else:
                try:
                    result = self._require_receipt(response.json())
                except (ValueError,TypeError):
                    error = SaveTaxError('점수 접수 결과 해석 실패',stage='decode')
        finally:
            response.close()
        if error:
            raise error from None
        return {'state':'submitted','response':_redact(result,self.client._token)}

    def _post(self, suffix, body, key=None):
        if suffix not in ('/submissions/preview','/submissions'):
            raise ValueError('허용되지 않은 점수 경로')
        serialized = json.dumps(body,ensure_ascii=False,allow_nan=False,separators=(',',':'))
        if TOKEN_PATTERN.search(serialized):
            raise ValueError('본문에 비밀 문자열을 넣을 수 없습니다')
        payload = serialized.encode('utf-8')
        if len(payload) > 1048576:
            raise ValueError('점수 전송 본문 1MiB 초과; 명시적 fact 범위 분리가 필요합니다')
        headers = {'Authorization':'Bearer '+self.client._token,'User-Agent':'Mozilla/5.0',
                   'Accept':'application/json','Content-Type':'application/json'}
        if key is not None:
            self._validate_key(key)
            headers['Idempotency-Key'] = key
        elif suffix == '/submissions':
            self._validate_key(key)
        response,error = None,None
        try:
            response = requests.post(BASE+suffix,data=payload,headers=headers,
                timeout=self.client.timeout,allow_redirects=False)
        except requests.RequestException:
            error = SaveTaxError('점수 요청 연결 결과 미확인; 같은 멱등 키로 결과를 확인하세요',stage='transport')
        if error:
            raise error from None
        try:
            try:
                result = response.json()
            except (ValueError,TypeError):
                result = None
            if response.status_code not in (200,201):
                detail = result.get('error',result) if isinstance(result,dict) else {}
                code = detail.get('code','http_error') if isinstance(detail,dict) else 'http_error'
                if not isinstance(code,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}',code) or TOKEN_PATTERN.search(code):
                    code = 'http_error'
                error = SaveTaxError(f'점수 요청 HTTP {response.status_code} ({code})',status=response.status_code,code=code,stage='http')
            elif not isinstance(result,dict):
                error = SaveTaxError('점수 요청 응답 해석 실패; 같은 멱등 키로 결과를 확인하세요',stage='decode')
            elif suffix == '/submissions':
                self._require_receipt(result)
        finally:
            response.close()
        if error:
            raise error from None
        return _redact(result,self.client._token)

    def preview(self, body):
        return self._post('/submissions/preview',body)

    def submit(self, body, idempotency_key, preview):
        self._validate_key(idempotency_key)
        if not isinstance(preview,dict) or preview.get('ok') is not True or preview.get('next_action') != 'submit':
            raise ValueError('점수 제출 가능한 preview 결과가 필요합니다')
        lookup = self.client.get_json(BASE+'/items/lookup',params={'ids':body['canonical_product_id']})
        rows = lookup.get('items',[])
        matching = [row for row in rows if isinstance(row,dict)
                    and row.get('item_id') == body['canonical_product_id']] if isinstance(rows,list) else []
        if len(matching) != 1 or matching[0].get('state') != 'available':
            raise ValueError('물품이 이미 등록되었거나 현재 등록할 수 없습니다')
        return self._post('/submissions',body,idempotency_key)
