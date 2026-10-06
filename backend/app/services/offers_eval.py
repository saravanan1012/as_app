"""Offer validation for ecommerce checkout."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.gst import round_money
from app.models import Offer
from app.models.ecommerce import OfferRedemption


class OfferError(Exception):
    pass


def validate_offer(
    db: Session,
    *,
    vendor_id: int,
    code: str,
    subtotal: float,
    party_type: str | None = "CUSTOMER",
    sales_channel: str = "ECOMMERCE",
    customer_id: int | None = None,
    item_ids: list[int] | None = None,
) -> dict[str, Any]:
    offer = db.scalar(
        select(Offer).where(
            Offer.vendor_id == vendor_id,
            Offer.code == code.strip().upper(),
        )
    )
    if not offer or not offer.is_active:
        raise OfferError("Offer not found or inactive")

    today = date.today()
    if offer.start_date and today < offer.start_date:
        raise OfferError("Offer not started yet")
    if offer.end_date and today > offer.end_date:
        raise OfferError("Offer expired")

    channel = (offer.sales_channel or "ECOMMERCE").upper()
    if channel not in ("ALL", "*", sales_channel.upper()):
        raise OfferError("Offer not valid for this channel")

    if offer.customer_type:
        if (party_type or "CUSTOMER").upper() != offer.customer_type.upper():
            raise OfferError("Offer not valid for your customer type")

    if offer.min_order_value is not None and subtotal < float(offer.min_order_value):
        raise OfferError(f"Minimum order value is {float(offer.min_order_value)}")

    if offer.item_id and item_ids is not None and offer.item_id not in item_ids:
        raise OfferError("Offer not valid for cart items")

    if offer.max_uses is not None:
        total_uses = db.scalar(
            select(func.count()).select_from(OfferRedemption).where(
                OfferRedemption.vendor_id == vendor_id,
                OfferRedemption.offer_id == offer.id,
            )
        ) or 0
        if total_uses >= int(offer.max_uses):
            raise OfferError("Offer usage limit reached")

    if offer.max_uses_per_customer is not None and customer_id:
        cust_uses = db.scalar(
            select(func.count()).select_from(OfferRedemption).where(
                OfferRedemption.vendor_id == vendor_id,
                OfferRedemption.offer_id == offer.id,
                OfferRedemption.customer_id == customer_id,
            )
        ) or 0
        if cust_uses >= int(offer.max_uses_per_customer):
            raise OfferError("You have already used this offer the maximum times")

    discount = 0.0
    if offer.discount_percentage is not None:
        discount = round_money(subtotal * float(offer.discount_percentage) / 100)
    if offer.discount_amount is not None:
        discount = max(discount, round_money(float(offer.discount_amount)))
    discount = min(discount, round_money(subtotal))

    return {
        "valid": True,
        "offer_id": offer.id,
        "code": offer.code,
        "discount_amount": discount,
        "discount_percentage": float(offer.discount_percentage) if offer.discount_percentage is not None else None,
        "free_shipping": bool(offer.free_shipping),
        "customer_type": offer.customer_type,
        "sales_channel": offer.sales_channel,
    }


def record_redemption(
    db: Session,
    *,
    vendor_id: int,
    offer_id: int,
    customer_id: int | None,
    sale_order_id: int,
) -> OfferRedemption:
    row = OfferRedemption(
        vendor_id=vendor_id,
        offer_id=offer_id,
        customer_id=customer_id,
        sale_order_id=sale_order_id,
    )
    db.add(row)
    db.flush()
    return row
