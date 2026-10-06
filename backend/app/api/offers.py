from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models import Offer
from app.services.parties import PARTY_TYPES

router = APIRouter(prefix="/offers", tags=["offers"])
FIELDS = [
    "id", "vendor_id", "code", "description", "discount_percentage", "discount_amount",
    "free_shipping", "min_order_value", "customer_type", "sales_channel", "item_id",
    "max_uses", "max_uses_per_customer", "start_date", "end_date", "is_active",
]


class OfferIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    description: str | None = None
    discount_percentage: float | None = None
    discount_amount: float | None = None
    free_shipping: bool = False
    min_order_value: float | None = None
    customer_type: str | None = None
    sales_channel: str | None = "ECOMMERCE"
    item_id: int | None = None
    max_uses: int | None = None
    max_uses_per_customer: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True


@router.get("")
def list_offers(ctx: tuple[AuthUser, int] = Depends(perm("offers.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(Offer).where(Offer.vendor_id == vendor_id).order_by(Offer.id.desc())).all()
    return success("Offers fetched", [row(o, FIELDS) for o in rows])


@router.post("")
def create_offer(body: OfferIn, ctx: tuple[AuthUser, int] = Depends(perm("offers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    if body.customer_type and body.customer_type.upper() not in PARTY_TYPES:
        return error("customer_type must be DISTRIBUTOR|DEALER|RETAILER|CUSTOMER", status_code=400)
    o = Offer(vendor_id=vendor_id, **body.model_dump())
    o.code = o.code.strip().upper()
    if o.customer_type:
        o.customer_type = o.customer_type.upper()
    db.add(o)
    db.commit()
    db.refresh(o)
    return success("Created", row(o, FIELDS), status_code=201)


@router.patch("/{offer_id}")
def patch_offer(offer_id: int, body: OfferIn, ctx: tuple[AuthUser, int] = Depends(perm("offers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    o = db.get(Offer, offer_id)
    if not o or o.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "code" and v:
            v = v.strip().upper()
        if k == "customer_type" and v:
            v = v.upper()
        setattr(o, k, v)
    db.commit()
    db.refresh(o)
    return success("Updated", row(o, FIELDS))


@router.delete("/{offer_id}")
def delete_offer(offer_id: int, ctx: tuple[AuthUser, int] = Depends(perm("offers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    o = db.get(Offer, offer_id)
    if not o or o.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    db.delete(o)
    db.commit()
    return success("Deleted", {"id": offer_id})
