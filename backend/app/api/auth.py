from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser, default_redirect, get_current_user, get_vendor_ctx
from app.config import get_settings
from app.core.responses import error, success
from app.core.security import create_access_token, verify_password
from app.core.vendor_context import VendorContext
from app.db import get_db
from app.models import User
from app.schemas.auth import LoginRequest, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_payload(user: User, permissions: set[str], store_enabled: bool = False) -> dict:
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        vendor_id=user.vendor_id,
        permissions=sorted(permissions),
        default_redirect=default_redirect(permissions, store_enabled=store_enabled),
    ).model_dump()


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    email = body.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(body.password, user.password):
        return error("Invalid credentials", status_code=401)
    if user.status != "ACTIVE":
        return error("Account inactive", status_code=403)

    from app.api.deps import _load_permissions

    permissions = _load_permissions(db, user.role)
    store_enabled = False
    if user.vendor_id:
        from app.models import Vendor

        vendor = db.get(Vendor, user.vendor_id)
        if vendor and isinstance(vendor.settings, dict):
            store_enabled = bool(vendor.settings.get("features", {}).get("store_enabled"))

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
            "vendor_id": user.vendor_id,
        }
    )
    payload = _user_payload(user, permissions, store_enabled)
    resp = JSONResponse(
        status_code=200,
        content={"success": True, "message": "Logged in", "data": payload},
    )
    resp.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return resp


@router.post("/logout")
def logout():
    settings = get_settings()
    resp = JSONResponse(
        status_code=200,
        content={"success": True, "message": "Logged out", "data": None},
    )
    resp.delete_cookie(settings.cookie_name, path="/")
    return resp


@router.get("/me")
def me(
    user: AuthUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    vctx: VendorContext = Depends(get_vendor_ctx),
):
    store_enabled = False
    if vctx.vendor and isinstance(vctx.vendor.settings, dict):
        store_enabled = bool(vctx.vendor.settings.get("features", {}).get("store_enabled"))
    db_user = db.get(User, user.id)
    if not db_user:
        return error("Unauthorized", status_code=401)
    return success(
        "OK",
        _user_payload(db_user, user.permissions, store_enabled),
    )
