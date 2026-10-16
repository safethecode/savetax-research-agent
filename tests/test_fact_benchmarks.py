"""Whole-panel orders must retain each fact's independently rounded cost."""
from copy import deepcopy
import unittest

from savetax.submissions import build_submission


class FactBenchmarkTests(unittest.TestCase):
    def setUp(self):
        fact={'fact_id':'F1','contract_no':'C','request_no':'R1','line_no':'1',
            'scorable':True,'quantity':'3','comparable_amount_krw':'180000',
            'unit':'㎡','tax_basis':'vat_included','basis_id':'basis:㎡:vat_included','period_kind':'none'}
        self.item={'item_id':'001','snapshot':{'model':'PANEL'},'availability':{'state':'available'},
            'facts':[fact,{**fact,'fact_id':'F2','request_no':'R2','quantity':'2','comparable_amount_krw':'120000'}]}
        self.offer={'model':'PANEL','url':'https://shop.example/panel','quote':'PANEL 2㎡ 한 장 59840원',
            'unit_price':'59840','pack_quantity':2,'pack_quantity_verified':True,
            'observed_at':'2026-10-16','vat_included':True,'shipping_included':False,
            'price_verified':True,'model_verified':True,
            'benchmark_unit_price_by_fact':{'F1':'39893.333334'}}
        self.event={'dataset_release_id':'release','ruleset_version':'rules'}

    def test_odd_area_order_uses_whole_panels_and_next_fact_keeps_default(self):
        body=build_submission(self.item,self.offer,self.event)
        lines={x['fact_id']:x for x in body['lines']}
        self.assertEqual(lines['F1']['benchmark_unit_price_krw'],'39893.333334')
        self.assertEqual(lines['F2']['benchmark_unit_price_krw'],'29920')
        self.assertEqual(lines['F1']['price_evidence'][0]['observed_price_krw'],'59840')
        self.assertIn('2㎡',lines['F1']['price_evidence'][0]['note'])
        self.assertIn('39893.333334',lines['F1']['price_evidence'][0]['note'])
        self.assertIn('29920',lines['F2']['price_evidence'][0]['note'])

    def test_overrides_must_name_actual_scorable_facts(self):
        for overrides in (None,[],{'UNKNOWN':'40000'},{'F1':'40000','TYPO':'40000'}):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    build_submission(self.item,{**self.offer,'benchmark_unit_price_by_fact':overrides},self.event)
        item=deepcopy(self.item);item['facts'][0]['scorable']=False
        with self.assertRaises(ValueError):
            build_submission(item,self.offer,self.event)

    def test_overrides_cannot_lower_observed_unit_cost_or_use_invalid_numbers(self):
        for value in ('0','29919','29920.0000001','NaN','Infinity',True,'-40000'):
            with self.subTest(value=value):
                offer={**self.offer,'benchmark_unit_price_by_fact':{'F1':value}}
                with self.assertRaises(ValueError):
                    build_submission(self.item,offer,self.event)

    def test_fact_with_no_positive_difference_is_skipped_using_its_own_cost(self):
        self.offer['benchmark_unit_price_by_fact']={'F1':'60000'}
        body=build_submission(self.item,self.offer,self.event)
        self.assertEqual([x['fact_id'] for x in body['lines']],['F2'])
        self.assertEqual(body['lines'][0]['benchmark_unit_price_krw'],'29920')


if __name__=='__main__':
    unittest.main()
