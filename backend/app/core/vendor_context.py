from dataclasses import dataclass

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Vendor


@dataclass
class VendorContext:
    vendor_id: int | None
    vendor: Vendor | None
    slug: str | None


def slug_from_host(host: str | None) -> str | None:
    if not host:
        return None
    host = host.split(":")[0].lower()
    parts = host.split(".")
    # e.g. acme.localhost or acme.example.com
    if len(parts) >= 2 and parts[0] not in ("www", "localhost", "api"):
        return parts[0]
    return None


def resolve_vendor_context(
    db: Session,
    request: Request,
    *,
    user_vendor_id: int | None = None,
    is_super_admin: bool = False,
) -> VendorContext:
    settings = get_settings()

    # Super admin must pass ?vendor_id= or x-vendor-slug — never silent DEFAULT_VENDOR_ID
    if is_super_admin:
        q = request.query_params.get("vendor_id")
        if q and q.isdigit():
            vendor = db.get(Vendor, int(q))
            if vendor:
                return VendorContext(vendor_id=vendor.id, vendor=vendor, slug=vendor.slug)
        slug = request.headers.get("x-vendor-slug") or slug_from_host(request.headers.get("host"))
        if slug:
            vendor = db.scalar(select(Vendor).where(Vendor.slug == slug, Vendor.status == "ACTIVE"))
            if vendor:
                return VendorContext(vendor_id=vendor.id, vendor=vendor, slug=vendor.slug)
        return VendorContext(vendor_id=None, vendor=None, slug=None)

    if user_vendor_id:
        vendor = db.get(Vendor, user_vendor_id)
        if vendor:
            return VendorContext(vendor_id=vendor.id, vendor=vendor, slug=vendor.slug)

    slug = request.headers.get("x-vendor-slug") or slug_from_host(request.headers.get("host"))
    if slug:
        vendor = db.scalar(select(Vendor).where(Vendor.slug == slug, Vendor.status == "ACTIVE"))
        if vendor:
            return VendorContext(vendor_id=vendor.id, vendor=vendor, slug=vendor.slug)

    default_id = settings.default_vendor_id
    vendor = db.get(Vendor, default_id)
    if vendor:
        return VendorContext(vendor_id=vendor.id, vendor=vendor, slug=vendor.slug)

    return VendorContext(vendor_id=None, vendor=None, slug=None)
