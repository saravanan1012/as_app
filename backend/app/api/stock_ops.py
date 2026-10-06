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
from app.models import Item, Location, StockMovement
from app.models.orders import StockAdjustment, StockAdjustmentLine
from app.services.audit import write_audit
from app.services.stock_ledger import StockError, apply_delta

router = APIRouter(tags=["stock"])


class AdjLineIn(BaseModel):
    item_id: int
    location_id: int
    qty_delta: int


class AdjIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    adjustment_date: date
    reason: str = "ADJUSTMENT"
    notes: str | None = None
    items: list[AdjLineIn]


@router.get("/stock-movements")
def list_movements(
    item_id: int | None = None,
    location_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: tuple[AuthUser, int] = Depends(perm("stock.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(StockMovement).where(StockMovement.vendor_id == vendor_id)
    if item_id:
        q = q.where(StockMovement.item_id == item_id)
    if location_id:
        q = q.where(StockMovement.location_id == location_id)
    rows = db.scalars(
        q.order_by(StockMovement.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return success(
        "Stock movements",
        {
            "data": [
                row(
                    m,
                    [
                        "id",
                        "item_id",
                        "location_id",
                        "qty_delta",
                        "qty_after",
                        "reason",
                        "reference_type",
                        "reference_id",
                        "created_by",
                        "created_at",
                    ],
                )
                for m in rows
            ]
        },
    )


@router.post("/stock-adjustments")
def create_adjustment(
    body: AdjIn,
    ctx: tuple[AuthUser, int] = Depends(perm("stock.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    if not body.items:
        return error("Adjustment lines required", status_code=400)
    if body.reason != "ADJUSTMENT":
        return error("reason must be ADJUSTMENT", status_code=400)

    try:
        adj = StockAdjustment(
            vendor_id=vendor_id,
            code=body.code,
            adjustment_date=body.adjustment_date,
            reason=body.reason,
            notes=body.notes,
            created_by=user.email,
        )
        db.add(adj)
        db.flush()

        for line in body.items:
            if line.qty_delta == 0:
                raise StockError("qty_delta cannot be zero")
            item = db.get(Item, line.item_id)
            loc = db.get(Location, line.location_id)
            if not item or item.vendor_id != vendor_id:
                raise StockError(f"Item {line.item_id} not found")
            if not loc or loc.vendor_id != vendor_id:
                raise StockError(f"Location {line.location_id} not found")
            db.add(
                StockAdjustmentLine(
                    vendor_id=vendor_id,
                    stock_adjustment_id=adj.id,
                    item_id=line.item_id,
                    location_id=line.location_id,
                    qty_delta=line.qty_delta,
                )
            )
            apply_delta(
                db,
                vendor_id=vendor_id,
                item_id=line.item_id,
                location_id=line.location_id,
                qty_delta=line.qty_delta,
                reason="ADJUSTMENT",
                reference_type="STOCK_ADJUSTMENT",
                reference_id=adj.id,
                created_by=user.email,
            )

        write_audit(
            db,
            vendor_id=vendor_id,
            user=user,
            action="CREATE",
            entity_type="STOCK_ADJUSTMENT",
            entity_id=adj.id,
            new_data={"code": adj.code},
        )
        db.commit()
        db.refresh(adj)
    except StockError as e:
        db.rollback()
        return error(str(e), status_code=400)

    lines = db.scalars(
        select(StockAdjustmentLine).where(StockAdjustmentLine.stock_adjustment_id == adj.id)
    ).all()
    return success(
        "Created",
        {
            **row(adj, ["id", "code", "adjustment_date", "reason", "notes"]),
            "items": [row(l, ["id", "item_id", "location_id", "qty_delta"]) for l in lines],
        },
        status_code=201,
    )
