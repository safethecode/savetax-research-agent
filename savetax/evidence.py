"""Conservative, offline checks for manually observed comparison offers.

This module never fetches a URL or invents a quote. ``price_verified`` means
the researcher actually inspected the price page; absent that confirmation,
an offer cannot be marked verified by this evaluator.
"""

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, localcontext
import ipaddress
import re
from urllib.parse import urlsplit


TARGET_KRW = "60000000000"
_KST = timezone(timedelta(hours=9))
_NUMBER = re.compile(r"[+]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)\Z")
_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z")
_CAVEAT = (
    "과거 납품요구의 가격과 현재 관측 판매가는 시점이 다르므로, 관측 절감가능액은 "
    "당시 구매 가능성·납품 완료·심사 인정액·실현절감액을 증명하지 않습니다."
)


def _number(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    text = str(value)
    if not _NUMBER.fullmatch(text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if not number.is_finite() or number < 0 or (positive and number <= 0):
        return None
    if number.as_tuple().exponent < -6:
        return None
    return number


def _decimal_string(number):
    result = format(number, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return result or "0"


def _source_valid(url):
    if (not isinstance(url, str) or len(url) > 2048
            or any(char.isspace() or ord(char) < 32 for char in url) or "\\" in url):
        return False
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if (parsed.scheme != "https" or not host or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443)):
            return False
        host = host.rstrip(".").lower()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            if re.fullmatch(r"[0-9.]+", host):
                return False
            return "." in host and all(part and re.fullmatch(r"[\w-]+", part) for part in host.split("."))
    except (ValueError, UnicodeError):
        return False


def _observation_valid(value, now):
    if not isinstance(value, str):
        return False
    try:
        if _DATE.fullmatch(value):
            observed = date.fromisoformat(value)
            return date(2015, 1, 1) <= observed <= now.astimezone(_KST).date()
        observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return (observed.tzinfo is not None and observed.utcoffset() is not None
                and observed.date() >= date(2015, 1, 1) and observed <= now)
    except (ValueError, OverflowError):
        return False


def _base_result():
    return {"status": "needs_review", "comparison_unit_price": None,
            "potential_savings_krw": None, "observed_potential_savings_krw": None,
            "reviewed_amount_krw": None, "realized_savings_krw": None,
            "eligible_for_preview": False, "reasons": [], "selected_offer": None,
            "caveats": [_CAVEAT], "target_krw": TARGET_KRW}


def _fact_values(fact):
    reasons = []
    for key in ("item_id", "model", "unit"):
        if not isinstance(fact.get(key), str) or not fact[key].strip():
            reasons.append("fact_" + key + "_unknown")
    for key in ("vat_included", "installation_required", "scorable"):
        if type(fact.get(key)) is not bool:
            reasons.append("fact_" + key + "_unknown")
    quantity = _number(fact.get("quantity"), positive=True)
    if quantity is None:
        reasons.append("fact_quantity_invalid")
    if "comparable_amount_krw" in fact:
        amount = _number(fact["comparable_amount_krw"])
        if amount is None:
            reasons.append("fact_comparable_amount_invalid")
    else:
        delivered_price = _number(fact.get("delivered_unit_price"), positive=True)
        if delivered_price is None:
            reasons.append("fact_delivered_unit_price_invalid")
        amount = delivered_price * quantity if delivered_price is not None and quantity is not None else None
    return quantity, amount, reasons


def _offer_value(fact, offer, quantity, now):
    reasons = []
    if not isinstance(offer, dict):
        return None, ["offer_not_an_object"]
    if not _source_valid(offer.get("url")):
        reasons.append("source_https_public_url_required")
    quote = offer.get("quote")
    if not isinstance(quote, str) or not quote.strip() or len(quote) > 2000:
        reasons.append("source_quote_required")
    if not _observation_valid(offer.get("observed_at"), now):
        reasons.append("observation_date_invalid")
    for key in ("model", "unit"):
        if offer.get(key) != fact[key]:
            reasons.append(key + "_mismatch")
    if type(offer.get("vat_included")) is not bool or offer["vat_included"] != fact["vat_included"]:
        reasons.append("vat_basis_mismatch_or_unknown")
    for key in ("stock_confirmed", "unconditional", "price_verified"):
        if offer.get(key) is not True:
            reasons.append(key + "_required")
    if type(offer.get("domestic")) is not bool:
        reasons.append("market_origin_unknown")
    if offer.get("currency") != "KRW":
        reasons.append("currency_must_be_krw")
    pack_quantity = _number(offer.get("pack_quantity"), positive=True)
    if pack_quantity != Decimal(1):
        reasons.append("single_unit_pack_required")
    price = _number(offer.get("unit_price"), positive=True)
    shipping = _number(offer.get("shipping_total"))
    installation = _number(offer.get("installation_total"))
    if price is None:
        reasons.append("observed_unit_price_invalid")
    if shipping is None:
        reasons.append("shipping_total_unknown")
    if installation is None:
        reasons.append("installation_total_unknown")
    if type(offer.get("installation_included")) is not bool:
        reasons.append("installation_inclusion_unknown")
    if (fact["installation_required"] and offer.get("installation_included") is not True
            and (installation is None or installation <= 0)):
        reasons.append("required_installation_not_evidenced")
    if offer.get("installation_included") is True and installation is not None and installation != 0:
        reasons.append("installation_cost_double_count")
    landed = None
    if offer.get("domestic") is False:
        landed = _number(offer.get("landed_cost_krw"), positive=True)
        if landed is None or offer.get("taxes_verified") is not True:
            reasons.append("overseas_landed_cost_and_taxes_required")
        if landed is not None and price is not None and landed < price:
            reasons.append("overseas_landed_cost_below_observed_price")
    if reasons:
        return None, reasons
    if landed is not None:
        # landed_cost_krw is the verified all-in cost per fact comparison unit.
        return landed, []
    comparison = price + (shipping + installation) / quantity
    # The submission API accepts six decimals. Rounding up never understates
    # the observed all-in price or inflates the official potential amount.
    return comparison.quantize(Decimal("0.000001"), rounding=ROUND_CEILING), []


def evaluate_candidate(fact, offers):
    """Evaluate supplied facts and independently observed, all-in KRW offers.

    A domestic valid offer wins over every overseas offer. An overseas offer
    additionally requires an all-in per-unit ``landed_cost_krw`` and explicit
    ``taxes_verified=True``. Multi-packs and unknown comparison conditions
    remain under review rather than being silently converted.

    Monetary result fields use plain decimal strings. Observed potential is
    not an official review award or a realized saving; those stay unknown.
    """
    result = _base_result()
    if not isinstance(fact, dict) or not isinstance(offers, list):
        result["reasons"] = ["fact_object_and_offer_list_required"]
        return result
    # Wide local precision preserves six-decimal source values and totals.
    with localcontext() as context:
        context.prec = 80
        quantity, amount, fact_reasons = _fact_values(fact)
        if fact_reasons:
            result["reasons"] = fact_reasons
            return result
        valid, exclusions = [], []
        now = datetime.now(timezone.utc)
        for index, offer in enumerate(offers):
            comparison, reasons = _offer_value(fact, offer, quantity, now)
            exclusions.extend(f"offer[{index}]:{reason}" for reason in reasons)
            if comparison is not None:
                valid.append((offer["domestic"] is not True, comparison, offer["url"], index, offer))
        if not valid:
            result["reasons"] = exclusions or ["no_observed_offers"]
            return result
        _, comparison, _, _, selected = min(valid, key=lambda entry: entry[:4])
        savings = max(amount - comparison * quantity, Decimal(0)).to_integral_value(rounding=ROUND_FLOOR)
        delivered_price = amount / quantity
        threshold_met = (delivered_price >= Decimal("1.2") * comparison
                         or delivered_price - comparison >= Decimal("1000000"))
        result.update({"status": "verified" if savings > 0 else "no_saving",
                       "comparison_unit_price": _decimal_string(comparison),
                       "potential_savings_krw": _decimal_string(savings),
                       "observed_potential_savings_krw": _decimal_string(savings),
                       "eligible_for_preview": bool(savings >= 1 and threshold_met and fact["scorable"]),
                       "selected_offer": deepcopy(selected), "reasons": exclusions})
        if not fact["scorable"]:
            result["reasons"].append("fact_not_scorable")
        if savings <= 0:
            result["reasons"].append("no_positive_savings")
        elif not threshold_met:
            result["reasons"].append("price_gap_below_threshold")
        if selected["domestic"] is False:
            result["caveats"].append("해외 비교는 확인된 단위당 원화 도착원가와 세금 근거에 한정됩니다.")
        return result
