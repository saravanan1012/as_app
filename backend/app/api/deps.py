from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.permissions import permission_implies
from app.core.security import decode_access_token
from app.core.vendor_context import VendorContext, resolve_vendor_context
from app.db import get_db
from app.models import Permission, RolePermission, User


@dataclass
class AuthUser:
    id: int
    email: str
    name: str
    role: str
    vendor_id: int | None
    permissions: set[str]


def _load_permissions(db: Session, role: str) -> set[str]:
    rows = db.execute(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role == role)
    ).scalars().all()
    return set(rows)


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> AuthUser | None:
    settings = get_settings()
    token = request.cookies.get(settings.cookie_name)
    if not token:
        auth = request.headers.get("Authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth[7:].strip()
    if not token:
        return None
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    user = db.get(User, int(payload["sub"]))
    if not user or user.status != "ACTIVE":
        return None
    perms = _load_permissions(db, user.role)
    return AuthUser(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        vendor_id=user.vendor_id,
        permissions=perms,
    )


def get_current_user(
    user: AuthUser | None = Depends(get_current_user_optional),
) -> AuthUser:
    if not user:
        # Raise via HTTPException pattern — use FastAPI HTTPException
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


def get_vendor_ctx(
    request: Request,
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_current_user_optional),
) -> VendorContext:
    return resolve_vendor_context(
        db,
        request,
        user_vendor_id=user.vendor_id if user else None,
        is_super_admin=bool(user and user.role == "SUPER_ADMIN"),
    )


def require_permission(code: str):
    def _dep(user: AuthUser = Depends(get_current_user)) -> AuthUser:
        from fastapi import HTTPException

        if not permission_implies(user.permissions, code):
            raise HTTPException(status_code=403, detail="Forbidden")
        return user

    return _dep


def default_redirect(permissions: set[str], store_enabled: bool = False) -> str:
    if permission_implies(permissions, "platform.vendors.manage"):
        return "/platform"
    has_sales_w = permission_implies(permissions, "sales.orders.write")
    has_purchase_w = permission_implies(permissions, "purchase.orders.write")
    if has_sales_w and not has_purchase_w:
        return "/admin/sales-orders"
    if has_purchase_w and not has_sales_w:
        return "/admin/purchase-orders"
    if has_sales_w or has_purchase_w or permission_implies(permissions, "dashboard.read"):
        return "/admin/sales-orders"
    # Trade roles have b2b.portal without admin dashboard
    if permission_implies(permissions, "b2b.portal"):
        return "/b2b"
    if store_enabled:
        return "/store"
    if permission_implies(permissions, "ecommerce.store.read"):
        return "/store/orders"
    return "/"
