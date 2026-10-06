from datetime import date

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from app.models import Customer, CustomerAddress
from app.services import parties as party_svc
from app.services.audit import write_audit

router = APIRouter(prefix="/customers", tags=["customers"])

FIELDS = [
    "id", "vendor_id", "name", "phone", "gstin", "email", "party_type", "parent_id",
    "acquisition_source", "acquisition_meta", "status", "member_since", "dob", "user_id",
    "created_at", "updated_at",
]


class AddressIn(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    status: str = "ACTIVE"


class CustomerIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: str | None = None
    gstin: str | None = None
    email: EmailStr | None = None
    party_type: str = "CUSTOMER"
    parent_id: int | None = None
    acquisition_source: str | None = None
    acquisition_meta: dict | None = None
    status: str = "ACTIVE"
    member_since: date | None = None
    dob: date | None = None
    address: AddressIn | None = None


class CustomerPatch(BaseModel):
    name: str | None = None
    phone: str | None = None
    gstin: str | None = None
    email: EmailStr | None = None
    party_type: str | None = None
    parent_id: int | None = None
    acquisition_source: str | None = None
    acquisition_meta: dict | None = None
    status: str | None = None
    member_since: date | None = None
    dob: date | None = None


@router.get("")
def list_customers(
    party_type: str | None = None,
    acquisition_source: str | None = None,
    parent_id: int | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: tuple[AuthUser, int] = Depends(perm("customers.read")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    q = select(Customer).where(Customer.vendor_id == vendor_id)
    if party_type:
        q = q.where(Customer.party_type == party_type.upper())
    if acquisition_source:
        q = q.where(Customer.acquisition_source == acquisition_source.upper())
    if parent_id is not None:
        q = q.where(Customer.parent_id == parent_id)
    if search:
        like = f"%{search}%"
        q = q.where(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
            )
        )
    rows = db.scalars(q.order_by(Customer.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success(
        "Customers fetched",
        {
            "data": [row(c, FIELDS) for c in rows],
            "pagination": {"page": page, "pageSize": page_size},
        },
    )


@router.get("/{customer_id}")
def get_customer(
    customer_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    c = db.get(Customer, customer_id)
    if not c or c.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    addrs = db.scalars(
        select(CustomerAddress).where(
            CustomerAddress.customer_id == c.id,
            CustomerAddress.vendor_id == vendor_id,
        )
    ).all()
    data = row(c, FIELDS)
    data["addresses"] = [
        row(a, ["id", "street", "city", "state", "zip", "status"]) for a in addrs
    ]
    data["children"] = [
        row(ch, ["id", "name", "party_type", "status"])
        for ch in party_svc.list_children(db, vendor_id, c.id)
    ]
    return success("Customer fetched", data)


@router.post("")
def create_customer(
    body: CustomerIn,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    try:
        party_type = body.party_type.upper()
        acq = party_svc.validate_acquisition_source(body.acquisition_source)
        party_svc.validate_party_link(
            db, vendor_id=vendor_id, party_type=party_type, parent_id=body.parent_id
        )
    except ValueError as exc:
        return error(str(exc), status_code=400)

    c = Customer(
        vendor_id=vendor_id,
        name=body.name.strip(),
        phone=body.phone,
        gstin=body.gstin,
        email=str(body.email).lower() if body.email else None,
        party_type=party_type,
        parent_id=body.parent_id,
        acquisition_source=acq,
        acquisition_meta=body.acquisition_meta,
        status=body.status.upper(),
        member_since=body.member_since,
        dob=body.dob,
    )
    db.add(c)
    db.flush()
    if body.address:
        db.add(
            CustomerAddress(
                vendor_id=vendor_id,
                customer_id=c.id,
                street=body.address.street,
                city=body.address.city,
                state=body.address.state,
                zip=body.address.zip,
                status=body.address.status.upper(),
            )
        )
    write_audit(
        db,
        vendor_id=vendor_id,
        user=user,
        action="CREATE",
        entity_type="customer",
        entity_id=c.id,
        new_data=row(c, FIELDS),
    )
    db.commit()
    db.refresh(c)
    return success("Created", row(c, FIELDS), status_code=201)


@router.patch("/{customer_id}")
def patch_customer(
    customer_id: int,
    body: CustomerPatch,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.write")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    c = db.get(Customer, customer_id)
    if not c or c.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    old = row(c, FIELDS)
    data = body.model_dump(exclude_unset=True)
    party_type = (data.get("party_type") or c.party_type).upper()
    parent_id = data["parent_id"] if "parent_id" in data else c.parent_id
    try:
        if "acquisition_source" in data:
            data["acquisition_source"] = party_svc.validate_acquisition_source(
                data["acquisition_source"]
            )
        party_svc.validate_party_link(
            db,
            vendor_id=vendor_id,
            party_type=party_type,
            parent_id=parent_id,
            self_id=c.id,
        )
    except ValueError as exc:
        return error(str(exc), status_code=400)

    for k, v in data.items():
        if k == "party_type" and v:
            v = v.upper()
        if k == "email" and v:
            v = str(v).lower()
        if k == "status" and v:
            v = v.upper()
        setattr(c, k, v)
    write_audit(
        db,
        vendor_id=vendor_id,
        user=user,
        action="UPDATE",
        entity_type="customer",
        entity_id=c.id,
        old_data=old,
        new_data=row(c, FIELDS),
    )
    db.commit()
    db.refresh(c)
    return success("Updated", row(c, FIELDS))


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.manage")),
    db: Session = Depends(get_db),
):
    user, vendor_id = ctx
    c = db.get(Customer, customer_id)
    if not c or c.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    write_audit(
        db,
        vendor_id=vendor_id,
        user=user,
        action="DELETE",
        entity_type="customer",
        entity_id=c.id,
        old_data=row(c, FIELDS),
    )
    db.delete(c)
    db.commit()
    return success("Deleted", {"id": customer_id})
