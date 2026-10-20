import copy
import json
import tempfile
import unittest
from pathlib import Path

from savetax.application.review import create_package, review_package, require_approved


def inputs(root):
    source = root / 'retailer.txt'
    source.write_text('MODEL-A 새상품 100원 부가세 포함 무료배송', encoding='utf-8')
    fact = {'fact_id': 'F1', 'basis_id': 'B1', 'unit': '개', 'tax_basis': 'vat_included',
            'quantity': '2', 'comparable_amount_krw': '1000', 'scorable': True,
            'contract_no': 'C1', 'request_no': 'R1', 'line_no': '1'}
    item = {'item_id': '001', 'facts': [fact], 'facts_total': 1,
            'returned_count': 1, 'facts_truncated': False}
    event = {'dataset_release_id': 'D1', 'ruleset_version': 'V1'}
    policy = {'schema_version': '1', 'policy_id': 'P1', 'allow_submit': True,
              'allow_revise': False}
    claims = [{'field': field, 'value': value, 'status': 'observed', 'source_id': 'S1',
               'quote': 'MODEL-A 새상품 100원 부가세 포함 무료배송', 'location': 'line 1'}
              for field, value in [('model', 'MODEL-A'), ('unit_price', '100'),
                                   ('vat_included', True), ('shipping_included', True),
                                   ('pack_quantity', 1), ('unit', '개'), ('new', True),
                                   ('purchase_available', True), ('complete_product', True)]]
    proposal = {'schema_version': '1', 'claims': claims, 'unknowns': [],
                'comparison_kind': 'identical'}
    sources = [{'source_id': 'S1', 'path': str(source), 'url': 'https://seller.example/item',
                'kind': 'retailer', 'observed_at': '2026-10-20T00:00:00Z',
                'truncated': False, 'method': 'browser'}]
    calculation = {'formula': 'floor(max(C-B*Q,0))', 'rows': [
        {'fact_id': 'F1', 'C': '1000', 'Q': '2', 'B': '100', 'savings_krw': '800'}],
        'total_savings_krw': '800'}
    body = {'dataset_release_id': 'D1', 'ruleset_version': 'V1',
            'canonical_product_id': '001', 'title': 'MODEL-A 가격 비교',
            'lines': [{'fact_id': 'F1', 'benchmark_unit_price_krw': '100',
                       'comparison_basis_id': 'B1', 'unit': '개',
                       'tax_basis': 'vat_included', 'period': None,
                       'price_evidence': [{'source_url': 'https://seller.example/item',
                                           'quote': claims[0]['quote']}]}]}
    return dict(item=item, event=event, policy=policy, proposal=proposal,
                sources=sources, calculation=calculation, body=body)


class FixtureReviewer:
    def __init__(self, decision='approved', blockers=None):
        self.decision = decision
        self.blockers = blockers or []

    def review(self, package_dir, manifest):
        result = {'schema_version': '1', 'decision': self.decision,
                  'blocking': self.blockers, 'accepted_limitations': [],
                  'notes': '원문과 계산 검토', 'source_assessments': [
                      {'source_id': 'S1', 'assessment': '직접 읽은 판매 근거'}]}
        from savetax.runtime.artifacts import canonical_hash
        self.last_execution = {'kind': 'codex-exec', 'provider': 'openai',
                               'model': 'test-review-model', 'thread_id': 'thread-test',
                               'returncode': 0, 'decision_sha256': canonical_hash(result),
                               'package_sha256': manifest['package_hash'],
                               'metadata_source': 'jsonl', 'observed_at': '2026-10-20T00:00:00Z'}
        return result


class EvidenceReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = inputs(self.root)

    def package(self, **changes):
        return create_package(self.root / 'packages', **{**self.data, **changes})

    def test_copies_actual_source_bytes_and_retains_official_scope(self):
        package = self.package()
        manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
        copied = package / manifest['sources'][0]['path']
        self.assertEqual(copied.read_bytes(), Path(self.data['sources'][0]['path']).read_bytes())
        self.assertEqual(manifest['official_scope']['adopted_fact_ids'], ['F1'])
        self.assertEqual(manifest['item']['facts'], self.data['item']['facts'])
        self.assertNotIn(str(self.root), json.dumps(manifest))

    def test_broker_approval_binds_exact_body_and_policy(self):
        package = self.package()
        review = review_package(package, FixtureReviewer())
        accepted = require_approved(self.data['body'], package, review)
        self.assertEqual(accepted['decision'], 'approved')
        with self.assertRaises(ValueError):
            require_approved({**self.data['body'], 'title': 'changed'}, package, review)
        with self.assertRaises(ValueError):
            require_approved(self.data['body'], package, review, operation='revise')

    def test_source_or_manifest_tamper_invalidates_approval(self):
        for target in ('source', 'policy'):
            with self.subTest(target=target):
                package = self.package()
                review = review_package(package, FixtureReviewer())
                manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
                if target == 'source':
                    (package / manifest['sources'][0]['path']).write_text('changed')
                else:
                    manifest['policy']['allow_submit'] = False
                    (package / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                with self.assertRaises(ValueError):
                    require_approved(self.data['body'], package, review)
                # Each iteration starts with a new destination to preserve immutability.
                self.data['policy']['policy_id'] += 'x'

    def test_fake_approved_dictionary_and_forged_metadata_are_rejected(self):
        package = self.package()
        fake = self.root / 'fake-review.json'
        fake.write_text(json.dumps({'decision': 'approved', 'reviewer': 'Codex'}))
        with self.assertRaises(ValueError):
            require_approved(self.data['body'], package, fake)

        class Forged:
            def review(self, package, manifest):
                return {'schema_version': '1', 'decision': 'approved', 'blocking': [],
                        'accepted_limitations': [], 'notes': 'ok', 'source_assessments': [],
                        'reviewer': {'provider': 'openai', 'model': 'fake'}}
        with self.assertRaises(ValueError):
            review_package(package, Forged())

    def test_approved_with_blockers_or_unknown_inputs_is_rejected(self):
        package = self.package()
        with self.assertRaises(ValueError):
            review_package(package, FixtureReviewer(blockers=['배송비 미확인']))
        proposal = copy.deepcopy(self.data['proposal'])
        proposal['claims'][3]['value'] = None
        proposal['claims'][3]['status'] = 'unknown'
        with self.assertRaises(ValueError):
            self.package(proposal=proposal)
        partial = self.package(proposal=proposal, body=None)
        review_package(partial, FixtureReviewer(decision='needs_evidence', blockers=['배송비']))
        with self.assertRaises(ValueError):
            review_package(partial, FixtureReviewer())

    def test_broken_source_quote_and_fact_references_are_rejected(self):
        proposal = copy.deepcopy(self.data['proposal'])
        proposal['claims'][0]['source_id'] = 'missing'
        with self.assertRaises(ValueError):
            self.package(proposal=proposal)
        proposal['claims'][0]['source_id'] = 'S1'
        proposal['claims'][0]['quote'] = 'fabricated text'
        with self.assertRaises(ValueError):
            self.package(proposal=proposal)
        body = copy.deepcopy(self.data['body'])
        body['lines'][0]['fact_id'] = 'not-returned'
        with self.assertRaises(ValueError):
            self.package(body=body)

    def test_truncated_facts_require_explicit_limited_scope(self):
        item = {**self.data['item'], 'facts_total': 3, 'facts_truncated': True}
        with self.assertRaises(ValueError):
            self.package(item=item)
        policy = {**self.data['policy'], 'fact_scope': {
            'kind': 'limited', 'fact_ids': ['F1'], 'reason': '이번 묶음은 반환된 납품만 비교'}}
        package = self.package(item=item, policy=policy)
        manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['official_scope']['facts_total'], 3)
        self.assertEqual(manifest['official_scope']['kind'], 'limited')

    def test_review_receipt_tamper_or_escape_is_rejected(self):
        package = self.package()
        review = review_package(package, FixtureReviewer())
        record = json.loads(review.read_text(encoding='utf-8'))
        record['execution_receipt'] = '../outside.json'
        review.write_text(json.dumps(record), encoding='utf-8')
        with self.assertRaises(ValueError):
            require_approved(self.data['body'], package, review)

    def test_calculation_cannot_disagree_with_official_fact_or_body(self):
        calculation = copy.deepcopy(self.data['calculation'])
        calculation['rows'][0]['C'] = '2000'
        with self.assertRaises(ValueError):
            self.package(calculation=calculation)

    def test_unknown_shipping_and_required_installation_cannot_be_accepted_as_limitations(self):
        for field, value in [('shipping_included', False), ('installation_required', True)]:
            with self.subTest(field=field):
                proposal = copy.deepcopy(self.data['proposal'])
                if field == 'shipping_included':
                    proposal['claims'][3]['value'] = value
                else:
                    proposal['claims'].append({**proposal['claims'][0], 'field': field, 'value': value})
                with self.assertRaises(ValueError):
                    self.package(proposal=proposal)
                self.package(proposal=proposal, body=None)

    def test_copies_raw_capture_and_detects_raw_byte_changes(self):
        raw = self.root / 'capture.json'
        raw.write_text('{"text":"MODEL-A 새상품 100원 부가세 포함 무료배송"}', encoding='utf-8')
        sources = [{**self.data['sources'][0], 'raw_path': str(raw)}]
        package = self.package(sources=sources)
        manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
        copied = package / manifest['sources'][0]['raw_path']
        self.assertEqual(copied.read_bytes(), raw.read_bytes())
        review = review_package(package, FixtureReviewer())
        copied.write_text('changed')
        with self.assertRaises(ValueError):
            require_approved(self.data['body'], package, review)

    def test_unsubstantiated_model_claim_is_preserved_only_without_body(self):
        proposal = copy.deepcopy(self.data['proposal'])
        proposal['claims'][0]['quote'] = 'model invented text'
        package = self.package(proposal=proposal, body=None)
        review_package(package, FixtureReviewer(decision='needs_evidence', blockers=['원문 불일치']))
        with self.assertRaises(ValueError):
            review_package(package, FixtureReviewer())

    def test_capture_metadata_is_retained(self):
        sources = [{**self.data['sources'][0], 'requested_url': 'https://seller.example/redirect',
                    'final_url': 'https://seller.example/item', 'capture_limit': 40000}]
        package = self.package(sources=sources)
        manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['sources'][0]['requested_url'], 'https://seller.example/redirect')
        self.assertEqual(manifest['sources'][0]['capture_limit'], 40000)

    def test_package_root_symbolic_link_is_not_resolved_before_validation(self):
        package = self.package()
        linked = self.root / 'linked-package'
        try:
            linked.symlink_to(package, target_is_directory=True)
        except OSError:
            self.skipTest('OS account cannot create directory symbolic links')
        with self.assertRaises(ValueError):
            review_package(linked, FixtureReviewer())

    def test_review_updates_only_the_matching_job_and_preserves_attempts(self):
        package = self.package()
        job = self.root / 'job.json'
        state = {'state': 'awaiting_review', 'package_dir': str(package.resolve()),
                 'attempts': 3, 'history': [{'kind': 'source_read'}]}
        job.write_text(json.dumps(state), encoding='utf-8')
        review = review_package(package, FixtureReviewer())
        updated = json.loads(job.read_text(encoding='utf-8'))
        self.assertEqual(updated['state'], 'approved')
        self.assertEqual(Path(updated['review_path']), review)
        self.assertEqual(updated['attempts'], 3)
        self.assertEqual(updated['history'], state['history'])
        updated['package_dir'] = str(self.root / 'different-package')
        job.write_text(json.dumps(updated), encoding='utf-8')
        before = job.read_bytes()
        review_package(package, FixtureReviewer(decision='rejected'))
        self.assertEqual(job.read_bytes(), before)
