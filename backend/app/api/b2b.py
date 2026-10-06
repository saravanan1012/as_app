"""B2B trade portal — Distributor / Dealer / Retailer."""

from __future__ import annotations

import time
import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser, get_current_user, require_permission
from app.api.serialize import row
from app.api.vendor_scope import require_vendor_id
from app.core.gst import aggregate_sale_lines, round_money
from app.core.responses import error, success
from app.db import get_db
from app.models import Customer, Item, SaleOrder, SaleOrderDetail, TaxCategory, Vendor
from app.services import parties as party_svc
from app.services.pricing import courier_label, resolve_item_prices, shipping_charge_for_qty
from app.services.sales_orders import SalesError, create_sale_order

router = APIRouter(prefix="/b2b", tags=["b2b"])

TRADE_ROLES = frozenset({"DISTRIBUTOR", "DEALER", "RETAILER"})

SO_FIELDS = [
    "id",
    "vendor_id",
    "order_code",
    "order_date",
    "customer_id",
    "placed_for_customer_id",
    "ordered_by_party_id",
    "sales_channel",
    "status",
    "payment_status",
    "fulfillment_status",
    "total_gross_amount",
    "total_discount_amount",
    "total_net_amount",
    "total_tax_amount",
    "shipping_charge",
    "handling_charge",
    "total_order_value",
    "invoice_number",
    "invoice_date",
    "courier",
    "tracking_number",
    "shipped_at",
    "created_at",
]
DETAIL_FIELDS = [
    "id",
    "item_id",
    "item_code",
    "item_name",
    "quantity",
    "unit_price",
    "trade_unit_price",
    "margin_amount",
    "line_gross_total",
    "discount_amount",
    "net_line_total",
    "gst_rate",
    "gst_amount",
    "cgst_amount",
    "sgst_amount",
    "igst_amount",
]


def _require_trade(
    user: AuthUser = Depends(require_permission("b2b.portal")),
    vendor_id: int = Depends(require_vendor_id),
    db: Session = Depends(get_db),
) -> tuple[AuthUser, int, Customer]:
    if user.role not in TRADE_ROLES:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Trade role required")
    party = party_svc.get_party_for_user(db, vendor_id, user.id)
    if not party:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="No party linked to this user")
    return user, vendor_id, party


def _gst_meta(db: Session, vendor_id: int, item_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not item_ids:
        return {}
    rows = db.execute(
        select(Item.id, Item.sale_price_includes_gst, TaxCategory.gst_rate)
        .outerjoin(TaxCategory, Item.tax_category_id == TaxCategory.id)
        .where(Item.vendor_id == vendor_id, Item.id.in_(item_ids))
    ).all()
    return {
        int(r.id): {"rate": float(r.gst_rate or 0), "includes": bool(r.sale_price_includes_gst)}
        for r in rows
    }


def _so_payload(db: Session, so: SaleOrder) -> dict:
    details = db.scalars(
        select(SaleOrderDetail).where(SaleOrderDetail.sale_order_id == so.id)
    ).all()
    payload = {**row(so, SO_FIELDS), "items": [row(d, DETAIL_FIELDS) for d in details]}
    payload["courier_label"] = courier_label(so.courier)
    return payload


class LineIn(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)
    unit_price: float | None = None


class PreviewIn(BaseModel):
    customer_id: int
    items: list[LineIn]
    shipping_state: str | None = None


class OrderIn(BaseModel):
    customer_id: int
    items: list[LineIn]
    shipping_street: str | None = None
    shipping_city: str | None = None
    shipping_state: str | None = None
    shipping_zip: str | None = None
    shipping_phone: str | None = None
    shipping_name: str | None = None
    payment_status: str = "UNPAID"
    payment_method: str | None = "COD"
    status: str = "CONFIRMED"


@router.get("/me")
def b2b_me(ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade)):
    user, vendor_id, party = ctx
    return success(
        "OK",
        {
            "user_id": user.id,
            "email": user.email,
            "role": user.role,
            "vendor_id": vendor_id,
            "party": row(
                party,
                ["id", "name", "party_type", "parent_id", "phone", "email", "status"],
            ),
        },
    )


@router.get("/downline")
def downline(
    party_type: str | None = None,
    include_self: bool = True,
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    _, vendor_id, party = ctx
    ids = party_svc.list_descendant_ids(db, vendor_id, party.id)
    if include_self:
        ids = set(ids) | {party.id}
    if not ids:
        return success("Downline", {"data": []})
    q = select(Customer).where(Customer.vendor_id == vendor_id, Customer.id.in_(ids))
    if party_type:
        q = q.where(Customer.party_type == party_type.upper())
    rows = db.scalars(q.order_by(Customer.name)).all()
    return success(
        "Downline",
        {
            "data": [
                row(c, ["id", "name", "party_type", "parent_id", "phone", "email", "status"])
                for c in rows
            ]
        },
    )


@router.get("/catalog")
def catalog(
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    _, vendor_id, party = ctx
    items = db.scalars(
        select(Item).where(
            Item.vendor_id == vendor_id,
            Item.status == "ACTIVE",
            Item.is_sellable.is_(True),
        )
    ).all()
    data = []
    for it in items:
        prices = resolve_item_prices(
            db, vendor_id=vendor_id, item=it, party_type=party.party_type
        )
        data.append(
            {
                "id": it.id,
                "code": it.code,
                "name": it.name,
                "description": it.description,
                "is_online_sale": it.is_online_sale,
                "unit_of_measure": it.unit_of_measure,
                "msrp": prices["msrp"],
                "trade_unit_price": prices["trade_unit_price"],
                "suggested_sell": prices["suggested_sell"],
                "sale_price_includes_gst": it.sale_price_includes_gst,
                "primary_image": it.primary_image,
            }
        )
    return success("Catalog", {"data": data})


def _build_priced_lines(
    db: Session,
    *,
    vendor_id: int,
    actor: Customer,
    lines_in: list[LineIn],
    allow_below_trade: bool = False,
) -> tuple[list[dict[str, Any]], int]:
    out: list[dict[str, Any]] = []
    total_qty = 0
    for line in lines_in:
        item = db.get(Item, line.item_id)
        if not item or item.vendor_id != vendor_id or not item.is_sellable:
            raise ValueError(f"Item {line.item_id} not found")
        prices = resolve_item_prices(
            db, vendor_id=vendor_id, item=item, party_type=actor.party_type
        )
        trade = float(prices["trade_unit_price"])
        sell = float(line.unit_price) if line.unit_price is not None else float(prices["suggested_sell"])
        if not allow_below_trade and sell + 1e-9 < trade:
            raise ValueError(
                f"unit_price for {item.code} cannot be below trade price {trade}"
            )
        out.append(
            {
                "item_id": item.id,
                "quantity": int(line.quantity),
                "unit_price": round_money(sell),
                "trade_unit_price": trade,
                "discount_amount": 0,
                "discount_percentage": 0,
            }
        )
        total_qty += int(line.quantity)
    return out, total_qty


@router.post("/cart/preview")
def preview(
    body: PreviewIn,
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    _, vendor_id, actor = ctx
    try:
        party_svc.assert_in_downline(
            db, vendor_id=vendor_id, actor_party=actor, target_id=body.customer_id
        )
        lines, total_qty = _build_priced_lines(
            db, vendor_id=vendor_id, actor=actor, lines_in=body.items
        )
    except ValueError as e:
        return error(str(e), status_code=400)

    vendor = db.get(Vendor, vendor_id)
    settings = vendor.settings if vendor and isinstance(vendor.settings, dict) else {}
    vendor_state = None
    if vendor:
        vendor_state = vendor.state_code or (settings.get("tax") or {}).get("state_code")
    agg = aggregate_sale_lines(
        lines,
        _gst_meta(db, vendor_id, [int(x["item_id"]) for x in lines]),
        vendor_state=vendor_state,
        place_state=body.shipping_state,
    )
    ship = shipping_charge_for_qty(
        settings, total_qty=total_qty, subtotal=float(agg["sum_gross"])
    )
    total = round_money(float(agg["sum_net"]) + ship)
    return success(
        "Preview",
        {
            "lines": agg["lines"],
            "total_qty": total_qty,
            "subtotal": agg["sum_gross"],
            "tax": agg["sum_tax"],
            "shipping_charge": ship,
            "total_order_value": total,
        },
    )


@router.post("/orders")
def create_order(
    body: OrderIn,
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    user, vendor_id, actor = ctx
    from app.core.permissions import permission_implies

    if not permission_implies(user.permissions, "b2b.orders.write"):
        return error("Forbidden", status_code=403)
    try:
        buyer = party_svc.assert_in_downline(
            db, vendor_id=vendor_id, actor_party=actor, target_id=body.customer_id
        )
        lines, total_qty = _build_priced_lines(
            db, vendor_id=vendor_id, actor=actor, lines_in=body.items
        )
    except ValueError as e:
        return error(str(e), status_code=400)

    vendor = db.get(Vendor, vendor_id)
    settings = vendor.settings if vendor and isinstance(vendor.settings, dict) else {}
    subtotal = sum(float(x["unit_price"]) * int(x["quantity"]) for x in lines)
    ship = shipping_charge_for_qty(settings, total_qty=total_qty, subtotal=subtotal)
    order_code = f"SO-B2B-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"
    payload = {
        "order_code": order_code,
        "order_date": date.today(),
        "customer_id": buyer.id,
        "placed_for_customer_id": buyer.id,
        "ordered_by_party_id": actor.id,
        "sales_channel": "B2B",
        "status": (body.status or "CONFIRMED").upper(),
        "payment_status": (body.payment_status or "UNPAID").upper(),
        "fulfillment_status": "UNFULFILLED",
        "payment_method": body.payment_method,
        "shipping_charge": ship,
        "handling_charge": 0,
        "shipping_street": body.shipping_street,
        "shipping_city": body.shipping_city,
        "shipping_state": body.shipping_state,
        "shipping_zip": body.shipping_zip,
        "shipping_phone": body.shipping_phone,
        "shipping_name": body.shipping_name or buyer.name,
        "items": lines,
    }
    try:
        so = create_sale_order(
            db,
            vendor_id=vendor_id,
            data=payload,
            created_by=user.email,
            user_id=user.id,
            stock_mode="deduct" if payload["status"] == "CONFIRMED" else "none",
        )
        db.commit()
        db.refresh(so)
    except SalesError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Created", _so_payload(db, so), status_code=201)


@router.get("/orders")
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    _, vendor_id, actor = ctx
    scope = party_svc.order_scope_party_ids(db, vendor_id, actor)
    q = (
        select(SaleOrder)
        .where(
            SaleOrder.vendor_id == vendor_id,
            or_(
                SaleOrder.customer_id.in_(scope),
                SaleOrder.ordered_by_party_id == actor.id,
                SaleOrder.placed_for_customer_id.in_(scope),
            ),
        )
        .order_by(SaleOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = db.scalars(q).all()
    data = []
    for s in rows:
        r = row(s, SO_FIELDS)
        r["courier_label"] = courier_label(s.courier)
        data.append(r)
    return success("Orders", {"data": data})


@router.get("/orders/{so_id}")
def get_order(
    so_id: int,
    ctx: tuple[AuthUser, int, Customer] = Depends(_require_trade),
    db: Session = Depends(get_db),
):
    _, vendor_id, actor = ctx
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    scope = party_svc.order_scope_party_ids(db, vendor_id, actor)
    allowed = (
        so.customer_id in scope
        or so.ordered_by_party_id == actor.id
        or (so.placed_for_customer_id and so.placed_for_customer_id in scope)
    )
    if not allowed:
        return error("Forbidden", status_code=403)
    return success("Order", _so_payload(db, so))
