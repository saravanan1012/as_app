"""Public vendor/product info — available even when Store is disabled."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_vendor_ctx
from app.api.serialize import row
from app.core.responses import error, success
from app.core.vendor_context import VendorContext
from app.db import get_db
from app.models import Item, ItemImage, Vendor
from app.services.checkout import store_enabled

router = APIRouter(prefix="/public", tags=["public"])

PRODUCT_FIELDS = [
    "id", "code", "name", "description", "unit_of_measure", "sale_price",
    "category", "primary_image", "sale_price_includes_gst",
]


def _require_vendor(vctx: VendorContext) -> Vendor:
    if not vctx.vendor or vctx.vendor.status != "ACTIVE":
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Vendor not found")
    return vctx.vendor


@router.get("/vendor")
def public_vendor(vctx: VendorContext = Depends(get_vendor_ctx)):
    vendor = _require_vendor(vctx)
    settings = vendor.settings if isinstance(vendor.settings, dict) else {}
    branding = settings.get("branding") or {}
    features = settings.get("features") or {}
    return success(
        "Vendor",
        {
            "vendor_id": vendor.id,
            "slug": vendor.slug,
            "name": vendor.name,
            "legal_name": vendor.legal_name,
            "address": vendor.address,
            "gstin": vendor.gstin,
            "currency": vendor.currency,
            "store_enabled": store_enabled(vendor),
            "branding": {
                "logo_url": branding.get("logo_url") or "",
                "primary": branding.get("primary") or "#D4AF7C",
                "theme_id": branding.get("theme_id") or "matte_gold",
                "store_name": branding.get("store_name") or vendor.name,
                "company_blurb": branding.get("company_blurb") or "",
                "company_tagline": branding.get("company_tagline") or "",
            },
            "features": {
                "cod": bool(features.get("cod", True)),
                "razorpay": bool(features.get("razorpay", True)),
                "reviews": bool(features.get("reviews", True)),
            },
        },
    )


@router.get("/products")
def public_products(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    vctx: VendorContext = Depends(get_vendor_ctx),
    db: Session = Depends(get_db),
):
    """Product info list (not cart). ACTIVE + sellable."""
    vendor = _require_vendor(vctx)
    q = select(Item).where(
        Item.vendor_id == vendor.id,
        Item.status == "ACTIVE",
        Item.is_sellable.is_(True),
    )
    if search:
        like = f"%{search}%"
        q = q.where(or_(Item.name.ilike(like), Item.code.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(Item.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return success(
        "Products",
        {
            "data": [row(i, PRODUCT_FIELDS + ["is_online_sale"]) for i in rows],
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size if page_size else 0,
            },
            "store_enabled": store_enabled(vendor),
        },
    )


@router.get("/products/{item_id}")
def public_product(
    item_id: int,
    vctx: VendorContext = Depends(get_vendor_ctx),
    db: Session = Depends(get_db),
):
    vendor = _require_vendor(vctx)
    it = db.get(Item, item_id)
    if not it or it.vendor_id != vendor.id or it.status != "ACTIVE" or not it.is_sellable:
        return error("Product not found", status_code=404)
    images = db.scalars(
        select(ItemImage).where(ItemImage.item_id == item_id).order_by(ItemImage.sort_order, ItemImage.id)
    ).all()
    d = row(it, PRODUCT_FIELDS + ["is_online_sale", "description"])
    d["images"] = [row(img, ["id", "path", "sort_order", "is_primary"]) for img in images]
    d["store_enabled"] = store_enabled(vendor)
    return success("Product", d)
