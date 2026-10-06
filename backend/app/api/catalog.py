from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models import Item, Location, Stock, TaxCategory
from app.services.audit import write_audit

router = APIRouter(tags=["catalog"])

ITEM_FIELDS = [
    "id", "vendor_id", "code", "name", "description", "unit_of_measure", "cost_price",
    "sale_price", "category", "type", "status", "is_sellable", "is_online_sale",
    "sale_price_includes_gst", "tax_category_id", "primary_image", "created_at", "updated_at",
]


class ItemIn(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    unit_of_measure: str = "PCS"
    cost_price: float = 0
    sale_price: float = 0
    category: str = "GENERAL"
    type: str = "PRODUCT"
    status: str = "ACTIVE"
    is_sellable: bool = True
    is_online_sale: bool = False
    sale_price_includes_gst: bool = True
    tax_category_id: int | None = None
    primary_image: str | None = None


class ItemPatch(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    unit_of_measure: str | None = None
    cost_price: float | None = None
    sale_price: float | None = None
    category: str | None = None
    type: str | None = None
    status: str | None = None
    is_sellable: bool | None = None
    is_online_sale: bool | None = None
    sale_price_includes_gst: bool | None = None
    tax_category_id: int | None = None
    primary_image: str | None = None


class LocationIn(BaseModel):
    code: str
    name: str
    type: str | None = "WAREHOUSE"


class StockIn(BaseModel):
    item_id: int
    location_id: int
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    reorder_level: int = 0
    reorder_qty: int = 0


class TaxIn(BaseModel):
    code: str
    name: str
    gst_rate: float = 0
    hsn_sac: str | None = None
    description: str | None = None


@router.get("/items")
def list_items(
    search: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(Item).where(Item.vendor_id == vendor_id)
    if status:
        q = q.where(Item.status == status.upper())
    if search:
        like = f"%{search}%"
        q = q.where(or_(Item.name.ilike(like), Item.code.ilike(like)))
    rows = db.scalars(q.order_by(Item.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success("Items fetched", {"data": [row(i, ITEM_FIELDS) for i in rows]})


@router.post("/items")
def create_item(
    body: ItemIn,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    item = Item(vendor_id=vendor_id, **body.model_dump())
    item.status = item.status.upper()
    db.add(item)
    db.flush()
    write_audit(db, vendor_id=vendor_id, user=user, action="CREATE", entity_type="item", entity_id=item.id, new_data=row(item, ITEM_FIELDS))
    db.commit()
    db.refresh(item)
    return success("Created", row(item, ITEM_FIELDS), status_code=201)


@router.get("/items/{item_id}")
def get_item(item_id: int, ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    return success("Item fetched", row(item, ITEM_FIELDS))


@router.patch("/items/{item_id}")
def patch_item(
    item_id: int,
    body: ItemPatch,
    ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    old = row(item, ITEM_FIELDS)
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "status" and v:
            v = v.upper()
        setattr(item, k, v)
    write_audit(db, vendor_id=vendor_id, user=user, action="UPDATE", entity_type="item", entity_id=item.id, old_data=old, new_data=row(item, ITEM_FIELDS))
    db.commit()
    db.refresh(item)
    return success("Updated", row(item, ITEM_FIELDS))


@router.delete("/items/{item_id}")
def delete_item(item_id: int, ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.manage")), db: Session = Depends(get_db)):
    user, vendor_id = ctx
    item = db.get(Item, item_id)
    if not item or item.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    write_audit(db, vendor_id=vendor_id, user=user, action="DELETE", entity_type="item", entity_id=item.id, old_data=row(item, ITEM_FIELDS))
    db.delete(item)
    db.commit()
    return success("Deleted", {"id": item_id})


@router.get("/locations")
def list_locations(ctx: tuple[AuthUser, int] = Depends(perm("stock.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(Location).where(Location.vendor_id == vendor_id).order_by(Location.id)).all()
    return success("Locations fetched", [row(r, ["id", "vendor_id", "code", "name", "type"]) for r in rows])


@router.post("/locations")
def create_location(body: LocationIn, ctx: tuple[AuthUser, int] = Depends(perm("stock.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    loc = Location(vendor_id=vendor_id, code=body.code.strip().upper(), name=body.name.strip(), type=body.type)
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return success("Created", row(loc, ["id", "vendor_id", "code", "name", "type"]), status_code=201)


@router.get("/stock")
def list_stock(ctx: tuple[AuthUser, int] = Depends(perm("stock.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(Stock).where(Stock.vendor_id == vendor_id).order_by(Stock.id.desc())).all()
    data = []
    for s in rows:
        d = row(s, ["id", "vendor_id", "item_id", "location_id", "quantity_on_hand", "quantity_reserved", "reorder_level", "reorder_qty"])
        d["quantity_available"] = s.quantity_on_hand - s.quantity_reserved
        data.append(d)
    return success("Stock fetched", data)


@router.post("/stock")
def upsert_stock(body: StockIn, ctx: tuple[AuthUser, int] = Depends(perm("stock.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    item = db.get(Item, body.item_id)
    loc = db.get(Location, body.location_id)
    if not item or item.vendor_id != vendor_id or not loc or loc.vendor_id != vendor_id:
        return error("Invalid item/location for vendor", status_code=400)
    existing = db.scalar(
        select(Stock).where(Stock.item_id == body.item_id, Stock.location_id == body.location_id)
    )
    if existing:
        existing.quantity_on_hand = body.quantity_on_hand
        existing.quantity_reserved = body.quantity_reserved
        existing.reorder_level = body.reorder_level
        existing.reorder_qty = body.reorder_qty
        db.commit()
        db.refresh(existing)
        return success("Updated", row(existing, ["id", "item_id", "location_id", "quantity_on_hand", "quantity_reserved", "reorder_level", "reorder_qty"]))
    s = Stock(vendor_id=vendor_id, **body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return success("Created", row(s, ["id", "item_id", "location_id", "quantity_on_hand", "quantity_reserved", "reorder_level", "reorder_qty"]), status_code=201)


@router.get("/tax-categories")
def list_tax(ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(TaxCategory).where(TaxCategory.vendor_id == vendor_id)).all()
    return success("Tax categories fetched", [row(t, ["id", "code", "name", "gst_rate", "hsn_sac", "description"]) for t in rows])


@router.post("/tax-categories")
def create_tax(body: TaxIn, ctx: tuple[AuthUser, int] = Depends(perm("catalog.items.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    t = TaxCategory(vendor_id=vendor_id, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return success("Created", row(t, ["id", "code", "name", "gst_rate", "hsn_sac"]), status_code=201)
