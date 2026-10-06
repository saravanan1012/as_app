"""Purchase orders + GRN receive + purchase returns."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.gst import aggregate_purchase_lines, round_money
from app.models import (
    GoodsReceipt,
    GoodsReceiptLine,
    Item,
    Location,
    PurchaseOrder,
    PurchaseOrderDetail,
    PurchaseReturn,
    PurchaseReturnDetail,
    Supplier,
    TaxCategory,
    Vendor,
)
from app.models.orders import OrderStatusEvent
from app.services.stock_ledger import StockError, add_stock, deduct_stock

PO_STATUSES = frozenset(
    {"DRAFT", "ORDERED", "PARTIAL_RECEIVED", "RECEIVED", "CANCELLED", "RETURNED"}
)


class PurchaseError(Exception):
    pass


def _default_location_id(db: Session, vendor_id: int) -> int:
    v = db.get(Vendor, vendor_id)
    if v and v.default_location_id:
        return v.default_location_id
    loc = db.scalar(select(Location).where(Location.vendor_id == vendor_id).order_by(Location.id))
    if not loc:
        raise PurchaseError("No location for vendor")
    return loc.id


def _gst_by_item(db: Session, vendor_id: int, item_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not item_ids:
        return {}
    rows = db.execute(
        select(Item.id, TaxCategory.gst_rate)
        .outerjoin(TaxCategory, Item.tax_category_id == TaxCategory.id)
        .where(Item.vendor_id == vendor_id, Item.id.in_(item_ids))
    ).all()
    return {int(r.id): {"rate": float(r.gst_rate or 0)} for r in rows}


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
            order_type="PURCHASE",
            order_id=order_id,
            from_status=from_status,
            to_status=to_status,
            note=note,
            created_by=created_by,
        )
    )


def create_purchase_order(
    db: Session,
    *,
    vendor_id: int,
    data: dict[str, Any],
    created_by: str | None,
) -> PurchaseOrder:
    supplier = db.get(Supplier, data["supplier_id"])
    if not supplier or supplier.vendor_id != vendor_id:
        raise PurchaseError("Supplier not found")

    items = data.get("items") or []
    if not items:
        raise PurchaseError("At least one line item required")

    default_loc = _default_location_id(db, vendor_id)
    for line in items:
        loc_id = int(line.get("location_id") or default_loc)
        item = db.get(Item, int(line["item_id"]))
        if not item or item.vendor_id != vendor_id:
            raise PurchaseError(f"Item {line['item_id']} not found")
        loc = db.get(Location, loc_id)
        if not loc or loc.vendor_id != vendor_id:
            raise PurchaseError(f"Location {loc_id} not found")
        line["location_id"] = loc_id

    item_ids = [int(x["item_id"]) for x in items]
    agg = aggregate_purchase_lines(items, _gst_by_item(db, vendor_id, item_ids))
    freight = round_money(float(data.get("freight_cost") or 0))
    packing = round_money(float(data.get("packing_cost") or 0))
    total_cost = round_money(agg["sum_net"] + freight + packing)

    status = (data.get("status") or "DRAFT").upper().replace(" ", "_")
    if status not in PO_STATUSES:
        raise PurchaseError(f"Invalid status: {status}")
    # Creating with RECEIVED via GRN only
    if status in ("PARTIAL_RECEIVED", "RECEIVED", "RETURNED"):
        raise PurchaseError("Use GRN receive / return endpoints for that status")

    po = PurchaseOrder(
        vendor_id=vendor_id,
        order_code=data["order_code"],
        order_date=data["order_date"],
        supplier_id=data["supplier_id"],
        total_gross_amount=agg["sum_gross"],
        total_discount_amount=agg["sum_discount"],
        total_net_amount=agg["sum_net"],
        total_tax_amount=agg["sum_tax"],
        freight_cost=freight,
        packing_cost=packing,
        total_purchase_cost=total_cost,
        status=status,
        payment_status=(data.get("payment_status") or "UNPAID").upper(),
        supplier_invoice_number=data.get("supplier_invoice_number"),
        supplier_invoice_date=data.get("supplier_invoice_date"),
        expected_delivery_date=data.get("expected_delivery_date"),
        created_by=created_by,
    )
    db.add(po)
    db.flush()

    for line in agg["lines"]:
        db.add(
            PurchaseOrderDetail(
                vendor_id=vendor_id,
                purchase_order_id=po.id,
                item_id=int(line["item_id"]),
                location_id=int(line["location_id"]),
                quantity_ordered=int(line["quantity_ordered"]),
                quantity_received=0,
                cost_price=line["cost_price"],
                line_gross_total=line["line_gross_total"],
                discount_percentage=line["discount_percentage"],
                discount_amount=line["discount_amount"],
                net_line_total=line["net_line_total"],
                gst_rate=line["gst_rate"],
                taxable_amount=line["taxable_amount"],
                gst_amount=line["gst_amount"],
            )
        )

    _record_status(
        db,
        vendor_id=vendor_id,
        order_id=po.id,
        from_status=None,
        to_status=status,
        created_by=created_by,
    )
    db.flush()
    return po


def receive_grn(
    db: Session,
    *,
    vendor_id: int,
    po_id: int,
    lines: list[dict[str, Any]],
    receipt_code: str,
    received_by: str | None,
    notes: str | None = None,
) -> GoodsReceipt:
    po = db.get(PurchaseOrder, po_id)
    if not po or po.vendor_id != vendor_id:
        raise PurchaseError("Purchase order not found")
    if po.status in ("CANCELLED", "RETURNED"):
        raise PurchaseError(f"Cannot receive against status {po.status}")
    if not lines:
        raise PurchaseError("Receive lines required")

    details = {
        d.id: d
        for d in db.scalars(
            select(PurchaseOrderDetail).where(
                PurchaseOrderDetail.purchase_order_id == po_id,
                PurchaseOrderDetail.vendor_id == vendor_id,
            )
        ).all()
    }

    grn = GoodsReceipt(
        vendor_id=vendor_id,
        purchase_order_id=po_id,
        receipt_code=receipt_code,
        received_at=datetime.now(timezone.utc),
        received_by=received_by,
        notes=notes,
        status="POSTED",
    )
    db.add(grn)
    db.flush()

    try:
        for line in lines:
            detail_id = line.get("purchase_order_detail_id")
            detail: PurchaseOrderDetail | None = None
            if detail_id:
                detail = details.get(int(detail_id))
            else:
                item_id = int(line["item_id"])
                loc_id = int(line.get("location_id") or 0)
                for d in details.values():
                    if d.item_id == item_id and (not loc_id or d.location_id == loc_id):
                        detail = d
                        break
            if not detail:
                raise PurchaseError(f"PO line not found for receive: {line}")

            qty = int(line["quantity"])
            if qty <= 0:
                raise PurchaseError("Receive quantity must be positive")
            new_recv = int(detail.quantity_received) + qty
            if new_recv > int(detail.quantity_ordered):
                raise PurchaseError(
                    f"Cannot receive more than ordered for item {detail.item_id}"
                )
            detail.quantity_received = new_recv
            loc_id = int(line.get("location_id") or detail.location_id)

            db.add(
                GoodsReceiptLine(
                    vendor_id=vendor_id,
                    goods_receipt_id=grn.id,
                    purchase_order_detail_id=detail.id,
                    item_id=detail.item_id,
                    location_id=loc_id,
                    quantity=qty,
                )
            )
            add_stock(
                db,
                vendor_id=vendor_id,
                item_id=detail.item_id,
                location_id=loc_id,
                quantity=qty,
                reason="PO_RECEIVE",
                reference_type="GOODS_RECEIPT",
                reference_id=grn.id,
                created_by=received_by,
            )
    except StockError as e:
        raise PurchaseError(str(e)) from e

    # Recompute PO status from all details
    all_details = list(details.values())
    ordered = sum(int(d.quantity_ordered) for d in all_details)
    received = sum(int(d.quantity_received) for d in all_details)
    old_status = po.status
    if received <= 0:
        new_status = old_status if old_status in ("DRAFT", "ORDERED") else "ORDERED"
    elif received < ordered:
        new_status = "PARTIAL_RECEIVED"
    else:
        new_status = "RECEIVED"
    if new_status != old_status:
        po.status = new_status
        _record_status(
            db,
            vendor_id=vendor_id,
            order_id=po.id,
            from_status=old_status,
            to_status=new_status,
            created_by=received_by,
            note=f"GRN {receipt_code}",
        )
    db.flush()
    return grn


def create_purchase_return(
    db: Session,
    *,
    vendor_id: int,
    data: dict[str, Any],
    created_by: str | None,
) -> PurchaseReturn:
    items = data.get("items") or []
    if not items:
        raise PurchaseError("Return lines required")

    po_id = data.get("purchase_order_id")
    if po_id:
        po = db.get(PurchaseOrder, po_id)
        if not po or po.vendor_id != vendor_id:
            raise PurchaseError("Purchase order not found")

    ret = PurchaseReturn(
        vendor_id=vendor_id,
        purchase_order_id=po_id,
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
                raise PurchaseError(f"Item {item_id} not found")
            db.add(
                PurchaseReturnDetail(
                    vendor_id=vendor_id,
                    purchase_return_id=ret.id,
                    item_id=item_id,
                    location_id=loc_id,
                    quantity=qty,
                )
            )
            deduct_stock(
                db,
                vendor_id=vendor_id,
                item_id=item_id,
                location_id=loc_id,
                quantity=qty,
                reason="PO_RETURN",
                reference_type="PURCHASE_RETURN",
                reference_id=ret.id,
                created_by=created_by,
            )
    except StockError as e:
        raise PurchaseError(str(e)) from e

    if po_id:
        po = db.get(PurchaseOrder, po_id)
        if po:
            old = po.status
            po.status = "RETURNED"
            _record_status(
                db,
                vendor_id=vendor_id,
                order_id=po.id,
                from_status=old,
                to_status="RETURNED",
                created_by=created_by,
                note=f"Return {ret.return_code}",
            )
    db.flush()
    return ret
