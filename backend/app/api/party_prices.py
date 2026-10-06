"""Admin CRUD for per-product party trade price rules."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models import Item, PartyPriceRule
from app.services.parties import TRADE_PARTY_TYPES
from app.services.pricing import PRICE_MODES

router = APIRouter(prefix="/party-price-rules", tags=["party-prices"])

FIELDS = [
    "id",
    "vendor_id",
    "item_id",
    "party_type",
    "mode",
    "value",
    "status",
    "created_at",
    "updated_at",
]


class RuleIn(BaseModel):
    item_id: int
    party_type: str
    mode: str
    value: float = Field(ge=0)
    status: str = "ACTIVE"


class BulkRuleIn(BaseModel):
    item_id: int
    rules: list[RuleIn]


@router.get("")
def list_rules(
    item_id: int | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(PartyPriceRule).where(PartyPriceRule.vendor_id == vendor_id)
    if item_id is not None:
        q = q.where(PartyPriceRule.item_id == item_id)
    rows = db.scalars(q.order_by(PartyPriceRule.item_id, PartyPriceRule.party_type)).all()
    return success("Rules", {"data": [row(r, FIELDS) for r in rows]})


@router.post("")
def upsert_rule(
    body: RuleIn,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    pt = body.party_type.upper()
    mode = body.mode.upper()
    if pt not in TRADE_PARTY_TYPES:
        return error("party_type must be DISTRIBUTOR|DEALER|RETAILER", status_code=400)
    if mode not in PRICE_MODES:
        return error("mode must be PERCENT_OFF|FIXED_PRICE|FIXED_OFF", status_code=400)
    item = db.get(Item, body.item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)

    existing = db.scalar(
        select(PartyPriceRule).where(
            PartyPriceRule.vendor_id == vendor_id,
            PartyPriceRule.item_id == body.item_id,
            PartyPriceRule.party_type == pt,
        )
    )
    if existing:
        existing.mode = mode
        existing.value = body.value
        existing.status = (body.status or "ACTIVE").upper()
        db.commit()
        db.refresh(existing)
        return success("Updated", row(existing, FIELDS))

    r = PartyPriceRule(
        vendor_id=vendor_id,
        item_id=body.item_id,
        party_type=pt,
        mode=mode,
        value=body.value,
        status=(body.status or "ACTIVE").upper(),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return success("Created", row(r, FIELDS), status_code=201)


@router.put("/bulk")
def bulk_upsert(
    body: BulkRuleIn,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    item = db.get(Item, body.item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Item not found", status_code=404)

    out = []
    for rule in body.rules:
        pt = rule.party_type.upper()
        mode = rule.mode.upper()
        if pt not in TRADE_PARTY_TYPES or mode not in PRICE_MODES:
            continue
        existing = db.scalar(
            select(PartyPriceRule).where(
                PartyPriceRule.vendor_id == vendor_id,
                PartyPriceRule.item_id == body.item_id,
                PartyPriceRule.party_type == pt,
            )
        )
        if existing:
            existing.mode = mode
            existing.value = rule.value
            existing.status = (rule.status or "ACTIVE").upper()
            out.append(existing)
        else:
            r = PartyPriceRule(
                vendor_id=vendor_id,
                item_id=body.item_id,
                party_type=pt,
                mode=mode,
                value=rule.value,
                status=(rule.status or "ACTIVE").upper(),
            )
            db.add(r)
            out.append(r)
    db.commit()
    for r in out:
        db.refresh(r)
    return success("Saved", {"data": [row(r, FIELDS) for r in out]})


@router.delete("/{rule_id}")
def delete_rule(
    rule_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    r = db.get(PartyPriceRule, rule_id)
    if not r or r.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    db.delete(r)
    db.commit()
    return success("Deleted", None)
