"""Phase 2 — Super-admin vendor platform APIs."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthUser, require_permission
from app.core.responses import error, success
from app.core.storage import vendor_storage_root
from app.db import get_db
from app.schemas.vendor import (
    BootstrapAdmin,
    StoreToggle,
    VendorCreate,
    VendorSettingsPatch,
    VendorUpdate,
    vendor_public_dict,
)
from app.services import vendors as vendor_svc

router = APIRouter(prefix="/platform", tags=["platform"])


def require_platform_admin(
    user: AuthUser = Depends(require_permission("platform.vendors.manage")),
) -> AuthUser:
    return user


@router.get("/dashboard")
def platform_dashboard(
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    return success("Platform dashboard", vendor_svc.platform_dashboard(db))


@router.get("/vendors")
def list_vendors(
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Vendor

    rows = db.scalars(select(Vendor).order_by(Vendor.id)).all()
    return success("Vendors fetched", [vendor_public_dict(v) for v in rows])


@router.post("/vendors")
def create_vendor(
    body: VendorCreate,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Vendor

    exists = db.scalar(select(Vendor).where(Vendor.slug == body.slug))
    if exists:
        return error("Slug already exists", status_code=409)
    try:
        vendor = vendor_svc.create_vendor(db, body)
    except ValueError as exc:
        return error(str(exc), status_code=409)
    return success("Created", vendor_public_dict(vendor), status_code=201)


@router.get("/vendors/{vendor_id}")
def get_vendor(
    vendor_id: int,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    data = vendor_public_dict(vendor)
    data["storage_path"] = str(vendor_storage_root(vendor.id))
    return success("Vendor fetched", data)


@router.patch("/vendors/{vendor_id}")
def patch_vendor(
    vendor_id: int,
    body: VendorUpdate,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    vendor = vendor_svc.update_vendor(db, vendor, body)
    return success("Vendor updated", vendor_public_dict(vendor))


@router.patch("/vendors/{vendor_id}/settings")
def patch_vendor_settings(
    vendor_id: int,
    body: VendorSettingsPatch,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    vendor = vendor_svc.patch_settings(db, vendor, body)
    return success("Settings updated", vendor_public_dict(vendor))


@router.patch("/vendors/{vendor_id}/store")
def toggle_store(
    vendor_id: int,
    body: StoreToggle,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    """Enable/disable Store menu + ecommerce for a vendor."""
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    vendor = vendor_svc.set_store_enabled(db, vendor, body.store_enabled)
    return success(
        "Store updated",
        {
            "vendor_id": vendor.id,
            "store_enabled": body.store_enabled,
            "settings": vendor.settings,
        },
    )


@router.post("/vendors/{vendor_id}/bootstrap-admin")
def bootstrap_admin(
    vendor_id: int,
    body: BootstrapAdmin,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    try:
        user = vendor_svc.bootstrap_admin(db, vendor, body)
    except ValueError as exc:
        return error(str(exc), status_code=409)
    return success(
        "Admin ready",
        {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "vendor_id": user.vendor_id,
        },
        status_code=201,
    )


@router.post("/vendors/{vendor_id}/suspend")
def suspend_vendor(
    vendor_id: int,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    vendor = vendor_svc.update_vendor(db, vendor, VendorUpdate(status="SUSPENDED"))
    return success("Vendor suspended", vendor_public_dict(vendor))


@router.post("/vendors/{vendor_id}/activate")
def activate_vendor(
    vendor_id: int,
    _: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    vendor = vendor_svc.update_vendor(db, vendor, VendorUpdate(status="ACTIVE"))
    return success("Vendor activated", vendor_public_dict(vendor))


@router.get("/vendors/{vendor_id}/items-isolation-check")
def items_isolation_check(
    vendor_id: int,
    user: AuthUser = Depends(require_platform_admin),
    db: Session = Depends(get_db),
):
    from sqlalchemy import select
    from app.models import Item

    vendor = vendor_svc.get_vendor_or_none(db, vendor_id)
    if not vendor:
        return error("Vendor not found", status_code=404)
    count = len(db.scalars(select(Item).where(Item.vendor_id == vendor_id)).all())
    return success(
        "OK",
        {"vendor_id": vendor_id, "item_count": count, "actor": user.email},
    )
