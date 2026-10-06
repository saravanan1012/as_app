from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.user import User

DEFAULT_VENDOR_SETTINGS: dict[str, Any] = {
    "branding": {
        "logo_url": "",
        "primary": "#D4AF7C",
        "theme_id": "matte_gold",
        "store_name": "",
        "company_blurb": "",
        "company_tagline": "",
    },
    "features": {
        "store_enabled": False,
        "cod": True,
        "razorpay": True,
        "reviews": True,
    },
    "payments": {"razorpay_key_id": "", "razorpay_key_secret_ref": ""},
    "shipping": {
        "flat_rate": 0,
        "free_over": None,
        "qty_tiers": [],
        "couriers": ["AKR_PARCEL", "MARUTHI_PARCEL"],
    },
    "limits": {"max_items": 5000, "max_staff": 20},
    "tax": {"gstin": "", "state_code": ""},
    "locale": {"currency": "INR", "timezone": "Asia/Kolkata"},
}


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE", nullable=False)
    plan: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    state_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    default_location_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    users: Mapped[list[User]] = relationship("User", back_populates="vendor")
