from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

ThemeId = Literal["matte_gold", "rose_gold", "deep_gold", "vibrant_gold"]
VendorStatus = Literal["ACTIVE", "SUSPENDED", "DRAFT"]


class BrandingSettings(BaseModel):
    logo_url: str | None = None
    primary: str | None = None
    theme_id: ThemeId | None = None
    store_name: str | None = None
    company_blurb: str | None = None
    company_tagline: str | None = None


class FeaturesSettings(BaseModel):
    store_enabled: bool | None = None
    cod: bool | None = None
    razorpay: bool | None = None
    reviews: bool | None = None


class PaymentsSettings(BaseModel):
    razorpay_key_id: str | None = None
    razorpay_key_secret_ref: str | None = None


class ShippingSettings(BaseModel):
    flat_rate: float | None = None
    free_over: float | None = None


class LimitsSettings(BaseModel):
    max_items: int | None = None
    max_staff: int | None = None


class TaxSettings(BaseModel):
    gstin: str | None = None
    state_code: str | None = None


class LocaleSettings(BaseModel):
    currency: str | None = None
    timezone: str | None = None


class VendorSettingsPatch(BaseModel):
    branding: BrandingSettings | None = None
    features: FeaturesSettings | None = None
    payments: PaymentsSettings | None = None
    shipping: ShippingSettings | None = None
    limits: LimitsSettings | None = None
    tax: TaxSettings | None = None
    locale: LocaleSettings | None = None


class StoreToggle(BaseModel):
    store_enabled: bool


class VendorCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=80)
    plan: str | None = None
    gstin: str | None = None
    state_code: str | None = None
    legal_name: str | None = None
    address: str | None = None
    settings: VendorSettingsPatch | None = None
    # Optional first admin at create time
    admin_email: EmailStr | None = None
    admin_name: str | None = None
    admin_password: str | None = Field(default=None, min_length=8)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, v: str) -> str:
        s = v.strip().lower().replace(" ", "-")
        if not s.replace("-", "").isalnum():
            raise ValueError("slug must be alphanumeric with hyphens")
        return s


class VendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    plan: str | None = None
    status: VendorStatus | None = None
    gstin: str | None = None
    state_code: str | None = None
    legal_name: str | None = None
    address: str | None = None
    timezone: str | None = None
    currency: str | None = None
    default_location_id: int | None = None


class BootstrapAdmin(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8)
    role: Literal["ADMIN", "MANAGER"] = "ADMIN"


def vendor_public_dict(v: Any) -> dict:
    settings = v.settings if isinstance(v.settings, dict) else {}
    features = settings.get("features") or {}
    branding = settings.get("branding") or {}
    return {
        "id": v.id,
        "name": v.name,
        "slug": v.slug,
        "status": v.status,
        "plan": v.plan,
        "gstin": v.gstin,
        "state_code": v.state_code,
        "legal_name": v.legal_name,
        "address": v.address,
        "timezone": v.timezone,
        "currency": v.currency,
        "default_location_id": v.default_location_id,
        "settings": settings,
        "store_enabled": bool(features.get("store_enabled")),
        "theme_id": branding.get("theme_id") or "matte_gold",
        "suspended_at": v.suspended_at.isoformat() if v.suspended_at else None,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }
