"""Resolve vendor_id for staff APIs (required)."""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import AuthUser, get_current_user, get_vendor_ctx, require_permission
from app.core.vendor_context import VendorContext
from app.db import get_db


def require_vendor_id(
    user: AuthUser = Depends(get_current_user),
    vctx: VendorContext = Depends(get_vendor_ctx),
) -> int:
    """Staff must operate in a vendor; SUPER_ADMIN passes ?vendor_id=."""
    if vctx.vendor_id:
        # Non-super staff cannot escape their vendor
        if user.role != "SUPER_ADMIN" and user.vendor_id and user.vendor_id != vctx.vendor_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        if user.role != "SUPER_ADMIN" and user.vendor_id:
            return user.vendor_id
        return vctx.vendor_id
    if user.vendor_id:
        return user.vendor_id
    raise HTTPException(status_code=400, detail="vendor_id required (query or session)")


def perm(code: str):
    """Compose permission + vendor scope."""

    def _dep(
        user: AuthUser = Depends(require_permission(code)),
        vendor_id: int = Depends(require_vendor_id),
    ) -> tuple[AuthUser, int]:
        return user, vendor_id

    return _dep
