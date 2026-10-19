import unittest
from unittest.mock import Mock, patch

import requests

from savetax.client import SaveTaxClient, SaveTaxError
from savetax.counterevidence import CounterevidenceClient, validate_counterevidence


class CounterevidenceTests(unittest.TestCase):
    def setUp(self):
        self.token = 'savetax_' + 'x' * 32
        self.transport = SaveTaxClient(token=self.token)
        self.client = CounterevidenceClient(self.transport)
        self.body = {'revision_no': 2, 'body': '실제 판매 원문의 단품과 조달 완제품의 구성이 다릅니다.', 'evidence_refs': []}

    def test_payload_rejects_score_fields_invalid_revision_and_secrets(self):
        for update in ({'benchmark_unit_price_krw': '1'}, {'revision_no': True},
                       {'revision_no': 0}, {'body': ' '}, {'body': '가' * 4001},
                       {'body': self.token}, {'evidence_refs': [self.token]},
                       {'evidence_refs': ['asset'] * 9}):
            with self.subTest(update=update), self.assertRaises(ValueError):
                validate_counterevidence({**self.body, **update})

    def test_post_is_narrow_and_never_follows_redirects(self):
        response = Mock(status_code=201, headers={})
        response.json.return_value = {'counterevidence_id': 'counter-1', 'body': self.token}
        with patch('savetax.counterevidence.requests.post', return_value=response) as request:
            result = self.client.submit('submission-1', self.body, 'stable-key-001')
        self.assertEqual(request.call_args.args[0],
                         'https://hackathon.savetax.now/v1/events/current/submissions/submission-1/counterevidence')
        self.assertEqual(request.call_args.kwargs['headers']['Idempotency-Key'], 'stable-key-001')
        self.assertFalse(request.call_args.kwargs['allow_redirects'])
        self.assertEqual(result['body'], '[REDACTED]')
        response.close.assert_called_once()
        for sid, key in (('../withdraw', 'stable-key-001'), ('valid', '../elsewhere'), (self.token, 'stable-key-001')):
            with self.assertRaises(ValueError):
                self.client.submit(sid, self.body, key)

    def test_pending_recovery_is_not_a_success(self):
        response = Mock(status_code=202)
        with patch.object(self.transport, '_get', return_value=response):
            self.assertEqual(self.client.recover_request('stable-key-001'), {'state': 'pending'})
        response.close.assert_called_once()

    def test_recovery_requires_counterevidence_receipt(self):
        response = Mock(status_code=200)
        response.json.return_value = {'submission_id': 'wrong-receipt'}
        with patch.object(self.transport, '_get', return_value=response), self.assertRaises(SaveTaxError):
            self.client.recover_request('stable-key-001')
        response.json.return_value = {'counterevidence_id': 'counter-1'}
        with patch.object(self.transport, '_get', return_value=response):
            self.assertEqual(self.client.recover_request('stable-key-001')['state'], 'submitted')
        with patch.object(self.transport, '_get', side_effect=SaveTaxError('missing', status=404)):
            self.assertEqual(self.client.recover_request('stable-key-001'), {'state': 'not_found'})

    def test_http_failure_preserves_retry_after_without_server_text(self):
        response = Mock(status_code=429, headers={'Retry-After': '60'})
        response.json.return_value = {'code': 'RATE_LIMITED', 'message': self.token}
        with patch('savetax.counterevidence.requests.post', return_value=response), self.assertRaises(SaveTaxError) as caught:
            self.client.submit('submission-1', self.body, 'stable-key-001')
        self.assertEqual(caught.exception.retry_after, 60)
        self.assertNotIn(self.token, str(caught.exception))
        response.close.assert_called_once()

    def test_transport_failure_does_not_expose_request_or_claim_success(self):
        with patch('savetax.counterevidence.requests.post', side_effect=requests.Timeout(self.token)), self.assertRaises(SaveTaxError) as caught:
            self.client.submit('submission-1', self.body, 'stable-key-001')
        self.assertEqual(caught.exception.stage, 'transport')
        self.assertNotIn(self.token, str(caught.exception))


if __name__ == '__main__':
    unittest.main()
