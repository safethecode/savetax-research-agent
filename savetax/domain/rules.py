"""Small, declarative candidate rules. No expressions or executable queries."""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import math
import re


TEXT_FIELDS = frozenset({"item_id", "product_name", "model", "manufacturer"})
NUMERIC_FIELDS = frozenset({"price", "dlv_amount", "dlv_qty", "dlv_count"})
ALLOWED_FIELDS = TEXT_FIELDS | NUMERIC_FIELDS
OPERATORS = frozenset({"eq", "ne", "gt", "gte", "lt", "lte", "contains", "not_contains", "in"})
_NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?\Z")


def _keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError(f"{label} must contain exactly {', '.join(sorted(expected))}")


def _strategy_value(value, field):
    if field in NUMERIC_FIELDS:
        if type(value) not in (int, float) or (isinstance(value, float) and not math.isfinite(value)):
            raise ValueError(f"{field} requires a finite JSON number (not bool or string)")
    elif not isinstance(value, str):
        raise ValueError(f"{field} requires a string")


def validate_strategy(strategy):
    """Validate the complete version-1 schema and return an independent copy."""
    _keys(strategy, {"version", "name", "filters", "order_by", "batch_size"}, "strategy")
    if type(strategy["version"]) is not int or strategy["version"] != 1:
        raise ValueError("strategy.version must be 1")
    if not isinstance(strategy["name"], str) or not strategy["name"].strip():
        raise ValueError("strategy.name must be a nonempty string")
    if type(strategy["batch_size"]) is not int or strategy["batch_size"] < 1:
        raise ValueError("strategy.batch_size must be a positive integer")
    if not isinstance(strategy["filters"], list) or not isinstance(strategy["order_by"], list):
        raise ValueError("strategy.filters and strategy.order_by must be lists")
    for rule in strategy["filters"]:
        _keys(rule, {"field", "op", "value"}, "filter")
        field, op, value = rule["field"], rule["op"], rule["value"]
        if not isinstance(field, str) or field not in ALLOWED_FIELDS:
            raise ValueError("unknown filter field")
        if not isinstance(op, str) or op not in OPERATORS:
            raise ValueError("unknown filter operator")
        if op in {"contains", "not_contains"} and field not in TEXT_FIELDS:
            raise ValueError("contains operators require a text field")
        if op in {"gt", "gte", "lt", "lte"} and field not in NUMERIC_FIELDS:
            raise ValueError("ordered comparisons require a numeric field")
        if op == "in":
            if not isinstance(value, list):
                raise ValueError("in requires a list")
            for member in value:
                _strategy_value(member, field)
        else:
            _strategy_value(value, field)
    for order in strategy["order_by"]:
        _keys(order, {"field", "direction"}, "order_by entry")
        if not isinstance(order["field"], str) or order["field"] not in ALLOWED_FIELDS:
            raise ValueError("unknown sort field")
        if order["direction"] not in ("asc", "desc"):
            raise ValueError("sort direction must be asc or desc")
    return deepcopy(strategy)


def _record_value(record, field):
    value = record.get(field)
    if field in TEXT_FIELDS:
        return value if isinstance(value, str) and value else None
    if isinstance(value, bool) or value is None:
        return None
    if not isinstance(value, (str, int, float, Decimal)):
        return None
    text = str(value)
    if not _NUMBER.fullmatch(text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _matches(record, rule):
    field, op = rule["field"], rule["op"]
    value = _record_value(record, field)
    if value is None:
        return False
    expected = rule["value"]
    if field in NUMERIC_FIELDS:
        expected = ([Decimal(str(member)) for member in expected] if op == "in"
                    else Decimal(str(expected)))
    if op == "eq":
        return value == expected
    if op == "ne":
        return value != expected
    if op == "gt":
        return value > expected
    if op == "gte":
        return value >= expected
    if op == "lt":
        return value < expected
    if op == "lte":
        return value <= expected
    if op == "contains":
        return expected in value
    if op == "not_contains":
        return expected not in value
    return value in expected


def apply_rules(records, strategy):
    """Filter and stably sort records with literal, type-checked predicates.

    Numeric CSV cells are parsed as Decimal; missing/malformed cells never
    satisfy a filter. Missing sort values always follow known values.
    """
    policy = validate_strategy(strategy)
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("records must be a list of dictionaries")
    selected = [row for row in records if all(_matches(row, rule) for rule in policy["filters"])]
    for order in reversed(policy["order_by"]):
        field = order["field"]
        known = [row for row in selected if _record_value(row, field) is not None]
        unknown = [row for row in selected if _record_value(row, field) is None]
        known.sort(key=lambda row: _record_value(row, field), reverse=order["direction"] == "desc")
        selected = known + unknown
    return deepcopy(selected)


def deterministic_batches(records, handle, dataset_version, batch_size=500):
    """Yield distinct item records in MD5(public-handle:version:item-id) order.

    The caller must supply the participant's public handle, never a PAT.
    Duplicate item IDs retain their first record; missing IDs are skipped.
    """
    if (not isinstance(handle, str) or not re.fullmatch(r"[\w.-]{1,100}", handle)
            or not isinstance(dataset_version, str) or not dataset_version.strip()
            or ":" in dataset_version or any(c.isspace() for c in dataset_version)):
        raise ValueError("a public handle and nonempty dataset version are required; never pass credentials")
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if not isinstance(records, list) or any(not isinstance(row, dict) for row in records):
        raise ValueError("records must be a list of dictionaries")
    distinct = {}
    for row in records:
        item_id = row.get("item_id")
        if isinstance(item_id, str) and item_id.strip():
            distinct.setdefault(item_id, row)
    def key(item_id):
        seed = f"{handle}:{dataset_version}:{item_id}".encode("utf-8")
        return hashlib.md5(seed, usedforsecurity=False).hexdigest(), item_id
    ordered = sorted(distinct, key=key)
    for offset in range(0, len(ordered), batch_size):
        yield deepcopy([distinct[item_id] for item_id in ordered[offset:offset + batch_size]])


def learn_from_feedback(strategy, feedback):
    """Return advisory review proposals; never rewrite rules, facts, or prices."""
    policy = validate_strategy(strategy)
    if not isinstance(feedback, list) or any(not isinstance(entry, dict) for entry in feedback):
        raise ValueError("feedback must be a list of dictionaries")
    counts = {}
    for entry in feedback:
        rejected = (entry.get("rejected") is True or entry.get("status") in {"rejected", "disqualified"}
                    or entry.get("review_status") in {"rejected", "disqualified"})
        if not rejected:
            continue
        code = entry.get("review_code")
        code = code if isinstance(code, str) and code.strip() else "UNKNOWN"
        counts[code] = counts.get(code, 0) + 1
    proposals = {
        "MODEL_MISMATCH": "제조사와 전체 모델명을 확인한 뒤 판매가 근거를 수집합니다.",
        "VAT_UNKNOWN": "부가세 포함 여부를 확인한 뒤 같은 세금 기준으로 비교합니다.",
        "PRICE_GAP_TOO_SMALL": "확인한 가격으로 기준을 넘는 후보를 우선 조사합니다. 관측 가격을 낮춰 적지 않습니다.",
        "COMPARISON_BASIS_MISMATCH": "공식 fact의 단위·세금·비교 기준을 그대로 사용합니다.",
    }
    suggestions = [{"review_code": code, "count": count,
                    "proposal": proposals.get(code, "반려 사유를 읽고 다음 후보에서 확인할 근거와 조건을 보완합니다.")}
                   for code, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))]
    return {"strategy": policy, "review_code_counts": dict(sorted(counts.items())),
            "suggestions": suggestions, "requires_human_review": True}
