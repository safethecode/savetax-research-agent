"""A catalog stock flag must not override an inspected delivery channel."""
import copy
import unittest

from savetax.evidence import evaluate_candidate
from savetax.submissions import build_submission


def availability(**changes):
    record = {'channel':'parcel_delivery','status':'available',
              'source_kind':'retail_page','url':'https://shop.example/item',
              'quote':'일반 택배배송 가능, 3만원 이상 무료배송',
              'observed_at':'2026-10-16'}
    record.update(changes)
    return record


class PurchaseAvailabilityTests(unittest.TestCase):
    def setUp(self):
        self.item = {'item_id':'001','availability':{'state':'available'},
                     'snapshot':{'model':'ABC'},'facts':[
            {'fact_id':'dl:001:C:R:1','contract_no':'C','request_no':'R','line_no':'1',
             'unit':'개','tax_basis':'vat_included','basis_id':'basis:개:vat_included',
             'period_kind':'none','scorable':True,'quantity':'1000','comparable_amount_krw':'150000'}]}
        self.offer = {'model':'ABC','url':'https://shop.example/item','quote':'ABC 100원 신품',
                      'unit_price':'100','observed_at':'2026-10-16','vat_included':True,
                      'shipping_included':True,'price_verified':True,'model_verified':True,
                      'purchase_channel':'parcel_delivery','purchase_availability':availability()}
        self.event = {'dataset_release_id':'release','ruleset_version':'rules'}

    def test_inspected_parcel_sold_out_blocks_body_despite_catalog_stock(self):
        offer = {**self.offer,'stock_confirmed':True,'soldOut':False,
                 'purchase_availability':availability(status='unavailable',quote='택배배송 일시품절')}
        with self.assertRaises(ValueError):
            build_submission(self.item,offer,self.event)

    def test_pickup_availability_does_not_prove_parcel_delivery(self):
        offer = {**self.offer,'purchase_availability':availability(channel='store_pickup')}
        with self.assertRaises(ValueError):
            build_submission(self.item,offer,self.event)

    def test_unchecked_catalog_or_malformed_review_cannot_generate_score(self):
        for change in [None,{},availability(status='unverified'),availability(source_kind='mcp'),
                       availability(url='https://127.0.0.1/item'),
                       availability(url='https://other.example/different-product'),availability(quote=' '),
                       availability(observed_at='2099-01-01')]:
            with self.subTest(review=change), self.assertRaises(ValueError):
                build_submission(self.item,{**self.offer,'purchase_availability':change},self.event)

    def test_declared_channel_requires_its_review(self):
        for key in ['purchase_channel','purchase_availability']:
            candidate=copy.deepcopy(self.offer);candidate.pop(key)
            with self.subTest(missing=key),self.assertRaises(ValueError):
                build_submission(self.item,candidate,self.event)

    def test_available_channel_review_is_retained_without_mutating_input(self):
        before=copy.deepcopy(self.offer)
        body=build_submission(self.item,self.offer,self.event)
        self.assertIn('parcel_delivery',body['reproduction_notes'])
        self.assertIn('일반 택배배송 가능',body['reproduction_notes'])
        self.assertEqual(body['lines'][0]['benchmark_unit_price_krw'],'100')
        self.assertEqual(before,self.offer)

    def test_evaluator_excludes_sold_out_offer_and_selects_available_retailer(self):
        fact={'item_id':'001','model':'ABC','unit':'개','quantity':'1000',
              'comparable_amount_krw':'150000','vat_included':True,
              'installation_required':False,'scorable':True}
        base={**self.offer,'unit':'개','currency':'KRW','domestic':True,'pack_quantity':1,
              'stock_confirmed':True,'unconditional':True,'shipping_total':'0',
              'installation_total':'0','installation_included':False}
        sold_out={**base,'unit_price':'50','purchase_availability':availability(status='unavailable')}
        available={**base,'unit_price':'100'}
        result=evaluate_candidate(fact,[sold_out,available])
        self.assertEqual(result['comparison_unit_price'],'100')
        self.assertEqual(result['potential_savings_krw'],'50000')
        self.assertTrue(result['eligible_for_preview'])


if __name__=='__main__':
    unittest.main()
