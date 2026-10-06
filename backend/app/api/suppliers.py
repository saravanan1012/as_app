from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models import Supplier

router = APIRouter(prefix="/suppliers", tags=["suppliers"])
FIELDS = ["id", "vendor_id", "code", "name", "gstin", "contact_person", "address", "phone", "email"]


class SupplierIn(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=150)
    gstin: str | None = None
    contact_person: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class SupplierPatch(BaseModel):
    code: str | None = None
    name: str | None = None
    gstin: str | None = None
    contact_person: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


@router.get("")
def list_suppliers(ctx: tuple[AuthUser, int] = Depends(perm("suppliers.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(Supplier).where(Supplier.vendor_id == vendor_id).order_by(Supplier.id.desc())).all()
    return success("Suppliers fetched", [row(s, FIELDS) for s in rows])


@router.post("")
def create_supplier(body: SupplierIn, ctx: tuple[AuthUser, int] = Depends(perm("suppliers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    s = Supplier(vendor_id=vendor_id, **body.model_dump())
    s.code = s.code.strip().upper()
    db.add(s)
    db.commit()
    db.refresh(s)
    return success("Created", row(s, FIELDS), status_code=201)


@router.patch("/{supplier_id}")
def patch_supplier(supplier_id: int, body: SupplierPatch, ctx: tuple[AuthUser, int] = Depends(perm("suppliers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    s = db.get(Supplier, supplier_id)
    if not s or s.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "code" and v:
            v = v.strip().upper()
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return success("Updated", row(s, FIELDS))


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, ctx: tuple[AuthUser, int] = Depends(perm("suppliers.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    s = db.get(Supplier, supplier_id)
    if not s or s.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    db.delete(s)
    db.commit()
    return success("Deleted", {"id": supplier_id})
