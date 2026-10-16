import json
import unittest
from unittest.mock import Mock, patch

import requests

from savetax.client import SaveTaxClient, SaveTaxError
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
        self.assessment = {
            'core_purpose':{'status':'verified','basis':'두 제품 모두 40W 조명용이다.'},
            'complete_product':{'status':'verified','basis':'두 가격 모두 완성 등기구 1개에 해당한다.'}}

    def test_build_keeps_every_contract_request_and_line_reference(self):
        body = build_submission(self.item,self.offer,self.event)
        line = body['lines'][0]
        self.assertEqual(line['comparison_basis_id'],'basis:대:vat_included')
        text = line['fulfillment_evidence'][0]['text']
        for value in ('계약 C1','납품요구 R1','라인 1'):
            self.assertIn(value,text)
        self.assertEqual(line['benchmark_unit_price_krw'],'100000')

    def test_pack_keeps_displayed_price_and_normalizes_benchmark(self):
        offer = {**self.offer,'unit_price':'18000','pack_quantity':5,'pack_quantity_verified':True,
                 'quote':'ABC 5개입 판매가 18000원 부가세 포함'}
        body = build_submission(self.item,offer,self.event)
        line = body['lines'][0]
        self.assertEqual(line['benchmark_unit_price_krw'],'3600')
        self.assertEqual(line['price_evidence'][0]['observed_price_krw'],'18000')
        self.assertIn('5',body['comparison_scope'])

    def test_unverified_pack_and_benchmark_below_normalized_price_are_rejected(self):
        for extra in ({'pack_quantity':5},{'pack_quantity':True},
                      {'pack_quantity':5,'pack_quantity_verified':True,'benchmark_unit_price_krw':'1'}):
            with self.assertRaises(ValueError):
                build_submission(self.item,{**self.offer,**extra},self.event)

    def test_fractional_pack_unit_rounds_up_instead_of_overstating_savings(self):
        body = build_submission(self.item,{**self.offer,'unit_price':'11210',
            'pack_quantity':3,'pack_quantity_verified':True},self.event)
        self.assertEqual(body['lines'][0]['benchmark_unit_price_krw'],'3736.666667')

    def test_unverified_model_or_claimed_item_cannot_build_score(self):
        for item, offer in (({**self.item,'availability':{'state':'claimed'}},self.offer),
                            (self.item,{**self.offer,'model_verified':False}),
                            (self.item,{**self.offer,'model':'ABD'})):
            with self.assertRaises(ValueError):
                build_submission(item,offer,self.event)

    def test_equivalent_comparison_preserves_real_retail_model_and_differences(self):
        offer = {**self.offer,'comparison_kind':'equivalent','model':'XYZ',
            'comparison_assessment':self.assessment,
            'model_verified':False,'retail_model_verified':True,'comparison_reviewed':True,
            'procurement_model':'ABC','spec_mapping':[{'attribute':'출력','original':'40W','alternative':'40W'}],
            'spec_source_urls':['https://maker.example/abc','https://maker.example/xyz'],
            'differences':'제조사·모델이 다르며 방수등급 IP67 대 IP66이다.'}
        body = build_submission(self.item,offer,self.event)
        self.assertIn('XYZ',body['title'])
        self.assertIn('대체',body['claim'])
        self.assertIn('IP67 대 IP66',body['comparison_scope'])
        self.assertIn('https://maker.example/abc',body['reproduction_notes'])
        self.assertNotIn('동일 모델·구성',body['claim'])
        for key in ('comparison_reviewed','procurement_model','spec_mapping','spec_source_urls','differences'):
            with self.subTest(key=key):
                invalid = {**offer};invalid.pop(key)
                with self.assertRaises(ValueError):
                    build_submission(self.item,invalid,self.event)
        for extra in ({'procurement_model':'OTHER'},{'comparison_kind':'unknown'},
                      {'spec_mapping':[{}]},{'spec_source_urls':['http://maker.example/abc']}):
            with self.subTest(extra=extra):
                with self.assertRaises(ValueError):
                    build_submission(self.item,{**offer,**extra},self.event)

    def test_submit_requires_successful_submit_preview(self):
        client = ScoreClient(SaveTaxClient(token='savetax_'+'x'*32))
        with patch('savetax.submissions.requests.post') as post:
            for preview in ({'ok':False},{'ok':True,'next_action':'pick_another_product'}):
                with self.assertRaises(ValueError):
                    client.submit(build_submission(self.item,self.offer,self.event),'research-key-123',preview)
        post.assert_not_called()

    def test_long_equivalent_differences_stay_in_claim_without_overflowing_scope(self):
        differences = '차이점은 모두 별도로 기록했다. ' * 35
        offer = {**self.offer,'comparison_kind':'equivalent','model':'XYZ',
            'comparison_assessment':self.assessment,
            'retail_model_verified':True,'comparison_reviewed':True,'procurement_model':'ABC',
            'spec_mapping':[{'attribute':'전력','original':'40W','alternative':'40W'}],
            'spec_source_urls':['https://maker.example/abc'],'differences':differences,
            'comparison_scope':'제품 본체의 가격 비교다. ' * 35}
        body = build_submission(self.item,offer,self.event)
        self.assertLessEqual(len(body['comparison_scope']),1000)
        self.assertIn(differences,body['claim'])
        self.assertIn('XYZ',body['comparison_scope'])
        for extra in ({'comparison_scope':'가'*1001},{'differences':'나'*2001}):
            with self.subTest(extra=next(iter(extra))):
                with self.assertRaises(ValueError):
                    build_submission(self.item,{**offer,**extra},self.event)

    def test_score_http_destination_and_idempotency_are_fixed(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=201,headers={})
        response.json.return_value = {'submission_id':'S1','amount_krw':'200000000'}
        with patch.object(raw,'get_json',return_value={'items':[{'item_id':'001','state':'available'}]}), \
                patch('savetax.submissions.requests.post',return_value=response) as post:
            result = ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    'research-key-123',{'ok':True,'next_action':'submit'})
        self.assertEqual(result['submission_id'],'S1')
        self.assertTrue(post.call_args.args[0].endswith('/submissions'))
        self.assertEqual(post.call_args.kwargs['headers']['Idempotency-Key'],'research-key-123')
        self.assertFalse(post.call_args.kwargs['allow_redirects'])

    def test_korean_evidence_wire_body_stays_within_validated_byte_limit(self):
        item = {**self.item, 'facts': [{**self.item['facts'][0],
            'fact_id': f'dl:001:C1:R{i}:1', 'request_no': f'R{i}'} for i in range(500)]}
        offer = {**self.offer, 'quote': '한글 판매 근거 ' * 40}
        body = build_submission(item, offer, self.event)
        self.assertLess(len(json.dumps(body, ensure_ascii=False).encode('utf-8')), 1048576)
        self.assertGreater(len(requests.Request('POST', 'https://example.invalid', json=body).prepare().body), 1048576)
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'ok': True}
        with patch('savetax.submissions.requests.post', return_value=response) as post:
            ScoreClient(SaveTaxClient(token='savetax_'+'x'*32)).preview(body)
        prepared = requests.Request('POST', *post.call_args.args, **{
            k: v for k, v in post.call_args.kwargs.items() if k in ('headers', 'json', 'data')}).prepare()
        self.assertLessEqual(len(prepared.body), 1048576)
        self.assertEqual(json.loads(prepared.body), body)
        self.assertEqual(prepared.headers['Content-Type'], 'application/json')

    def test_success_http_with_unreadable_json_remains_an_unconfirmed_result(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=201, headers={})
        response.json.side_effect = ValueError('untrusted response contents')
        with patch.object(raw, 'get_json', return_value={'items':[{'item_id':'001','state':'available'}]}), \
                patch('savetax.submissions.requests.post', return_value=response):
            with self.assertRaises(SaveTaxError) as error:
                ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    'research-key-123', {'ok':True,'next_action':'submit'})
        self.assertEqual(error.exception.stage, 'decode')
        self.assertNotIn('untrusted', str(error.exception))
        response.close.assert_called_once()

    def test_success_without_submission_id_is_not_a_receipt(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        for payload in ({}, [], {'submission_id':None}, {'submission_id':''}, {'submission_id':True}):
            with self.subTest(payload=payload):
                response = Mock(status_code=201, headers={})
                response.json.return_value = payload
                with patch.object(raw,'get_json',return_value={'items':[{'item_id':'001','state':'available'}]}), \
                        patch('savetax.submissions.requests.post',return_value=response):
                    with self.assertRaises(SaveTaxError):
                        ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                            'research-key-123', {'ok':True,'next_action':'submit'})

    def test_lookup_must_match_requested_product_instead_of_first_available_row(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        rows = [{'item_id':'other','state':'available'}, {'item_id':'001','state':'claimed'}]
        response = Mock(status_code=201,headers={})
        response.json.return_value = {'submission_id':'S1'}
        with patch.object(raw,'get_json',return_value={'items':rows}), \
                patch('savetax.submissions.requests.post',return_value=response) as post:
            with self.assertRaises(ValueError):
                ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    'research-key-123', {'ok':True,'next_action':'submit'})
        post.assert_not_called()

    def test_no_lookup_match_never_sends_submission(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=201,headers={})
        response.json.return_value = {'submission_id':'S1'}
        with patch.object(raw,'get_json',return_value={'items':[{'item_id':'other','state':'available'}]}), \
                patch('savetax.submissions.requests.post',return_value=response) as post:
            with self.assertRaises(ValueError):
                ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    'research-key-123', {'ok':True,'next_action':'submit'})
        post.assert_not_called()

    def test_submission_requires_key_before_any_network_call(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=201,headers={})
        response.json.return_value = {'submission_id':'S1'}
        with patch.object(raw,'get_json',return_value={'items':[{'item_id':'001','state':'available'}]}) as lookup, \
                patch('savetax.submissions.requests.post',return_value=response) as post:
            with self.assertRaises(ValueError):
                ScoreClient(raw).submit(build_submission(self.item,self.offer,self.event),
                    None, {'ok':True,'next_action':'submit'})
        lookup.assert_not_called()
        post.assert_not_called()

    def test_recovery_distinguishes_pending_from_committed_receipt(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        for status, payload, expected in (
                (202, {'state':'pending'}, {'state':'pending'}),
                (200, {'submission_id':'S1'}, {'state':'submitted','response':{'submission_id':'S1'}})):
            with self.subTest(status=status):
                response = Mock(status_code=status, headers={})
                response.json.return_value = payload
                with patch('savetax.client.requests.get',return_value=response), \
                        patch('savetax.submissions.requests.post') as post:
                    self.assertEqual(ScoreClient(raw).recover_request('research-key-123'),expected)
                response.close.assert_called_once()
                post.assert_not_called()

    def test_recovery_404_is_not_found_but_invalid_200_remains_unresolved(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=404, headers={})
        response.json.return_value = {'code':'NOT_FOUND'}
        with patch('savetax.client.requests.get',return_value=response):
            self.assertEqual(ScoreClient(raw).recover_request('research-key-123'),{'state':'not_found'})
        response = Mock(status_code=200, headers={})
        response.json.return_value = {'state':'pending'}
        with patch('savetax.client.requests.get',return_value=response):
            with self.assertRaises(SaveTaxError) as error:
                ScoreClient(raw).recover_request('research-key-123')
        self.assertEqual(error.exception.stage,'decode')

    def test_nested_api_error_preserves_safe_status_and_code(self):
        raw = SaveTaxClient(token='savetax_'+'x'*32)
        response = Mock(status_code=422,headers={})
        response.json.return_value = {'error':{'code':'PRICE_GAP_TOO_SMALL','message':raw._token}}
        with patch('savetax.submissions.requests.post',return_value=response):
            with self.assertRaises(SaveTaxError) as error:
                ScoreClient(raw).preview({})
        self.assertEqual(error.exception.status,422)
        self.assertEqual(error.exception.code,'PRICE_GAP_TOO_SMALL')
        self.assertNotIn(raw._token,str(error.exception))


if __name__ == '__main__':
    unittest.main()
