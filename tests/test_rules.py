import copy
import unittest

try:
    from savetax import rules
except ImportError:
    rules = None


def strategy(**updates):
    result = {
        "version": 1, "name": "domestic-first", "filters": [],
        "order_by": [{"field": "dlv_amount", "direction": "desc"}],
        "batch_size": 500,
    }
    result.update(updates)
    return result


class RulesTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rules, "the declarative rules API must exist")

    def test_numeric_filters_accept_csv_values_without_lexical_comparison(self):
        rows = [{"item_id": "001", "price": "100", "dlv_amount": "20"},
                {"item_id": "002", "price": "9", "dlv_amount": "100"}]
        result = rules.apply_rules(rows, strategy(filters=[
            {"field": "price", "op": "gt", "value": 10}]))
        self.assertEqual([row["item_id"] for row in result], ["001"])

    def test_text_filters_are_literal_and_case_sensitive(self):
        rows = [{"item_id": "A", "model": "ABC-123", "dlv_amount": 1},
                {"item_id": "B", "model": "abc-123", "dlv_amount": 2}]
        selected = rules.apply_rules(rows, strategy(filters=[
            {"field": "model", "op": "contains", "value": "ABC"}]))
        self.assertEqual([row["item_id"] for row in selected], ["A"])

    def test_all_supported_predicates_filter_real_records(self):
        cases = [("eq", 10, ["B"]), ("ne", 10, ["C", "A"]),
                 ("gt", 10, ["C"]), ("gte", 10, ["C", "B"]),
                 ("lt", 10, ["A"]), ("lte", 10, ["B", "A"]),
                 ("in", [5, 15], ["C", "A"])]
        rows = [{"item_id": "A", "price": 5, "dlv_amount": 1},
                {"item_id": "B", "price": 10, "dlv_amount": 2},
                {"item_id": "C", "price": 15, "dlv_amount": 3}]
        for op, value, expected in cases:
            with self.subTest(op=op):
                selected = rules.apply_rules(rows, strategy(filters=[
                    {"field": "price", "op": op, "value": value}]))
                self.assertEqual([row["item_id"] for row in selected], expected)

    def test_missing_numeric_values_do_not_become_zero_or_match_negative_filters(self):
        rows = [{"item_id": "A", "price": None}, {"item_id": "B", "price": ""},
                {"item_id": "C", "price": "NaN"}, {"item_id": "D", "price": True},
                {"item_id": "E", "price": 5}]
        selected = rules.apply_rules(rows, strategy(filters=[
            {"field": "price", "op": "ne", "value": 0}]))
        self.assertEqual([row["item_id"] for row in selected], ["E"])

    def test_multifield_sort_is_numeric_and_keeps_missing_last(self):
        rows = [{"item_id": "B", "dlv_amount": "9"},
                {"item_id": "C", "dlv_amount": None},
                {"item_id": "D", "dlv_amount": "100"},
                {"item_id": "A", "dlv_amount": "100"}]
        selected = rules.apply_rules(rows, strategy(order_by=[
            {"field": "dlv_amount", "direction": "desc"},
            {"field": "item_id", "direction": "asc"}]))
        self.assertEqual([row["item_id"] for row in selected], ["A", "D", "B", "C"])

    def test_unknown_schema_and_executable_expressions_are_rejected(self):
        bad_rules = [strategy(sql="DROP TABLE listings"), strategy(version=True),
                     strategy(batch_size=0), strategy(batch_size=True),
                     strategy(filters=[{"field": "__class__", "op": "eq", "value": "x"}]),
                     strategy(filters=[{"field": "price", "op": "eval", "value": "1"}]),
                     strategy(filters=[{"field": "price", "op": "gt", "value": "1"}]),
                     strategy(filters=[{"field": "price", "op": "gt", "value": True}]),
                     strategy(filters=[{"field": "price", "op": "gt", "value": float("nan")}]),
                     strategy(filters=[{"field": "price", "op": "contains", "value": "1"}]),
                     strategy(order_by=[{"field": "price; DROP TABLE x", "direction": "asc"}]),
                     strategy(order_by=[{"field": "price", "direction": "DESC NULLS FIRST"}])]
        for bad in bad_rules:
            with self.subTest(strategy=bad), self.assertRaises(ValueError):
                rules.apply_rules([], bad)

    def test_strategy_and_records_are_not_mutated(self):
        rows = [{"item_id": "A", "price": "10", "nested": {"x": 1}}]
        policy = strategy()
        before = copy.deepcopy((rows, policy))
        result = rules.apply_rules(rows, policy)
        result[0]["nested"]["x"] = 9
        self.assertEqual((rows, policy), before)

    def test_batches_are_reproducible_distinct_and_use_public_seed(self):
        rows = [{"item_id": value} for value in ["001", "002", "003", "004", "001", "", None]]
        actual = list(rules.deterministic_batches(rows, "public-handle", "2026-10", 2))
        self.assertEqual([[r["item_id"] for r in batch] for batch in actual],
                         [["001", "002"], ["003", "004"]])
        self.assertEqual(actual, list(rules.deterministic_batches(list(reversed(rows)),
                                                                "public-handle", "2026-10", 2)))

    def test_batch_parameters_reject_non_public_token_and_bad_size(self):
        for handle, version, size in [("", "v1", 2), ("public", "", 2),
                                      ("public", "v1", 0), ("public", "v1", True),
                                      ("Bearer secret", "v1", 2)]:
            with self.subTest(handle=handle, size=size), self.assertRaises(ValueError):
                list(rules.deterministic_batches([], handle, version, size))

    def test_feedback_counts_rejections_without_changing_strategy_or_facts(self):
        policy = strategy()
        feedback = [{"rejected": True, "review_code": "MODEL_MISMATCH", "fact": {"price": 99}},
                    {"status": "rejected", "review_code": "MODEL_MISMATCH"},
                    {"status": "accepted", "review_code": "MODEL_MISMATCH"},
                    {"status": "disqualified", "review_code": "VAT_UNKNOWN"}]
        before = copy.deepcopy((policy, feedback))
        result = rules.learn_from_feedback(policy, feedback)
        self.assertEqual(result["review_code_counts"], {"MODEL_MISMATCH": 2, "VAT_UNKNOWN": 1})
        self.assertEqual(result["strategy"], policy)
        self.assertTrue(result["requires_human_review"])
        self.assertEqual(len(result["suggestions"]), 2)
        self.assertEqual((policy, feedback), before)


if __name__ == "__main__":
    unittest.main()
