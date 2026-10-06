"""Ecommerce checkout: COD + Razorpay."""

from __future__ import annotations

import time
import uuid
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gst import allocate_order_discount_to_lines, round_money
from app.models import Customer, CustomerAddress, Item, Stock, Transaction, Vendor
from app.models.ecommerce import PaymentEvent
from app.models.orders import SaleOrder
from app.services.offers_eval import OfferError, record_redemption, validate_offer
from app.services.razorpay_client import (
    RazorpayError,
    create_order,
    credentials_for_vendor,
    verify_payment_signature,
    verify_webhook_signature,
)
from app.services.sales_orders import SalesError, create_sale_order, mark_sale_order_paid


class CheckoutError(Exception):
    pass


def store_enabled(vendor: Vendor) -> bool:
    settings = vendor.settings if isinstance(vendor.settings, dict) else {}
    return bool(settings.get("features", {}).get("store_enabled"))


def shipping_charge(
    vendor: Vendor,
    subtotal: float,
    free_shipping: bool = False,
    total_qty: int | None = None,
) -> float:
    from app.services.pricing import shipping_charge_for_qty

    settings = vendor.settings if isinstance(vendor.settings, dict) else {}
    return shipping_charge_for_qty(
        settings,
        total_qty=int(total_qty or 0),
        subtotal=subtotal,
        free_shipping=free_shipping,
    )


def find_or_create_customer(
    db: Session,
    *,
    vendor_id: int,
    user_id: int,
    email: str | None,
    name: str | None,
) -> Customer:
    existing = db.scalar(
        select(Customer).where(Customer.vendor_id == vendor_id, Customer.user_id == user_id)
    )
    if existing:
        return existing
    if email:
        by_email = db.scalar(
            select(Customer).where(Customer.vendor_id == vendor_id, Customer.email == email)
        )
        if by_email:
            if not by_email.user_id:
                by_email.user_id = user_id
            return by_email
    c = Customer(
        vendor_id=vendor_id,
        name=(name or email or "Online Customer")[:100],
        email=email,
        party_type="CUSTOMER",
        acquisition_source="ONLINE",
        status="ACTIVE",
        user_id=user_id,
        member_since=date.today(),
    )
    db.add(c)
    db.flush()
    return c


def save_shipping_address(
    db: Session,
    *,
    vendor_id: int,
    customer_id: int,
    address: dict[str, Any] | None,
) -> None:
    if not address:
        return
    if not any(address.get(k) for k in ("street", "city", "zip", "state")):
        return
    for row in db.scalars(
        select(CustomerAddress).where(
            CustomerAddress.customer_id == customer_id,
            CustomerAddress.vendor_id == vendor_id,
            CustomerAddress.status == "ACTIVE",
        )
    ).all():
        row.status = "INACTIVE"
    db.add(
        CustomerAddress(
            vendor_id=vendor_id,
            customer_id=customer_id,
            street=address.get("street"),
            city=address.get("city"),
            state=address.get("state"),
            zip=address.get("zip"),
            status="ACTIVE",
        )
    )
    db.flush()


def _load_cart_lines(
    db: Session,
    *,
    vendor_id: int,
    items: list[dict[str, Any]],
    default_location_id: int | None,
) -> tuple[list[dict[str, Any]], float]:
    if not items:
        raise CheckoutError("Cart is empty")
    lines = []
    subtotal = 0.0
    for raw in items:
        item_id = int(raw.get("item_id") or raw.get("id"))
        qty = int(raw.get("quantity") or 1)
        if qty <= 0:
            raise CheckoutError("Invalid quantity")
        item = db.get(Item, item_id)
        if (
            not item
            or item.vendor_id != vendor_id
            or item.status != "ACTIVE"
            or not item.is_sellable
            or not item.is_online_sale
        ):
            raise CheckoutError(f"Item {item_id} not available online")
        unit = float(raw.get("unit_price") if raw.get("unit_price") is not None else item.sale_price)
        loc_id = int(raw.get("location_id") or default_location_id or 0)
        if not loc_id:
            raise CheckoutError("No stock location")
        lines.append(
            {
                "item_id": item_id,
                "location_id": loc_id,
                "quantity": qty,
                "unit_price": unit,
            }
        )
        subtotal = round_money(subtotal + qty * unit)
    return lines, subtotal


def _build_order_payload(
    *,
    order_code: str,
    customer: Customer,
    lines: list[dict[str, Any]],
    address: dict[str, Any] | None,
    offer: dict[str, Any] | None,
    shipping: float,
    payment_status: str,
    payment_method: str,
    razorpay_order_id: str | None = None,
) -> dict[str, Any]:
    addr = address or {}
    return {
        "order_code": order_code,
        "order_date": date.today(),
        "customer_id": customer.id,
        "sales_channel": "ECOMMERCE",
        "status": "CONFIRMED",
        "payment_status": payment_status,
        "fulfillment_status": "UNFULFILLED",
        "payment_method": payment_method,
        "offer_code": offer.get("code") if offer else None,
        "shipping_charge": shipping,
        "handling_charge": 0,
        "shipping_street": addr.get("street"),
        "shipping_city": addr.get("city"),
        "shipping_state": addr.get("state"),
        "shipping_zip": addr.get("zip"),
        "shipping_phone": addr.get("phone"),
        "shipping_name": addr.get("name") or customer.name,
        "razorpay_order_id": razorpay_order_id,
        "items": lines,
    }


def checkout_cod(
    db: Session,
    *,
    vendor: Vendor,
    user_id: int,
    email: str | None,
    name: str | None,
    items: list[dict[str, Any]],
    address: dict[str, Any] | None = None,
    offer_code: str | None = None,
) -> SaleOrder:
    if not store_enabled(vendor):
        raise CheckoutError("Store is disabled")
    feats = (vendor.settings or {}).get("features") or {}
    if not feats.get("cod", True):
        raise CheckoutError("COD is disabled for this store")

    customer = find_or_create_customer(
        db, vendor_id=vendor.id, user_id=user_id, email=email, name=name
    )
    save_shipping_address(db, vendor_id=vendor.id, customer_id=customer.id, address=address)

    lines, subtotal = _load_cart_lines(
        db, vendor_id=vendor.id, items=items, default_location_id=vendor.default_location_id
    )
    offer = None
    if offer_code:
        try:
            offer = validate_offer(
                db,
                vendor_id=vendor.id,
                code=offer_code,
                subtotal=subtotal,
                party_type=customer.party_type,
                sales_channel="ECOMMERCE",
                customer_id=customer.id,
                item_ids=[int(x["item_id"]) for x in lines],
            )
        except OfferError as e:
            raise CheckoutError(str(e)) from e
        lines = allocate_order_discount_to_lines(lines, offer["discount_amount"])

    total_qty = sum(int(x.get("quantity") or 0) for x in lines)
    ship = shipping_charge(
        vendor,
        subtotal,
        free_shipping=bool(offer and offer.get("free_shipping")),
        total_qty=total_qty,
    )
    order_code = f"SO-ECO-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    payload = _build_order_payload(
        order_code=order_code,
        customer=customer,
        lines=lines,
        address=address,
        offer=offer,
        shipping=ship,
        payment_status="UNPAID",
        payment_method="COD",
    )
    try:
        so = create_sale_order(
            db,
            vendor_id=vendor.id,
            data=payload,
            created_by=email,
            user_id=user_id,
            stock_mode="deduct",
        )
    except SalesError as e:
        raise CheckoutError(str(e)) from e

    if offer:
        record_redemption(
            db,
            vendor_id=vendor.id,
            offer_id=int(offer["offer_id"]),
            customer_id=customer.id,
            sale_order_id=so.id,
        )
    db.add(
        Transaction(
            vendor_id=vendor.id,
            transaction_date=date.today(),
            type="SALE_PAYMENT",
            direction="IN",
            amount=float(so.total_order_value),
            reference_id=so.id,
            reference_type="SALE_ORDER",
            payment_method="COD",
            created_by=email,
        )
    )
    db.flush()
    return so


def checkout_razorpay_create(
    db: Session,
    *,
    vendor: Vendor,
    user_id: int,
    email: str | None,
    name: str | None,
    items: list[dict[str, Any]],
    address: dict[str, Any] | None = None,
    offer_code: str | None = None,
) -> dict[str, Any]:
    if not store_enabled(vendor):
        raise CheckoutError("Store is disabled")
    feats = (vendor.settings or {}).get("features") or {}
    if not feats.get("razorpay", True):
        raise CheckoutError("Razorpay is disabled for this store")

    key_id, key_secret, mock = credentials_for_vendor(vendor.settings if isinstance(vendor.settings, dict) else {})
    if not mock and not (key_id and key_secret):
        raise CheckoutError("Razorpay is not configured")

    customer = find_or_create_customer(
        db, vendor_id=vendor.id, user_id=user_id, email=email, name=name
    )
    save_shipping_address(db, vendor_id=vendor.id, customer_id=customer.id, address=address)

    lines, subtotal = _load_cart_lines(
        db, vendor_id=vendor.id, items=items, default_location_id=vendor.default_location_id
    )
    offer = None
    if offer_code:
        try:
            offer = validate_offer(
                db,
                vendor_id=vendor.id,
                code=offer_code,
                subtotal=subtotal,
                party_type=customer.party_type,
                sales_channel="ECOMMERCE",
                customer_id=customer.id,
                item_ids=[int(x["item_id"]) for x in lines],
            )
        except OfferError as e:
            raise CheckoutError(str(e)) from e
        lines = allocate_order_discount_to_lines(lines, offer["discount_amount"])

    total_qty = sum(int(x.get("quantity") or 0) for x in lines)
    ship = shipping_charge(
        vendor,
        subtotal,
        free_shipping=bool(offer and offer.get("free_shipping")),
        total_qty=total_qty,
    )
    # Approximate net for Razorpay amount: subtotal - discount + shipping (GST inclusive prices)
    discount = float(offer["discount_amount"]) if offer else 0.0
    amount_rupees = round_money(max(0.0, subtotal - discount + ship))
    amount_paise = int(round(amount_rupees * 100))

    order_code = f"SO-ECO-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    try:
        rz = create_order(
            amount_paise=amount_paise,
            currency=vendor.currency or "INR",
            receipt=order_code[:40],
            notes={"orderCode": order_code, "vendorId": str(vendor.id)},
            key_id=key_id or "rzp_mock",
            key_secret=key_secret or "mock-secret",
            mock=mock,
        )
    except RazorpayError as e:
        raise CheckoutError(str(e)) from e

    payload = _build_order_payload(
        order_code=order_code,
        customer=customer,
        lines=lines,
        address=address,
        offer=offer,
        shipping=ship,
        payment_status="UNPAID",
        payment_method="UPI",
        razorpay_order_id=rz["id"],
    )
    try:
        so = create_sale_order(
            db,
            vendor_id=vendor.id,
            data=payload,
            created_by=email,
            user_id=user_id,
            stock_mode="reserve",
        )
    except SalesError as e:
        raise CheckoutError(str(e)) from e

    if offer:
        record_redemption(
            db,
            vendor_id=vendor.id,
            offer_id=int(offer["offer_id"]),
            customer_id=customer.id,
            sale_order_id=so.id,
        )

    db.add(
        PaymentEvent(
            vendor_id=vendor.id,
            provider="RAZORPAY",
            event_id=f"order.created:{rz['id']}",
            event_type="order.created",
            razorpay_order_id=rz["id"],
            sale_order_id=so.id,
            payload={"amount": amount_paise, "mock": mock},
        )
    )
    db.flush()
    return {
        "order_code": order_code,
        "sale_order_id": so.id,
        "razorpay_order_id": rz["id"],
        "amount": amount_paise,
        "currency": vendor.currency or "INR",
        "key_id": key_id or "rzp_mock",
        "mock": mock,
    }


def checkout_razorpay_verify(
    db: Session,
    *,
    vendor: Vendor,
    order_code: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    created_by: str | None = None,
) -> SaleOrder:
    if not store_enabled(vendor):
        raise CheckoutError("Store is disabled")
    key_id, key_secret, mock = credentials_for_vendor(vendor.settings if isinstance(vendor.settings, dict) else {})
    secret = key_secret or "mock-secret"
    if not verify_payment_signature(
        order_id=razorpay_order_id,
        payment_id=razorpay_payment_id,
        signature=razorpay_signature,
        secret=secret,
    ):
        raise CheckoutError("Payment verification failed")

    event_id = f"payment.captured:{razorpay_payment_id}"
    existing = db.scalar(
        select(PaymentEvent).where(
            PaymentEvent.vendor_id == vendor.id,
            PaymentEvent.event_id == event_id,
        )
    )
    if existing and existing.sale_order_id:
        so = db.get(SaleOrder, existing.sale_order_id)
        if so:
            return so

    try:
        so = mark_sale_order_paid(
            db,
            vendor_id=vendor.id,
            order_code=order_code,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            payment_method="UPI",
            created_by=created_by,
        )
    except SalesError as e:
        raise CheckoutError(str(e)) from e

    if not existing:
        db.add(
            PaymentEvent(
                vendor_id=vendor.id,
                provider="RAZORPAY",
                event_id=event_id,
                event_type="payment.captured",
                razorpay_order_id=razorpay_order_id,
                razorpay_payment_id=razorpay_payment_id,
                sale_order_id=so.id,
                payload={"mock": mock},
            )
        )
    db.add(
        Transaction(
            vendor_id=vendor.id,
            transaction_date=date.today(),
            type="SALE_PAYMENT",
            direction="IN",
            amount=float(so.total_order_value),
            reference_id=so.id,
            reference_type="SALE_ORDER",
            payment_method="UPI",
            reference_number=razorpay_payment_id,
            created_by=created_by,
        )
    )
    db.flush()
    return so


def handle_razorpay_webhook(
    db: Session,
    *,
    vendor: Vendor,
    body: bytes,
    signature: str,
) -> dict[str, Any]:
    key_id, key_secret, mock = credentials_for_vendor(vendor.settings if isinstance(vendor.settings, dict) else {})
    secret = key_secret or "mock-secret"
    if not mock and not verify_webhook_signature(body=body, signature=signature, secret=secret):
        raise CheckoutError("Invalid webhook signature")

    import json

    payload = json.loads(body.decode("utf-8"))
    event = payload.get("event") or "unknown"
    payment = (payload.get("payload") or {}).get("payment", {}).get("entity") or {}
    razorpay_payment_id = payment.get("id")
    razorpay_order_id = payment.get("order_id")
    event_id = f"webhook:{event}:{razorpay_payment_id or razorpay_order_id or uuid.uuid4().hex}"

    existing = db.scalar(
        select(PaymentEvent).where(PaymentEvent.vendor_id == vendor.id, PaymentEvent.event_id == event_id)
    )
    if existing:
        return {"duplicate": True, "event_id": event_id}

    so = None
    if razorpay_order_id:
        so = db.scalar(
            select(SaleOrder).where(
                SaleOrder.vendor_id == vendor.id,
                SaleOrder.razorpay_order_id == razorpay_order_id,
            )
        )
    if so and event in ("payment.captured", "order.paid") and razorpay_payment_id:
        if so.payment_status != "PAID":
            try:
                so = mark_sale_order_paid(
                    db,
                    vendor_id=vendor.id,
                    order_code=so.order_code,
                    razorpay_order_id=razorpay_order_id,
                    razorpay_payment_id=razorpay_payment_id,
                    payment_method="UPI",
                    created_by="webhook",
                )
            except SalesError as e:
                raise CheckoutError(str(e)) from e

    db.add(
        PaymentEvent(
            vendor_id=vendor.id,
            provider="RAZORPAY",
            event_id=event_id,
            event_type=event,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            sale_order_id=so.id if so else None,
            payload=payload,
        )
    )
    db.flush()
    return {"duplicate": False, "event_id": event_id, "sale_order_id": so.id if so else None}


def available_qty(db: Session, *, vendor_id: int, item_id: int, location_id: int | None) -> int:
    q = select(Stock).where(Stock.vendor_id == vendor_id, Stock.item_id == item_id)
    if location_id:
        q = q.where(Stock.location_id == location_id)
    rows = db.scalars(q).all()
    return sum(max(0, int(s.quantity_on_hand) - int(s.quantity_reserved)) for s in rows)
