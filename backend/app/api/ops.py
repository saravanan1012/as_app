from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.db import get_db
from copy import deepcopy

from sqlalchemy.orm.attributes import flag_modified

from app.models import Activity, AuditLog, Customer, Item, Stock, Transaction, Vendor

router = APIRouter(tags=["ops"])


class TxIn(BaseModel):
    transaction_date: date
    amount: float
    type: str | None = None
    direction: str | None = None
    reference_id: int | None = None
    reference_type: str | None = None
    payment_method: str | None = None
    reference_number: str | None = None
    notes: str | None = None


class ActivityIn(BaseModel):
    customer_id: int
    type: str = Field(min_length=1, max_length=30)
    subject: str | None = None
    body: str | None = None
    due_at: datetime | None = None


class EcommerceShippingIn(BaseModel):
    enabled: bool | None = None
    flat_rate: float | None = None
    interstate_flat_rate: float | None = None
    free_over_enabled: bool | None = None
    free_over: float | None = None
    eta_same_min: int | None = None
    eta_same_max: int | None = None
    eta_other_min: int | None = None
    eta_other_max: int | None = None


class B2bShippingIn(BaseModel):
    qty_tiers: list[dict] | None = None


class ShippingSettingsIn(BaseModel):
    ecommerce: EcommerceShippingIn | None = None
    b2b: B2bShippingIn | None = None
    couriers: list[str] | None = None
    # Legacy flat fields still accepted and mapped into ecommerce / b2b
    flat_rate: float | None = None
    free_over: float | None = None
    qty_tiers: list[dict] | None = None


@router.get("/vendor-settings/shipping")
def get_shipping_settings(
    ctx: tuple[AuthUser, int] = Depends(perm("dashboard.read")),
    db: Session = Depends(get_db),
):
    from app.services.pricing import normalize_shipping

    _, vendor_id = ctx
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    shipping = normalize_shipping((vendor.settings or {}).get("shipping") or {})
    return success("Shipping settings", shipping)


@router.patch("/vendor-settings/shipping")
def patch_shipping_settings(
    body: ShippingSettingsIn,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.manage")),
    db: Session = Depends(get_db),
):
    """Admin: Online Store (amount-based) + B2B qty tiers + couriers."""
    from app.services.pricing import normalize_shipping

    _, vendor_id = ctx
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    settings = deepcopy(vendor.settings or {})
    shipping = normalize_shipping(settings.get("shipping") or {})
    data = body.model_dump(exclude_unset=True)

    if "ecommerce" in data and data["ecommerce"] is not None:
        eco = dict(shipping.get("ecommerce") or {})
        for k, v in data["ecommerce"].items():
            if v is not None or k in ("free_over",):
                eco[k] = v
        shipping["ecommerce"] = eco
    if "b2b" in data and data["b2b"] is not None:
        b2b = dict(shipping.get("b2b") or {})
        if data["b2b"].get("qty_tiers") is not None:
            b2b["qty_tiers"] = data["b2b"]["qty_tiers"]
        shipping["b2b"] = b2b
    if "couriers" in data and data["couriers"] is not None:
        shipping["couriers"] = data["couriers"]

    # Legacy field mapping
    eco = dict(shipping.get("ecommerce") or {})
    if "flat_rate" in data and data["flat_rate"] is not None:
        eco["flat_rate"] = data["flat_rate"]
    if "free_over" in data:
        eco["free_over"] = data["free_over"]
        if data["free_over"] is not None:
            eco["free_over_enabled"] = True
    shipping["ecommerce"] = eco
    if "qty_tiers" in data and data["qty_tiers"] is not None:
        shipping["b2b"] = {**(shipping.get("b2b") or {}), "qty_tiers": data["qty_tiers"]}

    if not shipping.get("couriers"):
        shipping["couriers"] = ["AKR_PARCEL", "MARUTHI_PARCEL"]

    settings["shipping"] = shipping
    vendor.settings = settings
    flag_modified(vendor, "settings")
    db.commit()
    return success("Updated", normalize_shipping(shipping))


class TaxSettingsIn(BaseModel):
    gst_enabled: bool | None = None
    gstin: str | None = None
    state_code: str | None = None


def _normalize_tax(vendor: Vendor) -> dict:
    settings = vendor.settings if isinstance(vendor.settings, dict) else {}
    tax = dict(settings.get("tax") or {})
    return {
        "gst_enabled": bool(tax.get("gst_enabled", True)),
        "gstin": (tax.get("gstin") or vendor.gstin or "") or "",
        "state_code": (tax.get("state_code") or vendor.state_code or "TN") or "TN",
    }


@router.get("/vendor-settings/tax")
def get_tax_settings(
    ctx: tuple[AuthUser, int] = Depends(perm("dashboard.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    return success("Tax settings", _normalize_tax(vendor))


@router.patch("/vendor-settings/tax")
def patch_tax_settings(
    body: TaxSettingsIn,
    ctx: tuple[AuthUser, int] = Depends(perm("customers.manage")),
    db: Session = Depends(get_db),
):
    """Admin GST profile: enable store GST display, GSTIN, place-of-supply state."""
    _, vendor_id = ctx
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    settings = deepcopy(vendor.settings or {})
    tax = dict(settings.get("tax") or {})
    data = body.model_dump(exclude_unset=True)
    if "gst_enabled" in data and data["gst_enabled"] is not None:
        tax["gst_enabled"] = bool(data["gst_enabled"])
    if "gstin" in data:
        tax["gstin"] = (data["gstin"] or "").strip().upper() or ""
        vendor.gstin = tax["gstin"] or None
    if "state_code" in data and data["state_code"] is not None:
        code = str(data["state_code"]).strip().upper()[:2]
        tax["state_code"] = code
        vendor.state_code = code or vendor.state_code
    settings["tax"] = tax
    vendor.settings = settings
    flag_modified(vendor, "settings")
    db.commit()
    return success("Updated", _normalize_tax(vendor))


@router.get("/transactions")
def list_tx(ctx: tuple[AuthUser, int] = Depends(perm("transactions.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(
        select(Transaction)
        .where(Transaction.vendor_id == vendor_id, Transaction.deleted_at.is_(None))
        .order_by(Transaction.id.desc())
        .limit(200)
    ).all()
    return success(
        "Transactions fetched",
        [row(t, ["id", "transaction_date", "type", "direction", "amount", "reference_type", "reference_id", "payment_method", "notes"]) for t in rows],
    )


@router.post("/transactions")
def create_tx(body: TxIn, ctx: tuple[AuthUser, int] = Depends(perm("transactions.write")), db: Session = Depends(get_db)):
    user, vendor_id = ctx
    t = Transaction(vendor_id=vendor_id, created_by=user.email, **body.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return success("Created", row(t, ["id", "amount", "type", "direction"]), status_code=201)


@router.get("/activities")
def list_activities(
    customer_id: int | None = None,
    ctx: tuple[AuthUser, int] = Depends(perm("activities.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    q = select(Activity).where(Activity.vendor_id == vendor_id)
    if customer_id:
        q = q.where(Activity.customer_id == customer_id)
    rows = db.scalars(q.order_by(Activity.id.desc()).limit(200)).all()
    return success(
        "Activities fetched",
        [row(a, ["id", "customer_id", "type", "subject", "body", "due_at", "done_at", "created_by"]) for a in rows],
    )


@router.post("/activities")
def create_activity(body: ActivityIn, ctx: tuple[AuthUser, int] = Depends(perm("activities.write")), db: Session = Depends(get_db)):
    user, vendor_id = ctx
    c = db.get(Customer, body.customer_id)
    if not c or c.vendor_id != vendor_id:
        return error("Customer not found", status_code=404)
    a = Activity(vendor_id=vendor_id, created_by=user.email, **body.model_dump())
    db.add(a)
    db.commit()
    db.refresh(a)
    return success("Created", row(a, ["id", "customer_id", "type", "subject"]), status_code=201)


@router.get("/audit-logs")
def list_audit(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    ctx: tuple[AuthUser, int] = Depends(perm("audit.read")),
    db: Session = Depends(get_db),
):
    _, vendor_id = ctx
    rows = db.scalars(
        select(AuditLog)
        .where(AuditLog.vendor_id == vendor_id)
        .order_by(AuditLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return success(
        "Audit logs fetched",
        {
            "data": [
                row(a, ["id", "action", "entity_type", "entity_id", "user_name", "created_at", "old_data", "new_data"])
                for a in rows
            ]
        },
    )


@router.get("/dashboard")
def vendor_dashboard(ctx: tuple[AuthUser, int] = Depends(perm("dashboard.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    items = db.scalar(select(func.count()).select_from(Item).where(Item.vendor_id == vendor_id)) or 0
    customers = db.scalar(select(func.count()).select_from(Customer).where(Customer.vendor_id == vendor_id)) or 0
    stock_qty = db.scalar(
        select(func.coalesce(func.sum(Stock.quantity_on_hand), 0)).where(Stock.vendor_id == vendor_id)
    ) or 0
    by_party = {}
    for pt in ("DISTRIBUTOR", "DEALER", "RETAILER", "CUSTOMER"):
        by_party[pt] = db.scalar(
            select(func.count()).select_from(Customer).where(
                Customer.vendor_id == vendor_id, Customer.party_type == pt
            )
        ) or 0
    return success(
        "Dashboard",
        {
            "items": items,
            "customers": customers,
            "customers_by_party_type": by_party,
            "stock_on_hand_total": int(stock_qty),
        },
    )
