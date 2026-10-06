"""Party trade price resolution for B2B."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gst import round_money
from app.models import Item, PartyPriceRule
from app.services.parties import TRADE_PARTY_TYPES

PRICE_MODES = frozenset({"PERCENT_OFF", "FIXED_PRICE", "FIXED_OFF"})

DEFAULT_COURIERS = ("AKR_PARCEL", "MARUTHI_PARCEL")
COURIER_LABELS = {
    "AKR_PARCEL": "AKR Parcel",
    "MARUTHI_PARCEL": "Maruthi Parcel",
}


def resolve_trade_price(
    msrp: float,
    mode: str | None,
    value: float | None,
) -> float:
    msrp = round_money(float(msrp or 0))
    if not mode or value is None:
        return msrp
    mode_u = mode.upper()
    val = float(value)
    if mode_u == "PERCENT_OFF":
        return round_money(max(0.0, msrp * (1 - val / 100)))
    if mode_u == "FIXED_OFF":
        return round_money(max(0.0, msrp - val))
    if mode_u == "FIXED_PRICE":
        return round_money(max(0.0, val))
    return msrp


def get_rule(
    db: Session,
    *,
    vendor_id: int,
    item_id: int,
    party_type: str,
) -> PartyPriceRule | None:
    pt = (party_type or "").upper()
    if pt not in TRADE_PARTY_TYPES:
        return None
    return db.scalar(
        select(PartyPriceRule).where(
            PartyPriceRule.vendor_id == vendor_id,
            PartyPriceRule.item_id == item_id,
            PartyPriceRule.party_type == pt,
            PartyPriceRule.status == "ACTIVE",
        )
    )


def resolve_item_prices(
    db: Session,
    *,
    vendor_id: int,
    item: Item,
    party_type: str,
) -> dict[str, Any]:
    msrp = round_money(float(item.sale_price or 0))
    pt = (party_type or "CUSTOMER").upper()
    rule = get_rule(db, vendor_id=vendor_id, item_id=item.id, party_type=pt)
    if rule:
        trade = resolve_trade_price(msrp, rule.mode, float(rule.value))
        return {
            "msrp": msrp,
            "trade_unit_price": trade,
            "suggested_sell": msrp,
            "rule_mode": rule.mode,
            "rule_value": float(rule.value),
        }
    return {
        "msrp": msrp,
        "trade_unit_price": msrp,
        "suggested_sell": msrp,
        "rule_mode": None,
        "rule_value": None,
    }


def shipping_charge_for_qty(
    settings: dict | None,
    *,
    total_qty: int,
    subtotal: float,
    free_shipping: bool = False,
) -> float:
    """Qty-tier shipping; falls back to flat_rate / free_over."""
    if free_shipping:
        return 0.0
    shipping = (settings or {}).get("shipping") or {}
    tiers = shipping.get("qty_tiers") or []
    if tiers:
        # Sort by max_qty ascending; null max = unlimited last
        def sort_key(t: dict) -> tuple[int, float]:
            mq = t.get("max_qty")
            if mq is None:
                return (1, float("inf"))
            return (0, float(mq))

        for tier in sorted(tiers, key=sort_key):
            mq = tier.get("max_qty")
            charge = float(tier.get("charge") or 0)
            if mq is None or total_qty <= int(mq):
                return round_money(charge)
        return 0.0

    flat = float(shipping.get("flat_rate") or 0)
    free_over = shipping.get("free_over")
    if free_over is not None and subtotal >= float(free_over):
        return 0.0
    return round_money(flat)


def courier_allowlist(settings: dict | None) -> list[str]:
    shipping = (settings or {}).get("shipping") or {}
    raw = shipping.get("couriers") or list(DEFAULT_COURIERS)
    out = []
    for c in raw:
        code = str(c).upper()
        if code in COURIER_LABELS and code not in out:
            out.append(code)
    return out or list(DEFAULT_COURIERS)


def normalize_courier(code: str | None, settings: dict | None = None) -> str:
    if not code:
        raise ValueError("courier is required")
    c = code.strip().upper().replace(" ", "_")
    # accept display names
    aliases = {
        "AKR_PARCEL": "AKR_PARCEL",
        "AKRPARCEL": "AKR_PARCEL",
        "AKR": "AKR_PARCEL",
        "MARUTHI_PARCEL": "MARUTHI_PARCEL",
        "MARUTHIPARCEL": "MARUTHI_PARCEL",
        "MARUTHI": "MARUTHI_PARCEL",
    }
    normalized = aliases.get(c, c)
    allowed = courier_allowlist(settings)
    if normalized not in allowed:
        raise ValueError(f"courier must be one of {allowed}")
    return normalized


def courier_label(code: str | None) -> str | None:
    if not code:
        return None
    return COURIER_LABELS.get(code.upper(), code)
