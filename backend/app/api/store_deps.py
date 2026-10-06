"""Dependencies for /api/store/* — vendor context + store_enabled gate."""

from fastapi import Depends, HTTPException

from app.api.deps import AuthUser, get_current_user, get_vendor_ctx
from app.core.vendor_context import VendorContext
from app.models import Vendor
from app.services.checkout import store_enabled


def require_store_vendor(
    vctx: VendorContext = Depends(get_vendor_ctx),
) -> Vendor:
    if not vctx.vendor or not vctx.vendor_id:
        raise HTTPException(status_code=400, detail="Vendor context required (x-vendor-slug)")
    if vctx.vendor.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Vendor inactive")
    if not store_enabled(vctx.vendor):
        raise HTTPException(status_code=403, detail="Store is disabled")
    return vctx.vendor


def require_store_user(
    user: AuthUser = Depends(get_current_user),
    vendor: Vendor = Depends(require_store_vendor),
) -> tuple[AuthUser, Vendor]:
    from app.core.permissions import permission_implies

    if user.role == "SUPER_ADMIN":
        return user, vendor
    if user.vendor_id and user.vendor_id != vendor.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not permission_implies(user.permissions, "ecommerce.store.read"):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user, vendor


def require_account_user(
    user: AuthUser = Depends(get_current_user),
    vctx: VendorContext = Depends(get_vendor_ctx),
) -> tuple[AuthUser, Vendor]:
    """Logged-in party account (orders/invoice) — storefront may be disabled."""
    from app.core.permissions import permission_implies

    if not vctx.vendor or not vctx.vendor_id:
        raise HTTPException(status_code=400, detail="Vendor context required (x-vendor-slug)")
    if vctx.vendor.status != "ACTIVE":
        raise HTTPException(status_code=403, detail="Vendor inactive")
    if user.role == "SUPER_ADMIN":
        return user, vctx.vendor
    if user.vendor_id and user.vendor_id != vctx.vendor.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if not (
        permission_implies(user.permissions, "ecommerce.store.read")
        or permission_implies(user.permissions, "b2b.orders.read")
    ):
        raise HTTPException(status_code=403, detail="Forbidden")
    return user, vctx.vendor
