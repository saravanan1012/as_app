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
from app.models import GoodsReceipt, GoodsReceiptLine, PurchaseOrder, PurchaseOrderDetail
from app.models.orders import PurchaseReturn, PurchaseReturnDetail
from app.services.audit import write_audit
from app.services.purchase_orders import PurchaseError, create_purchase_order, create_purchase_return, receive_grn

router = APIRouter(tags=["purchase"])

PO_FIELDS = [
    "id", "vendor_id", "order_code", "order_date", "supplier_id",
    "total_gross_amount", "total_discount_amount", "total_net_amount", "total_tax_amount",
    "freight_cost", "packing_cost", "total_purchase_cost",
    "status", "payment_status", "supplier_invoice_number", "supplier_invoice_date",
    "expected_delivery_date", "created_by", "created_at",
]
DETAIL_FIELDS = [
    "id", "item_id", "location_id", "quantity_ordered", "quantity_received",
    "cost_price", "line_gross_total", "discount_percentage", "discount_amount",
    "net_line_total", "gst_rate", "taxable_amount", "gst_amount",
]


class PoLineIn(BaseModel):
    item_id: int
    location_id: int | None = None
    quantity_ordered: int = Field(gt=0)
    cost_price: float
    discount_percentage: float = 0
    discount_amount: float = 0


class PoIn(BaseModel):
    order_code: str = Field(min_length=1, max_length=50)
    order_date: date
    supplier_id: int
    items: list[PoLineIn]
    freight_cost: float = 0
    packing_cost: float = 0
    status: str = "ORDERED"
    payment_status: str = "UNPAID"
    supplier_invoice_number: str | None = None
    supplier_invoice_date: date | None = None
    expected_delivery_date: date | None = None


class ReceiveLineIn(BaseModel):
    purchase_order_detail_id: int | None = None
    item_id: int | None = None
    location_id: int | None = None
    quantity: int = Field(gt=0)


class ReceiveIn(BaseModel):
    receipt_code: str = Field(min_length=1, max_length=50)
    notes: str | None = None
    lines: list[ReceiveLineIn]


class PrLineIn(BaseModel):
    item_id: int
    location_id: int | None = None
    quantity: int = Field(gt=0)


class PrIn(BaseModel):
    return_code: str
    return_date: date | None = None
    purchase_order_id: int | None = None
    notes: str | None = None
    items: list[PrLineIn]


def _po_payload(db: Session, po: PurchaseOrder) -> dict:
    details = db.scalars(
        select(PurchaseOrderDetail).where(PurchaseOrderDetail.purchase_order_id == po.id)
    ).all()
    return {**row(po, PO_FIELDS), "items": [row(d, DETAIL_FIELDS) for d in details]}


@router.get("/purchase-orders")
def list_pos(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status: str | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(PurchaseOrder).where(PurchaseOrder.vendor_id == vendor_id)
    if status:
        q = q.where(PurchaseOrder.status == status.upper())
    rows = db.scalars(q.order_by(PurchaseOrder.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success("Purchase orders fetched", {"data": [row(p, PO_FIELDS) for p in rows]})


@router.get("/purchase-orders/{po_id}")
def get_po(
    po_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    po = db.get(PurchaseOrder, po_id)
    if not po or po.vendor_id != vendor_id:
        return error("Purchase order not found", status_code=404)
    return success("Purchase order", _po_payload(db, po))


@router.post("/purchase-orders")
def create_po(
    body: PoIn,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        po = create_purchase_order(
            db,
            vendor_id=vendor_id,
            data=body.model_dump(),
            created_by=user.email,
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CREATE",
            entity_type="PURCHASE_ORDER",
            entity_id=po.id,
            new_data={"order_code": po.order_code, "status": po.status},
        )
        db.commit()
        db.refresh(po)
    except PurchaseError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Created", _po_payload(db, po), status_code=201)


@router.post("/purchase-orders/{po_id}/receive")
def receive_po(
    po_id: int,
    body: ReceiveIn,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        grn = receive_grn(
            db,
            vendor_id=vendor_id,
            po_id=po_id,
            lines=[ln.model_dump() for ln in body.lines],
            receipt_code=body.receipt_code,
            received_by=user.email,
            notes=body.notes,
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="RECEIVE",
            entity_type="GOODS_RECEIPT",
            entity_id=grn.id,
            new_data={"purchase_order_id": po_id, "receipt_code": body.receipt_code},
        )
        db.commit()
        db.refresh(grn)
    except PurchaseError as e:
        db.rollback()
        return error(str(e), status_code=400)

    grn_lines = db.scalars(
        select(GoodsReceiptLine).where(GoodsReceiptLine.goods_receipt_id == grn.id)
    ).all()
    po = db.get(PurchaseOrder, po_id)
    return success(
        "Received",
        {
            "grn": row(grn, ["id", "receipt_code", "purchase_order_id", "received_at", "status"]),
            "lines": [row(l, ["id", "item_id", "location_id", "quantity", "purchase_order_detail_id"]) for l in grn_lines],
            "purchase_order": _po_payload(db, po) if po else None,
        },
        status_code=201,
    )


@router.get("/goods-receipts")
def list_grns(
    purchase_order_id: int | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(GoodsReceipt).where(GoodsReceipt.vendor_id == vendor_id)
    if purchase_order_id:
        q = q.where(GoodsReceipt.purchase_order_id == purchase_order_id)
    rows = db.scalars(q.order_by(GoodsReceipt.id.desc()).limit(100)).all()
    return success(
        "GRNs fetched",
        [row(g, ["id", "receipt_code", "purchase_order_id", "received_at", "received_by", "status", "notes"]) for g in rows],
    )


@router.post("/purchase-returns")
def create_pr(
    body: PrIn,
    ctx: tuple[AuthUser, int] = Depends(perm("purchase.orders.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        ret = create_purchase_return(
            db, vendor_id=vendor_id, data=body.model_dump(), created_by=user.email
        )
        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CREATE",
            entity_type="PURCHASE_RETURN",
            entity_id=ret.id,
            new_data={"return_code": ret.return_code},
        )
        db.commit()
        db.refresh(ret)
    except PurchaseError as e:
        db.rollback()
        return error(str(e), status_code=400)
    details = db.scalars(
        select(PurchaseReturnDetail).where(PurchaseReturnDetail.purchase_return_id == ret.id)
    ).all()
    return success(
        "Created",
        {
            **row(ret, ["id", "return_code", "return_date", "purchase_order_id", "status"]),
            "items": [row(d, ["id", "item_id", "location_id", "quantity"]) for d in details],
        },
        status_code=201,
    )
