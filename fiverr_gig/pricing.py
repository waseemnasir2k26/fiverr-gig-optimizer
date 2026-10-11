"""Pricing calculator: Fiverr's 20% seller fee, ladder suggestion, hourly equivalent."""
from __future__ import annotations

from . import rules


def net_from_gross(gross: float, fee: float = rules.SELLER_FEE) -> float:
    if gross < 0:
        raise ValueError("price cannot be negative")
    return round(gross * (1 - fee), 2)


def gross_for_net(net_target: float, fee: float = rules.SELLER_FEE) -> float:
    """Sticker price you must quote to keep `net_target` after the seller fee."""
    if net_target < 0:
        raise ValueError("net target cannot be negative")
    if not 0 <= fee < 1:
        raise ValueError("fee must be in [0, 1)")
    return round(net_target / (1 - fee), 2)


def hourly_equivalent(gross: float, hours: float, fee: float = rules.SELLER_FEE) -> float:
    if hours <= 0:
        raise ValueError("hours must be positive")
    return round(net_from_gross(gross, fee) / hours, 2)


def buyer_total_estimate(gross: float) -> float:
    """Rough buyer checkout: 5.5% service fee plus a small-order fee under $200.
    An estimate only: Fiverr's help pages differ on the small-order fee."""
    fee = gross * rules.BUYER_FEE
    if gross < rules.BUYER_SMALL_ORDER_LIMIT:
        fee += rules.BUYER_SMALL_ORDER_FEE
    return round(gross + fee, 2)


def _round_price(x: float) -> int:
    """Round to a clean sticker: nearest 5 below 100, nearest 10 below 500, else nearest 25."""
    step = 5 if x < 100 else 10 if x < 500 else 25
    return int(round(x / step) * step)


def suggest_ladder(basic: float, multipliers: dict[str, float] | None = None) -> dict:
    """Suggest a Basic/Standard/Premium ladder from the Basic sticker price.

    Multipliers (1x / 2.5x / 5x) are a heuristic, not a Fiverr rule.
    """
    if basic <= 0:
        raise ValueError("basic price must be positive")
    mult = multipliers or rules.LADDER_MULTIPLIERS
    ladder = {}
    prev = 0
    for tier in rules.PACKAGE_TIERS:
        price = _round_price(basic * mult[tier]) if tier != "basic" else int(round(basic))
        if price <= prev:
            price = prev + 5
        prev = price
        ladder[tier] = {"gross": price, "net": net_from_gross(price)}
    return ladder


def report(gross: float | None = None, net_target: float | None = None, hours: float | None = None) -> dict:
    if (gross is None) == (net_target is None):
        raise ValueError("give exactly one of gross or net_target")
    if gross is None:
        gross = gross_for_net(net_target)
    out = {
        "gross": round(gross, 2),
        "fee_rate": rules.SELLER_FEE,
        "fee": round(gross * rules.SELLER_FEE, 2),
        "net": net_from_gross(gross),
        "buyer_checkout_estimate": buyer_total_estimate(gross),
    }
    if hours is not None:
        out["hours"] = hours
        out["net_hourly"] = hourly_equivalent(gross, hours)
    return out
