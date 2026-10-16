import unittest
from unittest.mock import Mock, patch

from savetax.client import SaveTaxClient
from savetax.submissions import ScoreClient, build_submission


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.item = {'item_id': '001', 'snapshot': {'name': '모델 ABC', 'model': 'ABC'},
            'availability': {'state': 'available'}, 'facts': [
                {'fact_id': 'dl:001:C1:R1:1', 'contract_no': 'C1', 'request_no': 'R1', 'line_no': '1',
                 'unit': '대', 'tax_basis': 'vat_included', 'basis_id': 'basis:대:vat_included',
                 'period_kind': 'none', 'scorable': True, 'quantity': '1000', 'comparable_amount_krw': '300000000'}]}
        self.offer = {'model': 'ABC', 'url': 'https://shop.example/item', 'quote': 'ABC 새상품 판매가 100000원 부가세 포함',
                      'unit_price': '100000', 'observed_at': '2026-10-16', 'vat_included': True,
                      'shipping_included': True, 'price_verified': True, 'model_verified': True}
        self.event = {'dataset_release_id': 'release', 'ruleset_version': 'rules'}

    def test_build_keeps_every_contract_request_and_line_reference(self):
        body = build_submission(self.item,self.offer,self.event)
        line = body['lines'][0]
        self.assertEqual(line['comparison_basis_id'],'basis:대:vat_included')
        text = line['fulfillment_evidence'][0]['text']
        for value in ('계약 C1','납품요구 R1','라인 1'):
            self.assertIn(value,text)
        self.assertEqual(line['benchmark_unit_price_krw'],'100000')

    def test_unverified_model_or_claimed_item_cannot_build_score(self):
        for item, offer in (({**self.item,'availability':{'state':'claimed'}},self.offer),
                            (self.item,{**self.offer,'model_verified':False}),
                            (self.item,{**self.offer,'model':'ABD'})):
            with self.assertRaises(ValueError):
                build_submission(item,offer,self.event)

    def test_submit_requires_successful_submit_preview(self):
        client = ScoreClient(SaveTaxClient(token='savetax_'+'x'*32))
        with patch('savetax.submissions.requests.post') as post:
            for preview in ({'ok':False},{'ok':True,'next_action':'pick_another_product'}):
                with self.assertRaises(ValueError):
                    client.submit(build_submission(self.item,self.offer,self.event),'research-key-123',preview)
        post.assert_not_called()

    def test_score_http_destination_and_idempotency_are_fixed(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=201,headers={})
        response.json.return_value = {'submission_id':'S1','amount_krw':'200000000'}
        with patch.object(raw,'get_json',return_value={'items':[{'state':'available'}]}), \
                patch('savetax.submissions.requests.post',return_value=response) as post:
            result = ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    'research-key-123',{'ok':True,'next_action':'submit'})
        self.assertEqual(result['submission_id'],'S1')
        self.assertTrue(post.call_args.args[0].endswith('/submissions'))
        self.assertEqual(post.call_args.kwargs['headers']['Idempotency-Key'],'research-key-123')
        self.assertFalse(post.call_args.kwargs['allow_redirects'])


if __name__ == '__main__':
    unittest.main()
