"""검증된 신규 물품을 예상 차액순으로 정렬하고 남은 한도 안에서 제출한다."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation


def prioritize(candidates, *, remaining=None, release_deferred=True, priority_min='100000000'):
    if remaining is not None and (type(remaining) is not int or remaining < 0):
        raise ValueError('remaining은 0 이상 정수 또는 무제한 null이어야 합니다')
    minimum = Decimal(priority_min)
    if not minimum.is_finite() or minimum <= 0:
        raise ValueError('우선 제출 금액은 양수여야 합니다')
    output = {'submit_now':[], 'deferred':[], 'needs_evidence':[], 'excluded_duplicates':[],
              'priority_min_krw':format(minimum,'f'), 'remaining':remaining}
    eligible = []
    seen = set()
    for original in candidates:
        row = deepcopy(original)
        item_id = row.get('item_id')
        if not item_id or item_id in seen:
            raise ValueError('대기열은 item_id별 한 건이어야 합니다')
        seen.add(item_id)
        if row.get('state') != 'available':
            output['excluded_duplicates'].append(row)
            continue
        try:
            amount = Decimal(str(row.get('potential_savings_krw')))
        except InvalidOperation:
            amount = None
        if (row.get('verified') is not True or row.get('eligible_for_preview') is not True
                or amount is None or not amount.is_finite() or amount <= 0):
            output['needs_evidence'].append(row)
            continue
        if amount < minimum and not release_deferred:
            output['deferred'].append(row)
        else:
            eligible.append(row)
    key = lambda r: (-Decimal(r['potential_savings_krw']),r['item_id'])
    eligible.sort(key=key)
    output['deferred'].sort(key=key)
    limit = len(eligible) if remaining is None else remaining
    output['submit_now'] = eligible[:limit]
    output['deferred'].extend(eligible[limit:])
    return output
