import unittest
from unittest.mock import patch, Mock

from savetax.client import SaveTaxClient, SaveTaxError
from savetax.reports import ReportClient, validate_report


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.report = {'product_id': '001', 'product_name': '동일모델 가격 확인',
                       'reason': '같은 모델의 현재 판매 페이지를 직접 확인했으며 설치 조건은 추가 검토가 필요합니다.',
                       'source_url': 'https://prod.danawa.com/info/?pcode=1', 'details': '관측일 2026-10-16. 지급 완료를 의미하지 않습니다.'}

    def test_score_fields_or_uploads_cannot_be_sent_as_general_report(self):
        for extra in ({'lines': []}, {'evidence_refs': ['file-id']}, {'owner': 'someone'}):
            with self.subTest(extra=extra):
                with self.assertRaises(ValueError):
                    validate_report({**self.report, **extra})

    def test_claimed_item_can_be_reported_without_lookup_or_score_submission(self):
        response = Mock(status_code=201, headers={})
        response.json.return_value = {'report_id': 'R1', 'status': 'submitted'}
        client = ReportClient(SaveTaxClient(token='savetax_' + 'x'*32))
        with patch('savetax.reports.requests.post', return_value=response) as request:
            result = client.submit(self.report, 'stable-key-001')
        self.assertEqual(result['report_id'], 'R1')
        self.assertEqual(request.call_args.args[0], 'https://hackathon.savetax.now/v1/events/current/reports')
        self.assertFalse(request.call_args.kwargs['allow_redirects'])
        self.assertEqual(request.call_args.kwargs['headers']['Idempotency-Key'], 'stable-key-001')

    def test_error_never_leaks_response_or_token(self):
        response = Mock(status_code=403, headers={})
        token = 'savetax_' + 'x'*32
        response.json.return_value = {'message': token, 'code': 'SCOPE_DENIED'}
        with patch('savetax.reports.requests.post', return_value=response):
            with self.assertRaises(SaveTaxError) as caught:
                ReportClient(SaveTaxClient(token=token)).submit(self.report, 'stable-key-001')
        self.assertNotIn(token, str(caught.exception))

    def test_short_reason_and_unverified_source_rejected(self):
        for updates in ({'reason': '싸다'}, {'source_url': 'http://example.com'},
                        {'source_url': 'https://127.0.0.1/private'}):
            with self.assertRaises(ValueError):
                validate_report({**self.report, **updates})

    def test_submitted_report_correction_uses_current_revision(self):
        client = ReportClient(SaveTaxClient(token='savetax_'+'x'*32))
        current = {'report_id':'37c99372-472d-4921-901b-ba87603f9e63','revision':1,'review_status':'submitted'}
        response = Mock(status_code=200,headers={})
        response.json.return_value = {'revision':2}
        with patch('savetax.reports.requests.patch',return_value=response) as request:
            client.revise(current,self.report,'correction-key-001')
        self.assertEqual(request.call_args.kwargs['headers']['If-Match'],'1')
        with self.assertRaises(ValueError):
            client.revise({**current,'review_status':'rejected'},self.report,'correction-key-001')


if __name__ == '__main__':
    unittest.main()
