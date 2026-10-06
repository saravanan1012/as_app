from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models.orders import OrderStatusEvent, SaleOrder, SaleOrderDetail, SaleReturn, SaleReturnDetail
from app.services.audit import write_audit
from app.services.pricing import courier_label
from app.services.sales_orders import (
    SalesError,
    cancel_sale_order,
    confirm_sale_order,
    create_sale_order,
    create_sale_return,
    ship_sale_order,
)

router = APIRouter(tags=["sales"])

SO_FIELDS = [
    "id", "vendor_id", "order_code", "order_date", "customer_id",
    "placed_for_customer_id", "ordered_by_party_id", "sales_channel",
    "order_type", "status", "payment_status", "fulfillment_status",
    "total_gross_amount", "total_discount_amount", "total_net_amount", "total_tax_amount",
    "shipping_charge", "handling_charge", "total_order_value",
    "shipping_street", "shipping_city", "shipping_state", "shipping_zip",
    "shipping_phone", "shipping_name", "invoice_number", "invoice_date",
    "offer_code", "payment_method", "courier", "tracking_number", "shipped_at",
    "cancelled_at", "cancel_reason", "created_by", "created_at",
]
DETAIL_FIELDS = [
    "id", "item_id", "location_id", "item_code", "item_name", "quantity", "unit_price",
    "trade_unit_price", "margin_amount",
    "line_gross_total", "discount_percentage", "discount_amount", "net_line_total",
    "gst_rate", "taxable_amount", "gst_amount", "cgst_amount", "sgst_amount", "igst_amount",
]


class SoLineIn(BaseModel):
    item_id: int
    location_id: int | None = None
    quantity: int = Field(gt=0)
    unit_price: float | None = None
    discount_percentage: float = 0
    discount_amount: float = 0


class SoIn(BaseModel):
    order_code: str = Field(min_length=1, max_length=50)
    order_date: date
    customer_id: int | None = None
    items: list[SoLineIn]
    sales_channel: str = "COUNTER"
    status: str = "DRAFT"
    payment_status: str = "UNPAID"
    fulfillment_status: str = "UNFULFILLED"
    shipping_charge: float = 0
    handling_charge: float = 0
    shipping_street: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_zip: str | None = None
    shipping_phone: str | None = None
    shipping_name: str | None = None
    billing_street: str | None = None
    billing_city: str | None = None
    billing_state: str | None = None
    billing_zip: str | None = None
    invoice_number: str | None = None
    invoice_date: date | None = None
    offer_code: str | None = None
    payment_method: str | None = None


class CancelIn(BaseModel):
    reason: str | None = None


class SrLineIn(BaseModel):
    item_id: int
    location_id: int | None = None
    quantity: int = Field(gt=0)


class SrIn(BaseModel):
    return_code: str
    return_date: date | None = None
    sale_order_id: int | None = None
    notes: str | None = None
    items: list[SrLineIn]


def _so_payload(db: Session, so: SaleOrder) -> dict:
    details = db.scalars(
        select(SaleOrderDetail).where(SaleOrderDetail.sale_order_id == so.id)
    ).all()
    payload = {**row(so, SO_FIELDS), "items": [row(d, DETAIL_FIELDS) for d in details]}
    payload["courier_label"] = courier_label(so.courier)
    return payload


class ShipmentIn(BaseModel):
    courier: str
    tracking_number: str = Field(min_length=1, max_length=100)


@router.get("/sale-orders")
def list_sos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(SaleOrder).where(SaleOrder.vendor_id == vendor_id)
    if status:
        q = q.where(SaleOrder.status == status.upper())
    rows = db.scalars(q.order_by(SaleOrder.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success("Sale orders fetched", {"data": [row(s, SO_FIELDS) for s in rows]})


@router.get("/sale-orders/{so_id}")
def get_so(
    so_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        return error("Sale order not found", status_code=404)
    return success("Sale order", _so_payload(db, so))


@router.post("/sale-orders")
def create_so(
    body: SoIn,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        so = create_sale_order(
            db,
            vendor_id=vendor_id,
            data=body.model_dump(),
            created_by=user.email,
            user_id=user.id,
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CREATE",
            entity_type="SALE_ORDER",
            entity_id=so.id,
            new_data={"order_code": so.order_code, "status": so.status},
        )
        db.commit()
        db.refresh(so)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Created", _so_payload(db, so), status_code=201)


@router.post("/sale-orders/{so_id}/confirm")
def confirm_so(
    so_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        so = confirm_sale_order(db, vendor_id=vendor_id, so_id=so_id, created_by=user.email)
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CONFIRM",
            entity_type="SALE_ORDER",
            entity_id=so.id,
        )
        db.commit()
        db.refresh(so)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Confirmed", _so_payload(db, so))


@router.patch("/sale-orders/{so_id}/shipment")
def ship_so(
    so_id: int,
    body: ShipmentIn,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        so = ship_sale_order(
            db,
            vendor_id=vendor_id,
            so_id=so_id,
            courier=body.courier,
            tracking_number=body.tracking_number,
            created_by=user.email,
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="SHIP",
            entity_type="SALE_ORDER",
            entity_id=so.id,
            new_data={"courier": so.courier, "tracking_number": so.tracking_number},
        )
        db.commit()
        db.refresh(so)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Shipped", _so_payload(db, so))


@router.post("/sale-orders/{so_id}/cancel")
def cancel_so(
    so_id: int,
    body: CancelIn | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        so = cancel_sale_order(
            db,
            vendor_id=vendor_id,
            so_id=so_id,
            created_by=user.email,
            reason=(body.reason if body else None),
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CANCEL",
            entity_type="SALE_ORDER",
            entity_id=so.id,
        )
        db.commit()
        db.refresh(so)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Cancelled", _so_payload(db, so))


@router.get("/sale-orders/{so_id}/events")
def so_events(
    so_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        return error("Sale order not found", status_code=404)
    events = db.scalars(
        select(OrderStatusEvent)
        .where(
            OrderStatusEvent.vendor_id == vendor_id,
            OrderStatusEvent.order_type == "SALE",
            OrderStatusEvent.order_id == so_id,
        )
        .order_by(OrderStatusEvent.id)
    ).all()
    return success(
        "Events",
        [row(e, ["id", "from_status", "to_status", "note", "created_by", "created_at"]) for e in events],
    )


@router.post("/sale-returns")
def create_sr(
    body: SrIn,
    ctx: tuple[AuthUser, int] = Depends(perm("sales.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        ret = create_sale_return(
            db, vendor_id=vendor_id, data=body.model_dump(), created_by=user.email
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CREATE",
            entity_type="SALE_RETURN",
            entity_id=ret.id,
            new_data={"return_code": ret.return_code},
        )
        db.commit()
        db.refresh(ret)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    details = db.scalars(
        select(SaleReturnDetail).where(SaleReturnDetail.sale_return_id == ret.id)
    ).all()
    return success(
        "Created",
        {
            **row(ret, ["id", "return_code", "return_date", "sale_order_id", "status"]),
            "items": [row(d, ["id", "item_id", "location_id", "quantity"]) for d in details],
        },
        status_code=201,
    )
