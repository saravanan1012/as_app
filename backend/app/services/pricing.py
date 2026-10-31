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


def normalize_shipping(shipping: dict | None) -> dict[str, Any]:
    """
    Canonical shipping shape:

    {
      ecommerce: { enabled, flat_rate, free_over_enabled, free_over },
      b2b: { qty_tiers },
      couriers: [...]
    }

    Legacy flat keys (flat_rate / free_over / qty_tiers at top level) are migrated.
    """
    raw = dict(shipping or {})
    has_split = "ecommerce" in raw or "b2b" in raw

    if has_split:
        eco_in = dict(raw.get("ecommerce") or {})
        b2b_in = dict(raw.get("b2b") or {})
        eco = {
            "enabled": bool(eco_in.get("enabled", True)),
            "flat_rate": float(eco_in.get("flat_rate") or 0),
            "free_over_enabled": bool(
                eco_in.get(
                    "free_over_enabled",
                    eco_in.get("free_over") is not None,
                )
            ),
            "free_over": (
                float(eco_in["free_over"])
                if eco_in.get("free_over") is not None
                else None
            ),
        }
        b2b = {"qty_tiers": list(b2b_in.get("qty_tiers") or [])}
        couriers = raw.get("couriers") or b2b_in.get("couriers") or list(DEFAULT_COURIERS)
        return {"ecommerce": eco, "b2b": b2b, "couriers": list(couriers)}

    # Legacy single blob → split channels
    free_over = raw.get("free_over")
    return {
        "ecommerce": {
            "enabled": True,
            "flat_rate": float(raw.get("flat_rate") or 0),
            "free_over_enabled": free_over is not None,
            "free_over": float(free_over) if free_over is not None else None,
        },
        "b2b": {"qty_tiers": list(raw.get("qty_tiers") or [])},
        "couriers": list(raw.get("couriers") or list(DEFAULT_COURIERS)),
    }


def _qty_tier_charge(tiers: list[dict], total_qty: int) -> float:
    if not tiers:
        return 0.0

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


def shipping_charge_ecommerce(
    settings: dict | None,
    *,
    subtotal: float,
    free_shipping: bool = False,
) -> float:
    """Online store / direct customer — amount-based flat + optional free_over."""
    if free_shipping:
        return 0.0
    ship = normalize_shipping((settings or {}).get("shipping") or {})
    eco = ship["ecommerce"]
    if not eco.get("enabled", True):
        return 0.0
    free_over = eco.get("free_over")
    if (
        eco.get("free_over_enabled")
        and free_over is not None
        and float(subtotal) >= float(free_over)
    ):
        return 0.0
    return round_money(float(eco.get("flat_rate") or 0))


def shipping_charge_b2b(
    settings: dict | None,
    *,
    total_qty: int,
    free_shipping: bool = False,
) -> float:
    """B2B trade — qty tiers (bags/units)."""
    if free_shipping:
        return 0.0
    ship = normalize_shipping((settings or {}).get("shipping") or {})
    return _qty_tier_charge(list(ship["b2b"].get("qty_tiers") or []), int(total_qty or 0))


def shipping_charge_for_qty(
    settings: dict | None,
    *,
    total_qty: int,
    subtotal: float,
    free_shipping: bool = False,
    channel: str = "b2b",
) -> float:
    """
    Channel-aware shipping.
    channel=b2b → qty tiers; channel=ecommerce → amount-based free_over / flat.
    """
    ch = (channel or "b2b").lower()
    if ch in ("ecommerce", "store", "online", "direct"):
        return shipping_charge_ecommerce(
            settings, subtotal=subtotal, free_shipping=free_shipping
        )
    return shipping_charge_b2b(
        settings, total_qty=total_qty, free_shipping=free_shipping
    )


def ecommerce_shipping_public(settings: dict | None) -> dict[str, Any]:
    """Safe public rules for store meta / checkout UI."""
    ship = normalize_shipping((settings or {}).get("shipping") or {})
    eco = ship["ecommerce"]
    return {
        "enabled": bool(eco.get("enabled", True)),
        "flat_rate": float(eco.get("flat_rate") or 0),
        "free_over_enabled": bool(eco.get("free_over_enabled")),
        "free_over": eco.get("free_over"),
    }


def courier_allowlist(settings: dict | None) -> list[str]:
    ship = normalize_shipping((settings or {}).get("shipping") or {})
    raw = ship.get("couriers") or list(DEFAULT_COURIERS)
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
