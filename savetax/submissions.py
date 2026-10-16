"""공식 fact와 실측 가격으로 점수 본문을 만들고 preview 뒤 제출한다."""
from datetime import datetime
from decimal import Decimal
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
    if offer.get('price_verified') is not True or offer.get('model_verified') is not True:
        raise ValueError('실측 판매가와 실제 발송 모델 확인이 필요합니다')
    model = canonical_model(item.get('snapshot',{}).get('model',''))
    if not model or canonical_model(offer.get('model','')) != model:
        raise ValueError('조달 모델과 실제 판매 모델이 다릅니다')
    if not _source_valid(offer.get('url')) or not isinstance(offer.get('quote'),str) or not 1 <= len(offer['quote']) <= 2000:
        raise ValueError('공개 HTTPS 판매 페이지와 직접 확인한 인용이 필요합니다')
    if any(type(offer.get(key)) is not bool for key in ('vat_included','shipping_included')):
        raise ValueError('세금·배송 기준을 명시해야 합니다')
    price = str(offer.get('unit_price',''))
    benchmark = str(offer.get('benchmark_unit_price_krw',price))
    if not re.fullmatch(r'[0-9]+',price) or Decimal(price) <= 0:
        raise ValueError('관측가는 양의 정수 원화여야 합니다')
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',benchmark) or Decimal(benchmark) < Decimal(price):
        raise ValueError('비교 단가는 관측가 이상의 십진 문자열이어야 합니다')
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
                'shipping_included':offer['shipping_included']}],
            'fulfillment_evidence':[{'kind':'text','text':f"계약 {fact['contract_no']}, 납품요구 {fact['request_no']}, 라인 {fact['line_no']}. 공식 fact {fact['fact_id']}, 수량 {fact['quantity']}, 비교금액 {fact['comparable_amount_krw']}원."}]})
    if not lines:
        raise ValueError('양의 절감액이 있는 공식 fact가 없습니다')
    body = {'dataset_release_id':event['dataset_release_id'],'ruleset_version':event['ruleset_version'],
        'canonical_product_id':item['item_id'], 'title':f'{model} 국내 실판매가 {price}원 비교'[:200],
        'claim':'실제 판매 상세의 동일 모델·구성과 일반 구매 가격을 확인했다.',
        'comparison_scope':offer.get('comparison_scope','동일 모델 신품, 공식 fact의 단위·세금 기준 비교'),
        'reproduction_notes':'공식 fact별 floor(max(C-B×Q,0))를 합산. 각 라인 근거에 계약·납품요구·라인 번호를 기재. 가격 시점 차이는 사용자 지정 대회 조사 기준에서 제외한다.',
        'lines':lines}
    if len(json.dumps(body,ensure_ascii=False).encode()) > 1048576:
        raise ValueError('점수 본문 1MiB 초과; 명시적 fact 범위 분리가 필요합니다')
    return body


class ScoreClient:
    def __init__(self, client: SaveTaxClient):
        self.client = client

    def _post(self, suffix, body, key=None):
        if suffix not in ('/submissions/preview','/submissions'):
            raise ValueError('허용되지 않은 점수 경로')
        if TOKEN_PATTERN.search(json.dumps(body,ensure_ascii=False)):
            raise ValueError('본문에 비밀 문자열을 넣을 수 없습니다')
        headers = {'Authorization':'Bearer '+self.client._token,'User-Agent':'Mozilla/5.0','Accept':'application/json'}
        if key is not None:
            if not re.fullmatch(r'[A-Za-z0-9_-]{8,100}',key):
                raise ValueError('안정된 멱등 키가 필요합니다')
            headers['Idempotency-Key'] = key
        response,error = None,None
        try:
            response = requests.post(BASE+suffix,json=body,headers=headers,
                timeout=self.client.timeout,allow_redirects=False)
        except requests.RequestException:
            error = SaveTaxError('점수 요청 연결 결과 미확인; 같은 멱등 키로 결과를 확인하세요',stage='transport')
        if error:
            raise error from None
        try:
            try:
                result = response.json()
            except ValueError:
                result = {}
            if not isinstance(result,dict):
                result = {}
            if response.status_code not in (200,201):
                code = result.get('code','http_error')
                if not isinstance(code,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,79}',code) or TOKEN_PATTERN.search(code):
                    code = 'http_error'
                error = SaveTaxError(f'점수 요청 HTTP {response.status_code} ({code})',status=response.status_code,code=code,stage='http')
        finally:
            response.close()
        if error:
            raise error from None
        return _redact(result,self.client._token)

    def preview(self, body):
        return self._post('/submissions/preview',body)

    def submit(self, body, idempotency_key, preview):
        if preview.get('ok') is not True or preview.get('next_action') != 'submit':
            raise ValueError('점수 제출 가능한 preview 결과가 필요합니다')
        lookup = self.client.get_json(BASE+'/items/lookup',params={'ids':body['canonical_product_id']})
        if not lookup.get('items') or lookup['items'][0].get('state') != 'available':
            raise ValueError('물품이 이미 등록되었거나 현재 등록할 수 없습니다')
        return self._post('/submissions',body,idempotency_key)
