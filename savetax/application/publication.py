"""Review-gated score publication, preserving receipt-first recovery."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from ..runtime.artifacts import atomic_json


def require_publication_approval(body, package_dir=None, review_path=None, *, operation='submit'):
    """A fresh write always needs the broker's approval of these exact inputs."""
    if not package_dir or not review_path:
        raise ValueError('새 점수 전송에는 package와 review 검토 파일이 필요합니다')
    from .review import require_approved
    return require_approved(body, package_dir, review_path, operation=operation)


def _read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def run_score(args):
    """Reconcile a saved request before requiring approval for any new send."""
    # Preserve the compatibility imports used by callers of the original client.
    from ..client import SaveTaxClient
    from ..submissions import ScoreClient

    body = _read_json(args.input)
    key = 'score-' + hashlib.sha256(
        json.dumps(body, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    saved = _read_json(args.receipt) if Path(args.receipt).exists() else None
    if saved and (saved.get('idempotency_key') != key or saved.get('body') != body):
        raise ValueError('다른 점수 제출의 영수증입니다. 새 경로를 사용하세요')
    if saved and saved.get('state') == 'submitted':
        try:
            ScoreClient._require_receipt(saved.get('response'))
        except RuntimeError:
            saved['state'] = 'sending'
            atomic_json(args.receipt, saved)
        else:
            print('이미 점수 접수한 영수증을 보존합니다: ' + str(args.receipt))
            return 0

    receipt = saved or {'idempotency_key': key, 'body': body, 'state': 'prepared'}
    scoring = None
    if receipt['state'] == 'sending':
        scoring = ScoreClient(SaveTaxClient(guide_path=args.guide))
        recovery = scoring.recover_request(key)
        if recovery['state'] == 'submitted':
            receipt['response'] = recovery['response']
            receipt['state'] = 'submitted'
            atomic_json(args.receipt, receipt)
            return 0
        if recovery['state'] == 'pending':
            print('점수 접수가 아직 확정되지 않았습니다. 같은 영수증을 유지합니다')
            return 0
        if recovery['state'] != 'not_found':
            raise ValueError('접수 조회 상태를 확인할 수 없습니다')

    minimum = Decimal(args.min_saving)
    if not minimum.is_finite() or minimum < 0:
        raise ValueError('min-saving은 0 이상의 원화 금액이어야 합니다')
    if args.send:
        require_publication_approval(body, args.package, args.review)
    if scoring is None:
        scoring = ScoreClient(SaveTaxClient(guide_path=args.guide))
    preview = scoring.preview(body)
    receipt.update(preview=preview, state='previewed')
    atomic_json(args.receipt, receipt)
    if preview.get('ok') is not True or preview.get('next_action') != 'submit':
        raise ValueError('점수 preview가 신규 제출을 허용하지 않았습니다')
    amount_raw = preview.get('total_amount_krw')
    # JSON integers and decimal strings avoid float rounding in the send decision.
    if type(amount_raw) not in (str, int):
        raise ValueError('점수 preview 금액은 정수 또는 십진 문자열이어야 합니다')
    amount = Decimal(amount_raw)
    if not amount.is_finite() or amount < 0:
        raise ValueError('점수 preview 금액은 유한한 0 이상의 원화여야 합니다')
    if amount < minimum:
        receipt['state'] = 'deferred_lower_amount'
        atomic_json(args.receipt, receipt)
        print(f'후순위 대기: 예상 {amount:,.0f}원, 우선 기준 {minimum:,.0f}원')
        return 0
    print(f'점수 preview 예상액 {amount:,.0f}원')
    if args.send:
        # Check again before persisting the ambiguous-send marker; the transport
        # repeats the same gate immediately before its final POST.
        require_publication_approval(body, args.package, args.review)
        receipt['state'] = 'sending'
        atomic_json(args.receipt, receipt)
        receipt['response'] = scoring.submit(
            body, key, preview, package_dir=args.package, review_path=args.review)
        receipt['state'] = 'submitted'
        atomic_json(args.receipt, receipt)
        print('점수 제출 결과: ' + json.dumps(receipt['response'], ensure_ascii=False))
    return 0
