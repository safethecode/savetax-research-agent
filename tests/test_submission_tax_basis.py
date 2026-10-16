"""Submission evidence keeps the observed price while B uses an explicit tax basis."""
from copy import deepcopy
import unittest

from savetax.submissions import build_submission


class SubmissionTaxBasisTests(unittest.TestCase):
    def setUp(self):
        self.item = {'item_id': '001', 'snapshot': {'model': 'ABC'},
            'availability': {'state': 'available'}, 'facts': [
                {'fact_id': 'F1', 'contract_no': 'C1', 'request_no': 'R1', 'line_no': '1',
                 'unit': '대', 'tax_basis': 'vat_included', 'basis_id': 'basis:대:vat_included',
                 'period_kind': 'none', 'scorable': True, 'quantity': '1000',
                 'comparable_amount_krw': '300000000'}]}
        self.offer = {'model': 'ABC', 'url': 'https://shop.example/item',
            'quote': 'ABC 새상품 100000원, 부가세 별도', 'unit_price': '100000',
            'observed_at': '2026-10-16', 'vat_included': False, 'shipping_included': True,
            'price_verified': True, 'model_verified': True,
            'benchmark_tax_basis': 'vat_included', 'vat_rate': '0.10'}
        self.event = {'dataset_release_id': 'release', 'ruleset_version': 'rules'}

    def test_excluded_source_price_is_preserved_and_gross_benchmark_is_used(self):
        before = deepcopy((self.item, self.offer, self.event))
        body = build_submission(self.item, self.offer, self.event)
        line = body['lines'][0]
        evidence = line['price_evidence'][0]
        self.assertEqual(line['benchmark_unit_price_krw'], '110000')
        self.assertEqual(line['tax_basis'], 'vat_included')
        self.assertEqual(line['comparison_basis_id'], 'basis:대:vat_included')
        self.assertEqual(evidence['observed_price_krw'], '100000')
        self.assertIs(evidence['vat_included'], False)
        self.assertEqual(evidence['quote'], self.offer['quote'])
        self.assertIn('10%', evidence['note'])
        self.assertIn('부가세 별도', evidence['note'])
        self.assertIn('110000', body['reproduction_notes'])
        for ref in ('계약 C1', '납품요구 R1', '라인 1'):
            self.assertIn(ref, line['fulfillment_evidence'][0]['text'])
        self.assertEqual((self.item, self.offer, self.event), before)

    def test_included_source_can_be_compared_with_excluded_fact(self):
        item = deepcopy(self.item)
        item['facts'][0].update(tax_basis='vat_excluded', basis_id='basis:대:vat_excluded')
        offer = {**self.offer, 'unit_price': '110000', 'vat_included': True,
            'quote': 'ABC 새상품 110000원, 부가세 포함', 'benchmark_tax_basis': 'vat_excluded'}
        line = build_submission(item, offer, self.event)['lines'][0]
        self.assertEqual(line['benchmark_unit_price_krw'], '100000')
        self.assertEqual(line['price_evidence'][0]['observed_price_krw'], '110000')
        self.assertIs(line['price_evidence'][0]['vat_included'], True)
        self.assertEqual(line['tax_basis'], 'vat_excluded')

    def test_pack_and_tax_conversion_round_once_after_both_operations(self):
        offer = {**self.offer, 'pack_quantity': 11, 'pack_quantity_verified': True}
        line = build_submission(self.item, offer, self.event)['lines'][0]
        # 100000 / 11 * 1.1 = 10000 exactly. Rounding before VAT gives 10000.000001.
        self.assertEqual(line['benchmark_unit_price_krw'], '10000')
        self.assertEqual(line['price_evidence'][0]['observed_price_krw'], '100000')
        offer.update(unit_price='11210', pack_quantity=3)
        self.assertEqual(build_submission(self.item, offer, self.event)['lines'][0]
            ['benchmark_unit_price_krw'], '4110.333334')

    def test_common_and_per_fact_benchmarks_cannot_omit_source_vat(self):
        for extra in ({'benchmark_unit_price_krw': '109999.999999'},
                      {'benchmark_unit_price_by_fact': {'F1': '109999.999999'}}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                build_submission(self.item, {**self.offer, **extra}, self.event)
        offer = {**self.offer, 'benchmark_unit_price_by_fact': {'F1': '114000'}}
        self.assertEqual(build_submission(self.item, offer, self.event)['lines'][0]
            ['benchmark_unit_price_krw'], '114000')

    def test_conversion_requires_explicit_valid_rate_and_target(self):
        missing = dict(self.offer)
        missing.pop('vat_rate')
        with self.assertRaises(ValueError):
            build_submission(self.item, missing, self.event)
        for rate in (None, True, '-0.1', 'NaN', 'Infinity', '1.01', '0.1000001', '10%'):
            with self.subTest(rate=rate), self.assertRaises(ValueError):
                build_submission(self.item, {**self.offer, 'vat_rate': rate}, self.event)
        for target in (None, True, 'unknown', 'VAT included'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                build_submission(self.item, {**self.offer, 'benchmark_tax_basis': target}, self.event)

    def test_unknown_source_and_wrong_fact_basis_are_still_rejected(self):
        for extra in ({'vat_included': None}, {'benchmark_tax_basis': 'vat_excluded'}):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                build_submission(self.item, {**self.offer, **extra}, self.event)

    def test_legacy_same_basis_needs_no_conversion_fields(self):
        offer = {k: v for k, v in self.offer.items()
            if k not in ('benchmark_tax_basis', 'vat_rate')}
        offer['vat_included'] = True
        self.assertEqual(build_submission(self.item, offer, self.event)['lines'][0]
            ['benchmark_unit_price_krw'], '100000')
        offer['vat_included'] = False
        with self.assertRaises(ValueError):
            build_submission(self.item, offer, self.event)


if __name__ == '__main__':
    unittest.main()
