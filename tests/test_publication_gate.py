"""Every final score write requires a current review before HTTP can run."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from savetax.client import SaveTaxClient
from savetax.submissions import ScoreClient
from publication_fixture import approved_publication


class MissingPublicationReviewTests(unittest.TestCase):
    def setUp(self):
        self.raw = SaveTaxClient(token='savetax_' + 'x' * 32)
        self.scoring = ScoreClient(self.raw)
        self.body = {'canonical_product_id': '001', 'lines': []}
        self.preview = {'ok': True, 'next_action': 'submit'}
        self.revision_preview = {
            'ok': True, 'next_action': 'revise_existing', 'claimed_by_me': True,
            'existing_submission_id': 'S1', 'existing_submission_state': 'accepted',
            'current_revision': 2}

    def test_direct_submit_requires_review_before_any_http(self):
        response = Mock(status_code=201, headers={})
        response.json.return_value = {'submission_id': 'S1'}
        with patch.object(self.raw, 'get_json', return_value={
                'items': [{'item_id': '001', 'state': 'available'}]}) as lookup, \
                patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            with self.assertRaisesRegex(ValueError, 'package|review|검토'):
                self.scoring.submit(self.body, 'publication-key-123', self.preview)
        lookup.assert_not_called()
        post.assert_not_called()

    def test_direct_revision_requires_review_before_any_http(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'submission_id': 'S1', 'revision': 3}
        with patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            with self.assertRaisesRegex(ValueError, 'package|review|검토'):
                self.scoring.revise('S1', self.body, 'publication-key-123', self.revision_preview)
        post.assert_not_called()

    def test_private_post_cannot_bypass_review_on_final_write(self):
        response = Mock(status_code=201, headers={})
        response.json.return_value = {'submission_id': 'S1'}
        with patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            with self.assertRaisesRegex(ValueError, 'package|review|검토'):
                self.scoring._post('/submissions', self.body, 'publication-key-123')
        post.assert_not_called()

    def test_private_revision_post_cannot_bypass_review(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'submission_id': 'S1', 'revision': 3}
        with patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            with self.assertRaisesRegex(ValueError, 'package|review|검토'):
                self.scoring._post('/submissions/S1/revisions', self.body,
                                   'publication-key-123', revision=2)
        post.assert_not_called()


class ApprovedPublicationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.body, self.package, self.review = approved_publication(self.root)
        self.context = {'package_dir': self.package, 'review_path': self.review}
        self.raw = SaveTaxClient(token='savetax_' + 'x' * 32)
        self.scoring = ScoreClient(self.raw)
        self.preview = {'ok': True, 'next_action': 'submit'}

    def test_broker_review_allows_exact_body_to_reach_fixed_post(self):
        response = Mock(status_code=201, headers={})
        response.json.return_value = {'submission_id': 'S1'}
        with patch.object(self.raw, 'get_json', return_value={
                'items': [{'item_id': '001', 'state': 'available'}]}), \
                patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            result = self.scoring.submit(self.body, 'publication-key-123', self.preview, **self.context)
        self.assertEqual(result, {'submission_id': 'S1'})
        self.assertEqual(json.loads(post.call_args.kwargs['data']), self.body)
        self.assertEqual(post.call_args.kwargs['headers']['Idempotency-Key'], 'publication-key-123')

    def test_exact_body_tampering_blocks_before_lookup_and_post(self):
        changed = copy.deepcopy(self.body)
        changed['lines'][0]['benchmark_unit_price_krw'] = '1'
        with patch.object(self.raw, 'get_json') as lookup, \
                patch('savetax.adapters.scoring.requests.post') as post:
            with self.assertRaises(ValueError):
                self.scoring.submit(changed, 'publication-key-123', self.preview, **self.context)
        lookup.assert_not_called()
        post.assert_not_called()

    def test_source_tampering_blocks_before_lookup_and_post(self):
        manifest = json.loads((self.package / 'manifest.json').read_text(encoding='utf-8'))
        (self.package / manifest['sources'][0]['path']).write_text('판매가를 바꾼 원문', encoding='utf-8')
        with patch.object(self.raw, 'get_json') as lookup, \
                patch('savetax.adapters.scoring.requests.post') as post:
            with self.assertRaises(ValueError):
                self.scoring.submit(self.body, 'publication-key-123', self.preview, **self.context)
        lookup.assert_not_called()
        post.assert_not_called()

    def test_body_changed_during_availability_lookup_cannot_reuse_review(self):
        def mutate_after_initial_gate(*args, **kwargs):
            self.body['title'] = '최초 승인 뒤 달라진 제목'
            return {'items': [{'item_id': '001', 'state': 'available'}]}
        with patch.object(self.raw, 'get_json', side_effect=mutate_after_initial_gate), \
                patch('savetax.adapters.scoring.requests.post') as post:
            with self.assertRaises(ValueError):
                self.scoring.submit(self.body, 'publication-key-123', self.preview, **self.context)
        post.assert_not_called()

    def test_submit_only_policy_does_not_authorize_revision(self):
        body, package, review = approved_publication(self.root / 'submit-only', allow_revise=False)
        preview = {'ok': True, 'next_action': 'revise_existing', 'claimed_by_me': True,
                   'existing_submission_id': 'S1', 'existing_submission_state': 'accepted',
                   'current_revision': 2}
        with patch('savetax.adapters.scoring.requests.post') as post:
            with self.assertRaises(ValueError):
                self.scoring.revise('S1', body, 'publication-key-123', preview,
                                    package_dir=package, review_path=review)
        post.assert_not_called()

    def test_either_missing_context_path_blocks_before_any_http(self):
        for context in ({'package_dir': self.package}, {'review_path': self.review}):
            with self.subTest(context=context), patch.object(self.raw, 'get_json') as lookup, \
                    patch('savetax.adapters.scoring.requests.post') as post:
                with self.assertRaises(ValueError):
                    self.scoring.submit(self.body, 'publication-key-123', self.preview, **context)
                lookup.assert_not_called()
                post.assert_not_called()
