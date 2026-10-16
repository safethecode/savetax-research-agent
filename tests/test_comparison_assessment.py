"""Reject incomplete or purpose-mismatched alternatives before a score body exists."""
from copy import deepcopy
import unittest

from savetax.submissions import build_submission


class ComparisonAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.item = {'item_id':'001','snapshot':{'model':'ORIGINAL'},
            'availability':{'state':'available'},'facts':[
                {'fact_id':'dl:001:C:R:1','contract_no':'C','request_no':'R','line_no':'1',
                 'scorable':True,'quantity':'10','comparable_amount_krw':'1000000',
                 'period_kind':'none','tax_basis':'vat_included','basis_id':'basis:개:vat_included','unit':'개'}]}
        self.event = {'dataset_release_id':'release','ruleset_version':'rules'}
        self.offer = {'comparison_kind':'equivalent','procurement_model':'ORIGINAL','model':'RETAIL',
            'price_verified':True,'retail_model_verified':True,'comparison_reviewed':True,
            'url':'https://shop.example/retail','quote':'RETAIL 완성 등기구 판매가 30000원',
            'unit_price':'30000','observed_at':'2026-10-16','vat_included':True,'shipping_included':True,
            'spec_mapping':[{'attribute':'용도','original':'40W 실내 조명','alternative':'40W 실내 조명'}],
            'spec_source_urls':['https://maker.example/original','https://shop.example/retail'],
            'differences':'방수등급은 IP67과 IP66으로 다르다.',
            'comparison_assessment':{
                'core_purpose':{'status':'verified','basis':'두 제품 모두 40W 실내 조명용으로 판매된다.'},
                'complete_product':{'status':'verified','basis':'판매 구성은 컨버터와 본체를 포함한 완성 등기구 1개다.'}}}

    def test_missing_assessment_cannot_be_replaced_by_general_review_flag(self):
        self.offer.pop('comparison_assessment')
        with self.assertRaises(ValueError):
            build_submission(self.item,self.offer,self.event)

    def test_general_surveillance_does_not_pass_an_unverified_disaster_purpose(self):
        self.offer['comparison_assessment']['core_purpose'] = {
            'status':'unverified','basis':'침입 감시는 확인했지만 수위·침수·화재 탐지는 입증하지 못했다.'}
        with self.assertRaises(ValueError):
            build_submission(self.item,self.offer,self.event)

    def test_surface_sheet_does_not_pass_a_missing_complete_wall_assembly(self):
        self.offer['comparison_assessment']['complete_product'] = {
            'status':'missing','basis':'표면판 가격만 있으며 프레임·레일·체결 부재가 빠졌다.'}
        with self.assertRaises(ValueError):
            build_submission(self.item,self.offer,self.event)

    def test_review_basis_is_required_for_both_critical_checks(self):
        for key in ('core_purpose','complete_product'):
            for invalid in (None,True,{'status':'verified','basis':''},
                            {'status':'verified','basis':' '*3},{'status':True,'basis':'확인'}):
                with self.subTest(key=key,invalid=invalid):
                    offer=deepcopy(self.offer);offer['comparison_assessment'][key]=invalid
                    with self.assertRaises(ValueError):
                        build_submission(self.item,offer,self.event)

    def test_complete_same_purpose_alternative_keeps_disclosed_spec_differences(self):
        body=build_submission(self.item,self.offer,self.event)
        self.assertEqual(body['lines'][0]['benchmark_unit_price_krw'],'30000')
        self.assertIn('IP67과 IP66',body['claim'])
        self.assertIn('40W 실내 조명용',body['reproduction_notes'])
        self.assertIn('컨버터와 본체를 포함한 완성 등기구',body['reproduction_notes'])


if __name__=='__main__':
    unittest.main()
