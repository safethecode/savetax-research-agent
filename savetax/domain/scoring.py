"""Pure draft assembly and official fact arithmetic. Drafts confer no approval."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, localcontext
import json
import re
from .evidence import _source_valid, _purchase_availability_reasons, is_procurement_price_url

def canonical_model(value):
    """카탈로그 원산지 접두사만 분리한다. 모델 suffix는 보존한다."""
    return re.sub(r'^\((?:CN|VN|KR|US|TW|JP|MY|TH|PH|ID|DE|GB)\)\s*', '', value).strip()


def _assemble_submission(item, offer, event, *, reviewed):
    if is_procurement_price_url(offer.get('url')):
        raise ValueError('공공조달 견적은 시중 판매가격 근거로 사용할 수 없습니다')
    if item.get('availability',{}).get('state') != 'available':
        raise ValueError('미등록 available 물품만 신규 점수 대상입니다')
    kind = offer.get('comparison_kind','identical')
    if kind not in ('identical','equivalent'):
        raise ValueError('비교 유형은 identical 또는 equivalent여야 합니다')
    equivalent = kind == 'equivalent'
    model_check = 'retail_model_verified' if equivalent else 'model_verified'
    if reviewed and (offer.get('price_verified') is not True or offer.get(model_check) is not True):
        raise ValueError('실측 판매가와 실제 판매 모델 확인이 필요합니다')
    availability_reasons = _purchase_availability_reasons(offer, datetime.now(timezone.utc))
    if availability_reasons:
        raise ValueError('선택한 판매 경로의 실제 구매 가능 근거가 필요합니다: ' + ', '.join(availability_reasons))
    model = canonical_model(item.get('snapshot',{}).get('model',''))
    retail_model = canonical_model(offer.get('model',''))
    if not model or not retail_model:
        raise ValueError('조달 모델과 실제 판매 모델이 필요합니다')
    if equivalent:
        mapping = offer.get('spec_mapping')
        sources = offer.get('spec_source_urls')
        if ((reviewed and offer.get('comparison_reviewed') is not True)
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
            if (not isinstance(check,dict) or (reviewed and check.get('status') != 'verified')
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
    if reviewed and pack > 1 and offer.get('pack_quantity_verified') is not True:
        raise ValueError('포장 안의 공식 비교 단위 수량을 실제로 확인해야 합니다')
    source_tax_basis = 'vat_included' if offer['vat_included'] else 'vat_excluded'
    benchmark_tax_basis = offer.get('benchmark_tax_basis',source_tax_basis)
    if benchmark_tax_basis not in ('vat_included','vat_excluded'):
        raise ValueError('비교 단가의 세금 기준은 vat_included 또는 vat_excluded여야 합니다')
    converting_tax = benchmark_tax_basis != source_tax_basis
    if converting_tax or 'vat_rate' in offer:
        rate_text = str(offer.get('vat_rate',''))
        if (not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',rate_text)
                or not Decimal(0) <= Decimal(rate_text) <= Decimal(1)):
            raise ValueError('세금 환산율은 0~1 사이의 소수 6자리 이내 값으로 명시해야 합니다')
        rate = Decimal(rate_text)
    with localcontext() as context:
        context.prec = max(80,len(price)+32)
        unit_price = Decimal(price)/pack
        if converting_tax:
            unit_price = (unit_price*(1+rate) if benchmark_tax_basis == 'vat_included'
                else unit_price/(1+rate))
        # Pack and VAT conversion precede the single conservative API rounding.
        unit_price = unit_price.quantize(Decimal('0.000001'),rounding=ROUND_CEILING)
    normalized = format(unit_price,'f').rstrip('0').rstrip('.')
    tax_note = ''
    if converting_tax:
        source_label = '부가세 포함' if offer['vat_included'] else '부가세 별도'
        target_label = '부가세 포함' if benchmark_tax_basis == 'vat_included' else '부가세 별도'
        percent = format((rate*100).normalize(),'f')
        tax_note = (f' 표시가는 {source_label}이며, 세율 {percent}%로 {target_label} 기준에 환산했다.'
            f' 포장 환산 기준 단가는 {normalized}원이다.')
    benchmark = str(offer.get('benchmark_unit_price_krw',normalized))
    if not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',benchmark) or Decimal(benchmark) < unit_price:
        raise ValueError('비교 단가는 포장·세금 기준으로 환산한 관측가 이상이어야 합니다')
    fact_benchmarks = offer.get('benchmark_unit_price_by_fact',{})
    scorable_ids = {fact.get('fact_id') for fact in item.get('facts',[]) if fact.get('scorable')}
    if (not isinstance(fact_benchmarks,dict)
            or any(key not in scorable_ids for key in fact_benchmarks)):
        raise ValueError('개별 비교 단가는 실제 scorable fact_id에만 지정해야 합니다')
    for value in fact_benchmarks.values():
        if (not re.fullmatch(r'[0-9]+(?:\.[0-9]{1,6})?',str(value))
                or Decimal(str(value)) < unit_price):
            raise ValueError('개별 비교 단가는 포장·세금 환산 관측가 이상인 소수 6자리 이내 원화여야 합니다')
    try:
        observed = datetime.fromisoformat(offer['observed_at'].replace('Z','+00:00'))
        kst = timezone(timedelta(hours=9))
        # API 관측일은 KST다. UTC의 자정 전 관측도 한국 날짜로 보존한다.
        observed_at = observed.replace(tzinfo=kst).date().isoformat() if observed.tzinfo is None else observed.astimezone(kst).date().isoformat()
    except (ValueError,KeyError,AttributeError):
        raise ValueError('가격 관측일이 필요합니다') from None
    lines, seen = [], set()
    for fact in item.get('facts',[]):
        if not fact.get('scorable') or fact['fact_id'] in seen:
            continue
        line_benchmark = str(fact_benchmarks.get(fact['fact_id'],benchmark))
        if Decimal(fact['comparable_amount_krw']) <= Decimal(line_benchmark)*Decimal(fact['quantity']):
            continue
        if fact.get('period_kind') not in (None,'none'):
            raise ValueError('기간형 물품은 별도 기간 검증이 필요합니다')
        if fact.get('tax_basis') != benchmark_tax_basis:
            raise ValueError('공식 fact와 비교 단가의 세금 기준이 다릅니다')
        if any(not str(fact.get(key,'')) for key in ('contract_no','request_no','line_no')):
            raise ValueError('계약번호·납품요구번호·라인 번호가 필요합니다')
        seen.add(fact['fact_id'])
        lines.append({'fact_id':fact['fact_id'], 'benchmark_unit_price_krw':line_benchmark,
            'comparison_basis_id':fact['basis_id'], 'unit':fact['unit'], 'tax_basis':fact['tax_basis'], 'period':None,
            'price_evidence':[{'kind':'price_page','source_url':offer['url'],'quote':offer['quote'],
                'observed_price_krw':price,'observed_at':observed_at,'vat_included':offer['vat_included'],
                'shipping_included':offer['shipping_included'],
                'note':f'표시가 {price}원/공식 비교 단위 {pack}{fact["unit"]} 구성. 공식 비교 단위 1{fact["unit"]}당 {line_benchmark}원으로 비교.' + tax_note}],
            'fulfillment_evidence':[{'kind':'text','text':f"계약 {fact['contract_no']}, 납품요구 {fact['request_no']}, 라인 {fact['line_no']}. 공식 fact {fact['fact_id']}, 수량 {fact['quantity']}, 비교금액 {fact['comparable_amount_krw']}원."}]})
    if not lines:
        raise ValueError('양의 절감액이 있는 공식 fact가 없습니다')
    body = {'dataset_release_id':event['dataset_release_id'],'ruleset_version':event['ruleset_version'],
        'canonical_product_id':item['item_id'], 'title':f'{model} 국내 실판매가 {price}원 비교'[:200],
        'claim':'실제 판매 상세의 동일 모델·구성과 일반 구매 가격을 확인했다.',
        'comparison_scope':offer.get('comparison_scope',f'동일 모델 신품, 한 포장의 공식 비교 단위 수량은 {pack}이며 fact의 단위·세금 기준으로 환산'),
        'reproduction_notes':'공식 fact별 floor(max(C-B×Q,0))를 합산. 각 라인 근거에 계약·납품요구·라인 번호를 기재. 가격 시점 차이는 사용자 지정 대회 조사 기준에서 제외한다.',
        'lines':lines}
    body['reproduction_notes'] += tax_note
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
    if 'purchase_availability' in offer:
        review = offer['purchase_availability']
        body['reproduction_notes'] += (f' 판매 경로 {offer["purchase_channel"]}: '
            f'{review["quote"].strip()} (출처 {review["url"]}, 관측 {review["observed_at"]}).')
    for field, limit in (('title',200),('claim',2000),('comparison_scope',1000),('reproduction_notes',4000)):
        if not isinstance(body[field],str) or not body[field].strip() or len(body[field]) > limit:
            raise ValueError(f'{field}는 비어 있지 않은 {limit}자 이하 문자열이어야 합니다. 근거를 자르지 말고 요약·분리하세요')
    if any(len(e['note']) > 500 for line in lines for e in line['price_evidence']):
        raise ValueError('가격 근거 note는 500자 이하로 요약해야 합니다')
    if len(json.dumps(body,ensure_ascii=False).encode()) > 1048576:
        raise ValueError('점수 본문 1MiB 초과; 명시적 fact 범위 분리가 필요합니다')
    return body


def build_submission(item, offer, event):
    """Legacy manual builder retains its existing verification requirements."""
    return _assemble_submission(item, offer, event, reviewed=True)


def build_draft(item, offer, event):
    """Assemble an UNREVIEWED body without manufacturing verification flags.

    Caller must retain observed field/source claims in the evidence package.
    ScoreClient independently requires a matching Codex review before sending.
    """
    return _assemble_submission(item, offer, event, reviewed=False)


def calculate_body(item, body):
    facts = {f['fact_id']: f for f in item['facts']}
    rows, seen = [], set()
    with localcontext() as context:
        context.prec = 100
        for line in body['lines']:
            fid = line['fact_id']
            if fid in seen or fid not in facts:
                raise ValueError('duplicate or unknown fact in body')
            seen.add(fid)
            fact = facts[fid]
            c, q, b = (Decimal(str(x)) for x in (fact['comparable_amount_krw'],fact['quantity'],line['benchmark_unit_price_krw']))
            if not all(x.is_finite() and x >= 0 for x in (c,q,b)) or q == 0:
                raise ValueError('invalid official C/Q or benchmark')
            amount = max(c-b*q,Decimal(0)).to_integral_value(rounding=ROUND_FLOOR)
            rows.append({'fact_id':fid,'C':str(c),'Q':str(q),'B':str(b),'savings_krw':str(amount),
                         'contract_no':fact['contract_no'],'request_no':fact['request_no'],'line_no':fact['line_no']})
    return {'formula':'sum(floor(max(C-B*Q,0)))','version':'1','rows':rows,
            'total_savings_krw':str(sum(int(row['savings_krw']) for row in rows)),
            'reviewed_amount_krw':None,'realized_savings_krw':None}
