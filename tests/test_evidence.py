import copy
import json
import unittest

try:
    from savetax import evidence
except ImportError:
    evidence = None


def fact(**updates):
    result = {"item_id": "001", "model": "ABC-123", "unit": "대",
              "delivered_unit_price": "120000", "quantity": "10",
              "vat_included": True, "installation_required": False, "scorable": True}
    result.update(updates)
    return result


def offer(**updates):
    result = {"url": "https://shop.example/product/123", "observed_at": "2025-10-01",
              "quote": "ABC-123 판매가 100000원 부가세 포함, 재고 있음",
              "model": "ABC-123", "unit": "대", "unit_price": "100000", "currency": "KRW",
              "vat_included": True, "shipping_total": "0", "installation_total": "0",
              "installation_included": False, "pack_quantity": 1, "stock_confirmed": True,
              "unconditional": True, "domestic": True, "price_verified": True}
    result.update(updates)
    return result


class EvidenceTests(unittest.TestCase):
    def test_overseas_all_in_price_cannot_omit_known_shipping_and_installation(self):
        current_fact = fact(quantity='1', delivered_unit_price='120000', installation_required=True)
        current_offer = offer(domestic=False, unit_price='80000', shipping_total='10000',
                     installation_total='20000', installation_included=False,
                     landed_cost_krw='90000', taxes_verified=True)
        result = evidence.evaluate_candidate(current_fact,[current_offer])
        self.assertEqual(result['status'],'needs_review')
        self.assertIsNone(result['potential_savings_krw'])

    def test_current_event_price_gap_override_and_off(self):
        current_fact = fact(quantity='1', delivered_unit_price='110000')
        current_offer = offer(unit_price='100000', shipping_total='0', installation_total='0')
        self.assertFalse(evidence.evaluate_candidate(current_fact,[current_offer])['eligible_for_preview'])
        self.assertTrue(evidence.evaluate_candidate(current_fact,[current_offer],price_gap={'rule':'off'})['eligible_for_preview'])
        self.assertTrue(evidence.evaluate_candidate(current_fact,[current_offer],price_gap={
            'rule':'enforce','min_ratio':'1.1','min_unit_krw':'1000000'})['eligible_for_preview'])
    def setUp(self):
        self.assertIsNotNone(evidence, "the candidate evidence API must exist")

    def test_verified_offer_uses_decimal_savings_and_json_safe_amounts(self):
        result = evidence.evaluate_candidate(fact(), [offer()])
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["comparison_unit_price"], "100000")
        self.assertEqual(result["potential_savings_krw"], "200000")
        self.assertTrue(result["eligible_for_preview"])
        self.assertEqual(result["observed_potential_savings_krw"], "200000")
        self.assertIsNone(result["reviewed_amount_krw"])
        self.assertIsNone(result["realized_savings_krw"])
        self.assertTrue(result["caveats"])
        json.dumps(result, allow_nan=False)

    def test_official_comparable_amount_overrides_displayed_unit_price_and_floors(self):
        result = evidence.evaluate_candidate(fact(delivered_unit_price="999999",
                                                  comparable_amount_krw="1200000.9"), [offer()])
        self.assertEqual(result["potential_savings_krw"], "200000")
        self.assertTrue(result["eligible_for_preview"])

    def test_total_shipping_and_installation_are_allocated_over_fact_quantity(self):
        result = evidence.evaluate_candidate(fact(delivered_unit_price="150000", installation_required=True),
                                             [offer(shipping_total="10000", installation_total="20000")])
        self.assertEqual(result["comparison_unit_price"], "103000")
        self.assertEqual(result["potential_savings_krw"], "470000")

    def test_domestic_verified_offer_has_priority_over_lower_overseas_offer(self):
        overseas = offer(domestic=False, unit_price="1000", landed_cost_krw="2000", taxes_verified=True)
        result = evidence.evaluate_candidate(fact(), [overseas, offer()])
        self.assertEqual(result["comparison_unit_price"], "100000")
        self.assertTrue(result["selected_offer"]["domestic"])

    def test_overseas_requires_verified_landed_cost_and_taxes(self):
        result = evidence.evaluate_candidate(fact(), [offer(domestic=False)])
        self.assertEqual(result["status"], "needs_review")
        self.assertFalse(result["eligible_for_preview"])
        valid = evidence.evaluate_candidate(fact(), [offer(domestic=False, unit_price="80000", landed_cost_krw="90000", taxes_verified=True)])
        self.assertEqual(valid["comparison_unit_price"], "90000")

    def test_threshold_ratio_and_absolute_gap_include_boundaries(self):
        cases = [("120000", "100000", True), ("119999", "100000", False),
                 ("11000000", "10000000", True), ("10999999", "10000000", False)]
        for delivered, market, eligible in cases:
            with self.subTest(delivered=delivered):
                result = evidence.evaluate_candidate(fact(delivered_unit_price=delivered), [offer(unit_price=market)])
                self.assertEqual(result["eligible_for_preview"], eligible)
                self.assertEqual(result["status"], "verified")

    def test_higher_market_price_produces_zero_instead_of_negative_savings(self):
        result = evidence.evaluate_candidate(fact(delivered_unit_price="50000"), [offer()])
        self.assertEqual(result["status"], "no_saving")
        self.assertEqual(result["potential_savings_krw"], "0")
        self.assertFalse(result["eligible_for_preview"])

    def test_incompatible_or_unverified_offers_never_pass(self):
        cases = [{"model": "ABC-124"}, {"unit": "박스"}, {"vat_included": False},
                 {"stock_confirmed": False}, {"unconditional": False}, {"currency": "USD"},
                 {"pack_quantity": 2}, {"price_verified": False}, {"url": "http://shop.example/x"},
                 {"quote": ""}, {"observed_at": "2999-01-01"},
                 {"observed_at": "2025-10-01T10:00:00"}, {"unit_price": "NaN"},
                 {"unit_price": True}, {"shipping_total": None}, {"domestic": None},
                 {"installation_total": None}]
        for updates in cases:
            with self.subTest(updates=updates):
                result = evidence.evaluate_candidate(fact(), [offer(**updates)])
                self.assertEqual(result["status"], "needs_review")
                self.assertFalse(result["eligible_for_preview"])
                self.assertTrue(result["reasons"])

    def test_bad_https_source_addresses_are_rejected_without_fetching(self):
        for url in ["https://localhost/x", "https://127.0.0.1/x", "https://10.1.2.3/x",
                    "https://user:secret@shop.example/x", "https://shop.example:444/x"]:
            with self.subTest(url=url):
                result = evidence.evaluate_candidate(fact(), [offer(url=url)])
                self.assertEqual(result["status"], "needs_review")

    def test_numeric_host_aliases_cannot_disguise_private_source_addresses(self):
        for url in ["https://127.1/x", "https://0177.0.0.1/x"]:
            with self.subTest(url=url):
                result = evidence.evaluate_candidate(fact(), [offer(url=url)])
                self.assertEqual(result["status"], "needs_review")

    def test_repeating_allocated_cost_rounds_up_to_submission_precision(self):
        result = evidence.evaluate_candidate(fact(quantity="3"), [offer(shipping_total="1")])
        self.assertEqual(result["comparison_unit_price"], "100000.333334")
        self.assertEqual(result["potential_savings_krw"], "59998")

    def test_valid_aware_observation_timestamp_is_accepted(self):
        result = evidence.evaluate_candidate(fact(), [offer(observed_at="2025-10-01T12:34:56+09:00")])
        self.assertEqual(result["status"], "verified")

    def test_missing_fact_values_are_not_inferred_from_offers(self):
        for updates in [{"model": None}, {"unit": None}, {"quantity": "0"},
                        {"quantity": "-1"}, {"vat_included": None},
                        {"installation_required": None}, {"scorable": None}]:
            with self.subTest(updates=updates):
                result = evidence.evaluate_candidate(fact(**updates), [offer()])
                self.assertEqual(result["status"], "needs_review")
                self.assertFalse(result["eligible_for_preview"])

    def test_unscorable_fact_retains_observed_saving_but_cannot_preview(self):
        result = evidence.evaluate_candidate(fact(scorable=False), [offer()])
        self.assertFalse(result["eligible_for_preview"])
        self.assertEqual(result["potential_savings_krw"], "200000")

    def test_unknown_installation_terms_are_not_treated_as_included(self):
        candidate = offer(installation_total="0", installation_included=False)
        result = evidence.evaluate_candidate(fact(installation_required=True), [candidate])
        self.assertEqual(result["status"], "needs_review")
        candidate["installation_included"] = True
        result = evidence.evaluate_candidate(fact(installation_required=True), [candidate])
        self.assertEqual(result["status"], "verified")

    def test_decimal_fractional_quantity_does_not_introduce_float_error(self):
        result = evidence.evaluate_candidate(fact(delivered_unit_price="1.2", quantity="0.3"),
                                             [offer(unit_price="1")])
        self.assertEqual(result["potential_savings_krw"], "0")
        self.assertFalse(result["eligible_for_preview"])

    def test_evaluation_does_not_mutate_facts_or_offers(self):
        source_fact, source_offers = fact(), [offer()]
        before = copy.deepcopy((source_fact, source_offers))
        result = evidence.evaluate_candidate(source_fact, source_offers)
        result["selected_offer"]["unit_price"] = "1"
        self.assertEqual((source_fact, source_offers), before)


if __name__ == "__main__":
    unittest.main()
