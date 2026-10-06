from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser
from app.api.serialize import row
from app.api.vendor_scope import perm
from app.core.responses import error, success
from app.core.security import hash_password
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])
FIELDS = ["id", "email", "name", "role", "status", "vendor_id", "phone"]
STAFF_ROLES = {"ADMIN", "MANAGER", "STAFF"}


class UserIn(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    role: str = "STAFF"
    phone: str | None = None
    status: str = "ACTIVE"


class UserPatch(BaseModel):
    name: str | None = None
    role: str | None = None
    phone: str | None = None
    status: str | None = None
    password: str | None = Field(default=None, min_length=8)


@router.get("")
def list_users(ctx: tuple[AuthUser, int] = Depends(perm("users.read")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    rows = db.scalars(select(User).where(User.vendor_id == vendor_id).order_by(User.id)).all()
    return success("Users fetched", [row(u, FIELDS) for u in rows])


@router.post("")
def create_user(body: UserIn, ctx: tuple[AuthUser, int] = Depends(perm("users.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    role = body.role.upper()
    if role not in STAFF_ROLES:
        return error("Invalid role for vendor user", status_code=400)
    email = str(body.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        return error("Email already exists", status_code=409)
    u = User(
        email=email,
        name=body.name.strip(),
        role=role,
        status=body.status.upper(),
        phone=body.phone,
        vendor_id=vendor_id,
        password=hash_password(body.password),
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return success("Created", row(u, FIELDS), status_code=201)


@router.patch("/{user_id}")
def patch_user(user_id: int, body: UserPatch, ctx: tuple[AuthUser, int] = Depends(perm("users.write")), db: Session = Depends(get_db)):
    _, vendor_id = ctx
    u = db.get(User, user_id)
    if not u or u.vendor_id != vendor_id:
        return error("Not found", status_code=404)
    data = body.model_dump(exclude_unset=True)
    if "role" in data and data["role"]:
        role = data["role"].upper()
        if role not in STAFF_ROLES:
            return error("Invalid role", status_code=400)
        data["role"] = role
    if "status" in data and data["status"]:
        data["status"] = data["status"].upper()
    if "password" in data and data["password"]:
        data["password"] = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(u, k, v)
    db.commit()
    db.refresh(u)
    return success("Updated", row(u, FIELDS))
