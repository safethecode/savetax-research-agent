"""Revision requests preserve ownership, optimistic locking and recovery."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from savetax.client import SaveTaxClient, SaveTaxError
from savetax.submissions import ScoreClient
from publication_fixture import approved_publication


class ScoreRevisionTests(unittest.TestCase):
    def setUp(self):
        self.client = ScoreClient(SaveTaxClient(token='savetax_'+'x'*32))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.body, self.package, self.review = approved_publication(Path(self.temp.name))
        self.context = {'package_dir': self.package, 'review_path': self.review}
        self.preview = {'ok': True, 'next_action': 'revise_existing',
                        'claimed_by_me': True, 'existing_submission_id': 'S1',
                        'existing_submission_state': 'accepted', 'current_revision': 2}

    def test_revision_uses_same_owned_submission_and_if_match(self):
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'submission_id': 'S1', 'revision': 3}
        with patch('savetax.adapters.scoring.requests.post', return_value=response) as post:
            receipt = self.client.revise('S1', self.body, 'revision-key-123', self.preview, **self.context)
        self.assertEqual(receipt['revision'], 3)
        args, kwargs = post.call_args
        self.assertEqual(args[0], 'https://hackathon.savetax.now/v1/events/current/submissions/S1/revisions')
        self.assertEqual(kwargs['headers']['If-Match'], '2')
        self.assertEqual(kwargs['headers']['Idempotency-Key'], 'revision-key-123')
        self.assertFalse(kwargs['allow_redirects'])
        response.close.assert_called_once()

    def test_new_other_uneditable_or_mismatched_claim_cannot_be_revised(self):
        cases = ({'next_action': 'submit'}, {'claimed_by_me': False},
                 {'existing_submission_id': 'S2'}, {'existing_submission_state': 'disqualified'},
                 {'current_revision': True}, {'current_revision': 0})
        with patch('savetax.adapters.scoring.requests.post') as post:
            for change in cases:
                with self.subTest(change=change), self.assertRaises(ValueError):
                    self.client.revise('S1', self.body, 'revision-key-123', {**self.preview, **change}, **self.context)
            for sid in ('../S1', 'S1/revisions', 'https://example.com', 'savetax_'+'x'*32):
                with self.subTest(sid=sid), self.assertRaises(ValueError):
                    self.client.revise(sid, self.body, 'revision-key-123', self.preview, **self.context)
        post.assert_not_called()

    def test_revision_conflict_is_sanitized_without_changing_key(self):
        response = Mock(status_code=409, headers={})
        response.json.return_value = {'code': 'REVISION_CONFLICT', 'message': 'untrusted text'}
        with patch('savetax.adapters.scoring.requests.post', return_value=response):
            with self.assertRaises(SaveTaxError) as caught:
                self.client.revise('S1', self.body, 'revision-key-123', self.preview, **self.context)
        self.assertEqual(caught.exception.code, 'REVISION_CONFLICT')
        self.assertNotIn('untrusted text', str(caught.exception))
        response.close.assert_called_once()
