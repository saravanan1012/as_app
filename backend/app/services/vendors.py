from copy import deepcopy
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, attributes

from app.core.security import hash_password
from app.core.settings_merge import deep_merge, settings_from_patch_model
from app.core.storage import vendor_storage_root
from app.models import DEFAULT_VENDOR_SETTINGS, Item, Location, Stock, User, Vendor
from app.schemas.vendor import BootstrapAdmin, VendorCreate, VendorSettingsPatch, VendorUpdate


def get_vendor_or_none(db: Session, vendor_id: int) -> Vendor | None:
    return db.get(Vendor, vendor_id)


def ensure_main_location(db: Session, vendor: Vendor) -> Location:
    loc = db.scalar(
        select(Location).where(Location.vendor_id == vendor.id, Location.code == "MAIN")
    )
    if loc:
        if not vendor.default_location_id:
            vendor.default_location_id = loc.id
        return loc
    loc = Location(
        vendor_id=vendor.id,
        code="MAIN",
        name="Main Warehouse",
        type="WAREHOUSE",
    )
    db.add(loc)
    db.flush()
    vendor.default_location_id = loc.id
    return loc


def create_vendor(db: Session, body: VendorCreate) -> Vendor:
    settings = deepcopy(DEFAULT_VENDOR_SETTINGS)
    if body.settings:
        settings = deep_merge(settings, settings_from_patch_model(body.settings))

    vendor = Vendor(
        name=body.name.strip(),
        slug=body.slug,
        plan=body.plan,
        gstin=body.gstin,
        state_code=body.state_code,
        legal_name=body.legal_name,
        address=body.address,
        status="ACTIVE",
        settings=settings,
    )
    db.add(vendor)
    db.flush()
    ensure_main_location(db, vendor)
    vendor_storage_root(vendor.id)

    if body.admin_email and body.admin_password:
        bootstrap_admin(
            db,
            vendor,
            BootstrapAdmin(
                email=body.admin_email,
                name=body.admin_name or body.name.strip() + " Admin",
                password=body.admin_password,
                role="ADMIN",
            ),
        )

    db.commit()
    db.refresh(vendor)
    return vendor


def update_vendor(db: Session, vendor: Vendor, body: VendorUpdate) -> Vendor:
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(vendor, key, value)
    if body.status == "SUSPENDED" and not vendor.suspended_at:
        vendor.suspended_at = datetime.now(timezone.utc)
    if body.status == "ACTIVE":
        vendor.suspended_at = None
    db.commit()
    db.refresh(vendor)
    return vendor


def patch_settings(db: Session, vendor: Vendor, patch: VendorSettingsPatch) -> Vendor:
    current = vendor.settings if isinstance(vendor.settings, dict) else {}
    merged = deep_merge(current, settings_from_patch_model(patch))
    # Keep top-level tax fields in sync when settings.tax provided
    tax = merged.get("tax") or {}
    if "gstin" in tax and tax["gstin"] is not None:
        vendor.gstin = tax["gstin"] or vendor.gstin
    if "state_code" in tax and tax["state_code"] is not None:
        vendor.state_code = tax["state_code"] or vendor.state_code
    locale = merged.get("locale") or {}
    if locale.get("timezone"):
        vendor.timezone = locale["timezone"]
    if locale.get("currency"):
        vendor.currency = locale["currency"]

    vendor.settings = merged
    attributes.flag_modified(vendor, "settings")
    db.commit()
    db.refresh(vendor)
    return vendor


def set_store_enabled(db: Session, vendor: Vendor, enabled: bool) -> Vendor:
    from app.schemas.vendor import FeaturesSettings

    return patch_settings(
        db,
        vendor,
        VendorSettingsPatch(features=FeaturesSettings(store_enabled=enabled)),
    )


def bootstrap_admin(db: Session, vendor: Vendor, body: BootstrapAdmin) -> User:
    email = str(body.email).strip().lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        if existing.vendor_id and existing.vendor_id != vendor.id:
            raise ValueError("Email already used by another vendor")
        existing.name = body.name.strip()
        existing.role = body.role
        existing.status = "ACTIVE"
        existing.vendor_id = vendor.id
        existing.password = hash_password(body.password)
        db.commit()
        db.refresh(existing)
        return existing

    user = User(
        email=email,
        name=body.name.strip(),
        role=body.role,
        status="ACTIVE",
        vendor_id=vendor.id,
        password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def platform_dashboard(db: Session) -> dict:
    vendor_total = db.scalar(select(func.count()).select_from(Vendor)) or 0
    vendor_active = (
        db.scalar(select(func.count()).select_from(Vendor).where(Vendor.status == "ACTIVE")) or 0
    )
    vendor_suspended = (
        db.scalar(select(func.count()).select_from(Vendor).where(Vendor.status == "SUSPENDED"))
        or 0
    )
    users_total = db.scalar(select(func.count()).select_from(User)) or 0
    items_total = db.scalar(select(func.count()).select_from(Item)) or 0
    stock_rows = db.scalar(select(func.count()).select_from(Stock)) or 0
    store_on = 0
    for v in db.scalars(select(Vendor)).all():
        feats = (v.settings or {}).get("features") or {}
        if feats.get("store_enabled"):
            store_on += 1

    per_vendor = []
    for v in db.scalars(select(Vendor).order_by(Vendor.id)).all():
        uc = db.scalar(select(func.count()).select_from(User).where(User.vendor_id == v.id)) or 0
        ic = db.scalar(select(func.count()).select_from(Item).where(Item.vendor_id == v.id)) or 0
        feats = (v.settings or {}).get("features") or {}
        per_vendor.append(
            {
                "id": v.id,
                "name": v.name,
                "slug": v.slug,
                "status": v.status,
                "store_enabled": bool(feats.get("store_enabled")),
                "users": uc,
                "items": ic,
            }
        )

    return {
        "vendors": {
            "total": vendor_total,
            "active": vendor_active,
            "suspended": vendor_suspended,
            "store_enabled_count": store_on,
        },
        "users_total": users_total,
        "items_total": items_total,
        "stock_rows": stock_rows,
        "vendors_detail": per_vendor,
    }
