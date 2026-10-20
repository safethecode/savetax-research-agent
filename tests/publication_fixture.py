"""Hand-checked source, fact, and broker execution fixture for publication tests."""
from pathlib import Path

from savetax.application.review import create_package, review_package
from savetax.runtime.artifacts import canonical_hash


class PublicationReviewer:
    """Replace the external Codex process, retaining the real review broker."""
    def review(self, package_dir, manifest):
        decision = {
            'schema_version': '1', 'decision': 'approved', 'blocking': [],
            'accepted_limitations': [], 'notes': '원문 모델과 완제품 가격 및 계산을 대조했다.',
            'source_assessments': [{'source_id': 'S1', 'assessment': '판매 원문 직접 대조'}]}
        self.last_execution = {
            'kind': 'codex-exec', 'provider': 'openai', 'model': 'fixture-codex',
            'thread_id': 'fixture-review-thread', 'returncode': 0,
            'decision_sha256': canonical_hash(decision),
            'package_sha256': manifest['package_hash'], 'metadata_source': 'jsonl',
            'observed_at': '2026-10-20T00:00:00Z'}
        return decision


def approved_publication(root, *, allow_submit=True, allow_revise=True):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    quote = 'MODEL-A 새상품 완제품 1개 판매가 100원 부가세 포함 무료배송 구매 가능'
    source = root / 'seller.txt'
    source.write_text(quote, encoding='utf-8')
    fact = {
        'fact_id': 'F1', 'basis_id': 'B1', 'unit': '개', 'tax_basis': 'vat_included',
        'quantity': '2', 'comparable_amount_krw': '1000', 'scorable': True,
        'contract_no': 'C1', 'request_no': 'R1', 'line_no': '1'}
    item = {'item_id': '001', 'facts': [fact], 'facts_total': 1,
            'returned_count': 1, 'facts_truncated': False}
    event = {'dataset_release_id': 'D1', 'ruleset_version': 'V1'}
    policy = {'schema_version': '1', 'policy_id': 'publication-test',
              'allow_submit': allow_submit, 'allow_revise': allow_revise}
    claims = [
        {'field': field, 'value': value, 'status': 'observed', 'source_id': 'S1',
         'quote': quote, 'location': 'line 1'}
        for field, value in (
            ('model', 'MODEL-A'), ('unit_price', '100'), ('vat_included', True),
            ('shipping_included', True), ('pack_quantity', 1), ('unit', '개'),
            ('new', True), ('purchase_available', True), ('complete_product', True))]
    proposal = {'schema_version': '1', 'comparison_kind': 'identical',
                'claims': claims, 'unknowns': []}
    sources = [{'source_id': 'S1', 'path': str(source), 'url': 'https://seller.example/item',
                'kind': 'retailer', 'observed_at': '2026-10-20T00:00:00Z',
                'truncated': False, 'method': 'browser'}]
    calculation = {'formula': 'floor(max(C-B*Q,0))', 'rows': [
        {'fact_id': 'F1', 'C': '1000', 'Q': '2', 'B': '100', 'savings_krw': '800'}],
        'total_savings_krw': '800'}
    body = {
        'dataset_release_id': 'D1', 'ruleset_version': 'V1', 'canonical_product_id': '001',
        'title': 'MODEL-A 일반 판매가격 비교',
        'lines': [{'fact_id': 'F1', 'benchmark_unit_price_krw': '100',
                   'comparison_basis_id': 'B1', 'unit': '개',
                   'tax_basis': 'vat_included', 'period': None,
                   'price_evidence': [{'source_url': 'https://seller.example/item', 'quote': quote}],
                   'fulfillment_evidence': [{'text': '계약 C1, 납품요구 R1, 라인 1'}]}]}
    package = create_package(root / 'packages', item=item, event=event, policy=policy,
                             proposal=proposal, sources=sources,
                             calculation=calculation, body=body)
    review = review_package(package, PublicationReviewer())
    return body, package, review
