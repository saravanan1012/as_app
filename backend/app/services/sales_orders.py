"""Sales orders create / confirm / cancel + sale returns."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gst import aggregate_sale_lines, round_money
from app.models import Customer, Item, Location, TaxCategory, Vendor
from app.models.orders import (
    OrderStatusEvent,
    SaleOrder,
    SaleOrderDetail,
    SaleReturn,
    SaleReturnDetail,
)
from app.services.pricing import courier_label, normalize_courier
from app.services.stock_ledger import (
    StockError,
    add_stock,
    consume_reservation,
    deduct_stock,
    release_reservation,
    reserve_stock,
)

SO_STATUSES = frozenset({"DRAFT", "CONFIRMED", "CANCELLED", "RETURNED"})
STOCKED_STATUSES = frozenset({"CONFIRMED"})


class SalesError(Exception):
    pass


def _default_location_id(db: Session, vendor_id: int) -> int:
    v = db.get(Vendor, vendor_id)
    if v and v.default_location_id:
        return v.default_location_id
    loc = db.scalar(select(Location).where(Location.vendor_id == vendor_id).order_by(Location.id))
    if not loc:
        raise SalesError("No location for vendor")
    return loc.id


def _gst_meta(db: Session, vendor_id: int, item_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not item_ids:
        return {}
    rows = db.execute(
        select(Item.id, Item.sale_price_includes_gst, TaxCategory.gst_rate)
        .outerjoin(TaxCategory, Item.tax_category_id == TaxCategory.id)
        .where(Item.vendor_id == vendor_id, Item.id.in_(item_ids))
    ).all()
    return {
        int(r.id): {
            "rate": float(r.gst_rate or 0),
            "includes": bool(r.sale_price_includes_gst),
        }
        for r in rows
    }


def _vendor_state(db: Session, vendor_id: int) -> str | None:
    v = db.get(Vendor, vendor_id)
    if not v:
        return None
    return v.state_code or (v.settings or {}).get("tax", {}).get("state_code")


def _record_status(
    db: Session,
    *,
    vendor_id: int,
    order_id: int,
    from_status: str | None,
    to_status: str,
    created_by: str | None,
    note: str | None = None,
) -> None:
    db.add(
        OrderStatusEvent(
            vendor_id=vendor_id,
            order_type="SALE",
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
            created_by=created_by,
        )
    )


def _apply_sale_stock(
    db: Session,
    *,
    vendor_id: int,
    so: SaleOrder,
    details: list[SaleOrderDetail],
    reason: str,
    created_by: str | None,
    deduct: bool,
) -> None:
    try:
        for d in details:
            if deduct:
                deduct_stock(
                    db,
                    vendor_id=vendor_id,
                    item_id=d.item_id,
                    location_id=d.location_id,
                    quantity=int(d.quantity),
                    reason=reason,
                    reference_type="SALE_ORDER",
                    reference_id=so.id,
                    created_by=created_by,
                )
            else:
                add_stock(
                    db,
                    vendor_id=vendor_id,
                    item_id=d.item_id,
                    location_id=d.location_id,
                    quantity=int(d.quantity),
                    reason=reason,
                    reference_type="SALE_ORDER",
                    reference_id=so.id,
                    created_by=created_by,
                )
    except StockError as e:
        raise SalesError(str(e)) from e


def _apply_reserve(
    db: Session,
    *,
    vendor_id: int,
    details: list[SaleOrderDetail],
) -> None:
    try:
        for d in details:
            reserve_stock(
                db,
                vendor_id=vendor_id,
                item_id=d.item_id,
                location_id=d.location_id,
                quantity=int(d.quantity),
            )
    except StockError as e:
        raise SalesError(str(e)) from e


def create_sale_order(
    db: Session,
    *,
    vendor_id: int,
    data: dict[str, Any],
    created_by: str | None,
    user_id: int | None = None,
    stock_mode: str = "deduct",
) -> SaleOrder:
    items = data.get("items") or []
    if not items:
        raise SalesError("At least one line item required")

    customer_id = data.get("customer_id")
    if customer_id:
        c = db.get(Customer, customer_id)
        if not c or c.vendor_id != vendor_id:
            raise SalesError("Customer not found")

    status = (data.get("status") or "DRAFT").upper()
    if status not in SO_STATUSES:
        raise SalesError(f"Invalid status: {status}")
    if status in ("CANCELLED", "RETURNED"):
        raise SalesError("Cannot create order directly as CANCELLED/RETURNED")

    default_loc = _default_location_id(db, vendor_id)
    item_map: dict[int, Item] = {}
    for line in items:
        item_id = int(line["item_id"])
        item = db.get(Item, item_id)
        if not item or item.vendor_id != vendor_id:
            raise SalesError(f"Item {item_id} not found")
        item_map[item_id] = item
        loc_id = int(line.get("location_id") or default_loc)
        loc = db.get(Location, loc_id)
        if not loc or loc.vendor_id != vendor_id:
            raise SalesError(f"Location {loc_id} not found")
        line["location_id"] = loc_id
        if line.get("unit_price") is None:
            line["unit_price"] = float(item.sale_price)

    place_state = data.get("shipping_state")
    vendor_state = _vendor_state(db, vendor_id)
    item_ids = [int(x["item_id"]) for x in items]
    agg = aggregate_sale_lines(
        items,
        _gst_meta(db, vendor_id, item_ids),
        vendor_state=vendor_state,
        place_state=place_state,
    )
    shipping = round_money(float(data.get("shipping_charge") or 0))
    handling = round_money(float(data.get("handling_charge") or 0))
    total_value = round_money(agg["sum_net"] + shipping + handling)

    placed_for = data.get("placed_for_customer_id") or customer_id
    ordered_by = data.get("ordered_by_party_id")
    so = SaleOrder(
        vendor_id=vendor_id,
        order_code=data["order_code"],
        order_date=data["order_date"],
        customer_id=customer_id,
        placed_for_customer_id=placed_for,
        ordered_by_party_id=ordered_by,
        sales_channel=data.get("sales_channel") or "COUNTER",
        order_type=data.get("order_type") or "SALE",
        status=status,
        payment_status=(data.get("payment_status") or "UNPAID").upper(),
        fulfillment_status=(data.get("fulfillment_status") or "UNFULFILLED").upper(),
        total_gross_amount=agg["sum_gross"],
        total_discount_amount=agg["sum_discount"],
        total_net_amount=agg["sum_net"],
        total_tax_amount=agg["sum_tax"],
        shipping_charge=shipping,
        handling_charge=handling,
        total_order_value=total_value,
        shipping_street=data.get("shipping_street"),
        shipping_city=data.get("shipping_city"),
        shipping_state=place_state,
        shipping_zip=data.get("shipping_zip"),
        shipping_phone=data.get("shipping_phone"),
        shipping_name=data.get("shipping_name"),
        billing_street=data.get("billing_street"),
        billing_city=data.get("billing_city"),
        billing_state=data.get("billing_state"),
        billing_zip=data.get("billing_zip"),
        invoice_number=data.get("invoice_number"),
        invoice_date=data.get("invoice_date"),
        offer_code=data.get("offer_code"),
        payment_method=data.get("payment_method"),
        razorpay_order_id=data.get("razorpay_order_id"),
        razorpay_payment_id=data.get("razorpay_payment_id"),
        placed_by_user_id=user_id,
        created_by=created_by,
    )
    db.add(so)
    db.flush()

    # Map original line trade prices by item_id (first match)
    trade_by_item: dict[int, float | None] = {}
    for raw in items:
        iid = int(raw["item_id"])
        if "trade_unit_price" in raw and raw["trade_unit_price"] is not None:
            trade_by_item[iid] = round_money(float(raw["trade_unit_price"]))

    detail_rows: list[SaleOrderDetail] = []
    for line in agg["lines"]:
        item = item_map[int(line["item_id"])]
        trade = trade_by_item.get(int(line["item_id"]))
        unit = float(line["unit_price"])
        margin = None
        if trade is not None:
            margin = round_money((unit - trade) * int(line["quantity"]))
        d = SaleOrderDetail(
            vendor_id=vendor_id,
            sale_order_id=so.id,
            item_id=int(line["item_id"]),
            location_id=int(line["location_id"]),
            item_code=item.code,
            item_name=item.name,
            quantity=int(line["quantity"]),
            unit_price=line["unit_price"],
            trade_unit_price=trade,
            margin_amount=margin,
            line_gross_total=line["line_gross_total"],
            discount_percentage=line["discount_percentage"],
            discount_amount=line["discount_amount"],
            net_line_total=line["net_line_total"],
            gst_rate=line["gst_rate"],
            taxable_amount=line["taxable_amount"],
            gst_amount=line["gst_amount"],
            cgst_amount=line["cgst_amount"],
            sgst_amount=line["sgst_amount"],
            igst_amount=line["igst_amount"],
        )
        db.add(d)
        detail_rows.append(d)
    db.flush()

    if status in STOCKED_STATUSES:
        mode = (stock_mode or "deduct").lower()
        if mode == "reserve":
            _apply_reserve(db, vendor_id=vendor_id, details=detail_rows)
        elif mode == "deduct":
            _apply_sale_stock(
                db,
                vendor_id=vendor_id,
                so=so,
                details=detail_rows,
                reason="SO_SALE",
                created_by=created_by,
                deduct=True,
            )
        elif mode != "none":
            raise SalesError(f"Invalid stock_mode: {stock_mode}")

    _record_status(
        db,
        vendor_id=vendor_id,
        order_id=so.id,
        from_status=None,
        to_status=status,
        created_by=created_by,
    )
    db.flush()
    return so


def confirm_sale_order(
    db: Session,
    *,
    vendor_id: int,
    so_id: int,
    created_by: str | None,
) -> SaleOrder:
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        raise SalesError("Sale order not found")
    if so.status != "DRAFT":
        raise SalesError(f"Only DRAFT can be confirmed (current: {so.status})")

    details = list(
        db.scalars(
            select(SaleOrderDetail).where(
                SaleOrderDetail.sale_order_id == so_id,
                SaleOrderDetail.vendor_id == vendor_id,
            )
        ).all()
    )
    _apply_sale_stock(
        db,
        vendor_id=vendor_id,
        so=so,
        details=details,
        reason="SO_SALE",
        created_by=created_by,
        deduct=True,
    )
    old = so.status
    so.status = "CONFIRMED"
    _record_status(
        db,
        vendor_id=vendor_id,
        order_id=so.id,
        from_status=old,
        to_status="CONFIRMED",
        created_by=created_by,
    )
    db.flush()
    return so


def cancel_sale_order(
    db: Session,
    *,
    vendor_id: int,
    so_id: int,
    created_by: str | None,
    reason: str | None = None,
) -> SaleOrder:
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        raise SalesError("Sale order not found")
    if so.status == "CANCELLED":
        raise SalesError("Already cancelled")
    if so.status == "RETURNED":
        raise SalesError("Cannot cancel a returned order")

    details = list(
        db.scalars(
            select(SaleOrderDetail).where(
                SaleOrderDetail.sale_order_id == so_id,
                SaleOrderDetail.vendor_id == vendor_id,
            )
        ).all()
    )
    if so.status in STOCKED_STATUSES:
        # Unpaid Razorpay holds use reservation; paid/COD already deducted
        if so.payment_status == "UNPAID" and so.razorpay_order_id and not so.razorpay_payment_id:
            try:
                for d in details:
                    release_reservation(
                        db,
                        vendor_id=vendor_id,
                        item_id=d.item_id,
                        location_id=d.location_id,
                        quantity=int(d.quantity),
                    )
            except StockError as e:
                raise SalesError(str(e)) from e
        else:
            _apply_sale_stock(
                db,
                vendor_id=vendor_id,
                so=so,
                details=details,
                reason="SO_CANCEL",
                created_by=created_by,
                deduct=False,
            )
    old = so.status
    so.status = "CANCELLED"
    so.cancelled_at = datetime.now(timezone.utc)
    so.cancel_reason = reason
    _record_status(
        db,
        vendor_id=vendor_id,
        order_id=so.id,
        from_status=old,
        to_status="CANCELLED",
        created_by=created_by,
        note=reason,
    )
    db.flush()
    return so


def mark_sale_order_paid(
    db: Session,
    *,
    vendor_id: int,
    order_code: str,
    razorpay_order_id: str | None,
    razorpay_payment_id: str,
    payment_method: str = "UPI",
    created_by: str | None = None,
) -> SaleOrder:
    so = db.scalar(
        select(SaleOrder).where(SaleOrder.vendor_id == vendor_id, SaleOrder.order_code == order_code)
    )
    if not so:
        raise SalesError("Sale order not found")
    if so.payment_status == "PAID" and so.razorpay_payment_id == razorpay_payment_id:
        return so  # idempotent
    if so.payment_status == "PAID":
        raise SalesError("Order already paid")
    if so.status == "CANCELLED":
        raise SalesError("Cannot pay a cancelled order")
    if razorpay_order_id and so.razorpay_order_id and so.razorpay_order_id != razorpay_order_id:
        raise SalesError("Razorpay order mismatch")

    details = list(
        db.scalars(
            select(SaleOrderDetail).where(
                SaleOrderDetail.sale_order_id == so.id,
                SaleOrderDetail.vendor_id == vendor_id,
            )
        ).all()
    )
    # Consume reservation if this was a held Razorpay order
    if so.razorpay_order_id and so.payment_status == "UNPAID":
        try:
            for d in details:
                consume_reservation(
                    db,
                    vendor_id=vendor_id,
                    item_id=d.item_id,
                    location_id=d.location_id,
                    quantity=int(d.quantity),
                    reference_type="SALE_ORDER",
                    reference_id=so.id,
                    created_by=created_by,
                )
        except StockError as e:
            raise SalesError(str(e)) from e

    so.payment_status = "PAID"
    so.payment_method = payment_method
    so.razorpay_payment_id = razorpay_payment_id
    if razorpay_order_id:
        so.razorpay_order_id = razorpay_order_id
    db.flush()
    return so


def ship_sale_order(
    db: Session,
    *,
    vendor_id: int,
    so_id: int,
    courier: str,
    tracking_number: str,
    created_by: str | None,
    shipped_at: datetime | None = None,
) -> SaleOrder:
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        raise SalesError("Sale order not found")
    if so.status == "CANCELLED":
        raise SalesError("Cannot ship a cancelled order")

    vendor = db.get(Vendor, vendor_id)
    settings = vendor.settings if vendor and isinstance(vendor.settings, dict) else {}
    try:
        code = normalize_courier(courier, settings)
    except ValueError as e:
        raise SalesError(str(e)) from e
    tn = (tracking_number or "").strip()
    if not tn:
        raise SalesError("tracking_number is required")

    so.courier = code
    so.tracking_number = tn
    so.shipped_at = shipped_at or datetime.now(timezone.utc)
    so.fulfillment_status = "SHIPPED"
    _record_status(
        db,
        vendor_id=vendor_id,
        order_id=so.id,
        from_status=so.status,
        to_status="SHIPPED",
        created_by=created_by,
        note=f"{courier_label(code)} · {tn}",
    )
    db.flush()
    return so


def create_sale_return(
    db: Session,
    *,
    vendor_id: int,
    data: dict[str, Any],
    created_by: str | None,
) -> SaleReturn:
    items = data.get("items") or []
    if not items:
        raise SalesError("Return lines required")

    so_id = data.get("sale_order_id")
    if so_id:
        so = db.get(SaleOrder, so_id)
        if not so or so.vendor_id != vendor_id:
            raise SalesError("Sale order not found")

    ret = SaleReturn(
        vendor_id=vendor_id,
        sale_order_id=so_id,
        return_code=data["return_code"],
        return_date=data.get("return_date") or date.today(),
        status="POSTED",
        notes=data.get("notes"),
        created_by=created_by,
    )
    db.add(ret)
    db.flush()

    default_loc = _default_location_id(db, vendor_id)
    try:
        for line in items:
            item_id = int(line["item_id"])
            loc_id = int(line.get("location_id") or default_loc)
            qty = int(line["quantity"])
            item = db.get(Item, item_id)
            if not item or item.vendor_id != vendor_id:
                raise SalesError(f"Item {item_id} not found")
            db.add(
                SaleReturnDetail(
                    vendor_id=vendor_id,
                    sale_return_id=ret.id,
                    item_id=item_id,
                    location_id=loc_id,
                    quantity=qty,
                )
            )
            add_stock(
                db,
                vendor_id=vendor_id,
                item_id=item_id,
                location_id=loc_id,
                quantity=qty,
                reason="SO_RETURN",
                reference_type="SALE_RETURN",
                reference_id=ret.id,
                created_by=created_by,
            )
    except StockError as e:
        raise SalesError(str(e)) from e

    if so_id:
        so = db.get(SaleOrder, so_id)
        if so and so.status == "CONFIRMED":
            old = so.status
            so.status = "RETURNED"
            _record_status(
                db,
                vendor_id=vendor_id,
                order_id=so.id,
                from_status=old,
                to_status="RETURNED",
                created_by=created_by,
                note=f"Return {ret.return_code}",
            )
    db.flush()
    return ret
