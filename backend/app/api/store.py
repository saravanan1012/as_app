"""Public Store APIs — gated on vendors.settings.features.store_enabled."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import AuthUser, get_current_user_optional
from app.api.serialize import row
from app.api.store_deps import require_account_user, require_store_user, require_store_vendor
from app.config import get_settings
from app.core.responses import error, success
from app.core.security import create_access_token, hash_password
from app.db import get_db
from app.models import Customer, Item, ItemImage, User, Vendor
from app.models.ecommerce import ItemReview
from app.models.orders import SaleOrder, SaleOrderDetail
from app.services.checkout import (
    CheckoutError,
    available_qty,
    checkout_cod,
    checkout_razorpay_create,
    checkout_razorpay_verify,
    find_or_create_customer,
    handle_razorpay_webhook,
)
from app.services.offers_eval import OfferError, validate_offer
from app.services.razorpay_client import mock_signature

router = APIRouter(prefix="/store", tags=["store"])

PRODUCT_FIELDS = [
    "id", "code", "name", "description", "unit_of_measure", "sale_price",
    "category", "primary_image", "sale_price_includes_gst", "tax_category_id",
]


class AddressIn(BaseModel):
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    phone: str | None = None
    name: str | None = None


class CartItemIn(BaseModel):
    item_id: int
    quantity: int = Field(gt=0)
    location_id: int | None = None


class CheckoutIn(BaseModel):
    items: list[CartItemIn]
    address: AddressIn | None = None
    offer_code: str | None = None


class OfferValidateIn(BaseModel):
    code: str
    subtotal: float = Field(ge=0)
    item_ids: list[int] | None = None


class VerifyIn(BaseModel):
    order_code: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class ReviewIn(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)
    name: str = Field(min_length=1, max_length=100)


@router.post("/auth/register")
def store_register(
    body: RegisterIn,
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
):
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        return error("Email already registered", status_code=409)
    user = User(
        email=email,
        name=body.name.strip(),
        role="CUSTOMER",
        status="ACTIVE",
        vendor_id=vendor.id,
        password=hash_password(body.password),
    )
    db.add(user)
    db.flush()
    find_or_create_customer(
        db, vendor_id=vendor.id, user_id=user.id, email=email, name=body.name.strip()
    )
    db.commit()
    db.refresh(user)

    settings = get_settings()
    token = create_access_token(
        {"sub": str(user.id), "role": user.role, "vendor_id": user.vendor_id}
    )
    resp = JSONResponse(
        status_code=201,
        content={
            "success": True,
            "message": "Registered",
            "data": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "vendor_id": user.vendor_id,
            },
        },
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


@router.get("/meta")
def store_meta(vendor: Vendor = Depends(require_store_vendor)):
    settings = vendor.settings if isinstance(vendor.settings, dict) else {}
    branding = settings.get("branding") or {}
    features = settings.get("features") or {}
    return success(
        "Store meta",
        {
            "vendor_id": vendor.id,
            "slug": vendor.slug,
            "name": vendor.name,
            "store_name": branding.get("store_name") or vendor.name,
            "theme_id": branding.get("theme_id") or "matte_gold",
            "primary": branding.get("primary"),
            "logo_url": branding.get("logo_url"),
            "features": {
                "cod": bool(features.get("cod", True)),
                "razorpay": bool(features.get("razorpay", True)),
                "reviews": bool(features.get("reviews", True)),
            },
            "currency": vendor.currency,
        },
    )


@router.get("/products")
def list_products(
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
):
    q = select(Item).where(
        Item.vendor_id == vendor.id,
        Item.status == "ACTIVE",
        Item.is_sellable.is_(True),
        Item.is_online_sale.is_(True),
    )
    if search:
        like = f"%{search}%"
        q = q.where(or_(Item.name.ilike(like), Item.code.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = db.scalars(q.order_by(Item.id.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    data = []
    for it in rows:
        d = row(it, PRODUCT_FIELDS)
        d["available_qty"] = available_qty(
            db, vendor_id=vendor.id, item_id=it.id, location_id=vendor.default_location_id
        )
        data.append(d)
    return success(
        "Products",
        {
            "data": data,
            "pagination": {
                "page": page,
                "pageSize": page_size,
                "total": total,
                "totalPages": (total + page_size - 1) // page_size if page_size else 0,
            },
        },
    )


@router.get("/products/{item_id}")
def get_product(
    item_id: int,
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
):
    it = db.get(Item, item_id)
    if (
        not it
        or it.vendor_id != vendor.id
        or it.status != "ACTIVE"
        or not it.is_sellable
        or not it.is_online_sale
    ):
        return error("Product not found", status_code=404)
    images = db.scalars(
        select(ItemImage).where(ItemImage.item_id == item_id).order_by(ItemImage.sort_order, ItemImage.id)
    ).all()
    d = row(it, PRODUCT_FIELDS)
    d["available_qty"] = available_qty(
        db, vendor_id=vendor.id, item_id=it.id, location_id=vendor.default_location_id
    )
    d["images"] = [row(img, ["id", "path", "sort_order", "is_primary"]) for img in images]
    return success("Product", d)


@router.post("/offers/validate")
def validate_store_offer(
    body: OfferValidateIn,
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
    user: AuthUser | None = Depends(get_current_user_optional),
):
    customer_id = None
    party_type = "CUSTOMER"
    if user:
        from app.models import Customer

        c = db.scalar(
            select(Customer).where(Customer.vendor_id == vendor.id, Customer.user_id == user.id)
        )
        if c:
            customer_id = c.id
            party_type = c.party_type
    try:
        result = validate_offer(
            db,
            vendor_id=vendor.id,
            code=body.code,
            subtotal=body.subtotal,
            party_type=party_type,
            sales_channel="ECOMMERCE",
            customer_id=customer_id,
            item_ids=body.item_ids,
        )
    except OfferError as e:
        return error(str(e), status_code=400)
    return success("Offer valid", result)


@router.post("/checkout/cod")
def store_checkout_cod(
    body: CheckoutIn,
    ctx: tuple[AuthUser, Vendor] = Depends(require_store_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    try:
        so = checkout_cod(
            db,
            vendor=vendor,
            user_id=user.id,
            email=user.email,
            name=user.name,
            items=[i.model_dump() for i in body.items],
            address=body.address.model_dump() if body.address else None,
            offer_code=body.offer_code,
        )
        db.commit()
        db.refresh(so)
    except CheckoutError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success(
        "Order placed",
        {
            "order_code": so.order_code,
            "sale_order_id": so.id,
            "payment_status": so.payment_status,
            "total_order_value": float(so.total_order_value),
        },
        status_code=201,
    )


@router.post("/checkout/razorpay/create")
def store_razorpay_create(
    body: CheckoutIn,
    ctx: tuple[AuthUser, Vendor] = Depends(require_store_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    try:
        data = checkout_razorpay_create(
            db,
            vendor=vendor,
            user_id=user.id,
            email=user.email,
            name=user.name,
            items=[i.model_dump() for i in body.items],
            address=body.address.model_dump() if body.address else None,
            offer_code=body.offer_code,
        )
        db.commit()
    except CheckoutError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Razorpay order created", data, status_code=201)


@router.post("/checkout/razorpay/verify")
def store_razorpay_verify(
    body: VerifyIn,
    ctx: tuple[AuthUser, Vendor] = Depends(require_store_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    try:
        so = checkout_razorpay_verify(
            db,
            vendor=vendor,
            order_code=body.order_code,
            razorpay_order_id=body.razorpay_order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            razorpay_signature=body.razorpay_signature,
            created_by=user.email,
        )
        db.commit()
        db.refresh(so)
    except CheckoutError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success(
        "Payment recorded",
        {
            "order_code": so.order_code,
            "payment_status": so.payment_status,
            "sale_order_id": so.id,
        },
    )


@router.post("/checkout/razorpay/webhook")
async def store_razorpay_webhook(
    request: Request,
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
):
    body = await request.body()
    signature = request.headers.get("x-razorpay-signature") or ""
    try:
        result = handle_razorpay_webhook(db, vendor=vendor, body=body, signature=signature)
        db.commit()
    except CheckoutError as e:
        db.rollback()
        return error(str(e), status_code=400)
    return success("Webhook processed", result)


@router.get("/checkout/razorpay/mock-sign")
def mock_sign_helper(
    order_id: str,
    payment_id: str,
    vendor: Vendor = Depends(require_store_vendor),
):
    """Dev/CI helper — only useful when razorpay_mock is on."""
    from app.config import get_settings

    if not get_settings().razorpay_mock:
        return error("Not available", status_code=404)
    return success("OK", {"signature": mock_signature(order_id, payment_id, "mock-secret")})


@router.get("/products/{item_id}/reviews")
def list_reviews(
    item_id: int,
    vendor: Vendor = Depends(require_store_vendor),
    db: Session = Depends(get_db),
):
    feats = (vendor.settings or {}).get("features") or {}
    if not feats.get("reviews", True):
        return error("Reviews disabled", status_code=403)
    rows = db.scalars(
        select(ItemReview)
        .where(ItemReview.vendor_id == vendor.id, ItemReview.item_id == item_id)
        .order_by(ItemReview.id.desc())
        .limit(100)
    ).all()
    return success(
        "Reviews",
        [
            row(r, ["id", "rating", "comment", "is_verified_purchase", "customer_id", "created_at"])
            for r in rows
        ],
    )


@router.post("/products/{item_id}/reviews")
def create_review(
    item_id: int,
    body: ReviewIn,
    ctx: tuple[AuthUser, Vendor] = Depends(require_store_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    feats = (vendor.settings or {}).get("features") or {}
    if not feats.get("reviews", True):
        return error("Reviews disabled", status_code=403)
    it = db.get(Item, item_id)
    if not it or it.vendor_id != vendor.id:
        return error("Product not found", status_code=404)

    from app.models import Customer

    customer = db.scalar(
        select(Customer).where(Customer.vendor_id == vendor.id, Customer.user_id == user.id)
    )
    verified = False
    if customer:
        bought = db.scalar(
            select(SaleOrderDetail.id)
            .join(SaleOrder, SaleOrder.id == SaleOrderDetail.sale_order_id)
            .where(
                SaleOrder.vendor_id == vendor.id,
                SaleOrder.customer_id == customer.id,
                SaleOrder.status.in_(("CONFIRMED", "RETURNED")),
                SaleOrderDetail.item_id == item_id,
            )
            .limit(1)
        )
        verified = bought is not None

    existing = None
    if customer:
        existing = db.scalar(
            select(ItemReview).where(
                ItemReview.vendor_id == vendor.id,
                ItemReview.item_id == item_id,
                ItemReview.customer_id == customer.id,
            )
        )
    if existing:
        existing.rating = body.rating
        existing.comment = body.comment
        existing.is_verified_purchase = verified
        db.commit()
        db.refresh(existing)
        return success("Updated", row(existing, ["id", "rating", "comment", "is_verified_purchase"]))

    rev = ItemReview(
        vendor_id=vendor.id,
        item_id=item_id,
        customer_id=customer.id if customer else None,
        user_id=user.id,
        rating=body.rating,
        comment=body.comment,
        is_verified_purchase=verified,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return success(
        "Created",
        row(rev, ["id", "rating", "comment", "is_verified_purchase"]),
        status_code=201,
    )


@router.get("/my-orders")
def my_orders(
    ctx: tuple[AuthUser, Vendor] = Depends(require_account_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    from app.models import Customer
    from app.services.pricing import courier_label

    customer = db.scalar(
        select(Customer).where(Customer.vendor_id == vendor.id, Customer.user_id == user.id)
    )
    if not customer:
        return success("Orders", {"data": []})
    rows = db.scalars(
        select(SaleOrder)
        .where(
            SaleOrder.vendor_id == vendor.id,
            SaleOrder.customer_id == customer.id,
        )
        .order_by(SaleOrder.id.desc())
        .limit(50)
    ).all()
    data = []
    for s in rows:
        r = row(
            s,
            [
                "id",
                "order_code",
                "order_date",
                "status",
                "payment_status",
                "fulfillment_status",
                "total_order_value",
                "courier",
                "tracking_number",
                "shipped_at",
                "sales_channel",
                "created_at",
            ],
        )
        r["courier_label"] = courier_label(s.courier)
        data.append(r)
    return success("Orders", {"data": data})


@router.get("/my-orders/{so_id}")
def my_order_detail(
    so_id: int,
    ctx: tuple[AuthUser, Vendor] = Depends(require_account_user),
    db: Session = Depends(get_db),
):
    user, vendor = ctx
    from app.models import Customer
    from app.services.pricing import courier_label

    customer = db.scalar(
        select(Customer).where(Customer.vendor_id == vendor.id, Customer.user_id == user.id)
    )
    if not customer:
        return error("Not found", status_code=404)
    so = db.get(SaleOrder, so_id)
    if not so or so.vendor_id != vendor.id or so.customer_id != customer.id:
        return error("Not found", status_code=404)
    details = db.scalars(
        select(SaleOrderDetail).where(SaleOrderDetail.sale_order_id == so.id)
    ).all()
    payload = row(
        so,
        [
            "id",
            "order_code",
            "order_date",
            "status",
            "payment_status",
            "fulfillment_status",
            "total_gross_amount",
            "total_discount_amount",
            "total_net_amount",
            "total_tax_amount",
            "shipping_charge",
            "total_order_value",
            "courier",
            "tracking_number",
            "shipped_at",
            "invoice_number",
            "shipping_name",
            "shipping_street",
            "shipping_city",
            "shipping_state",
            "shipping_zip",
            "sales_channel",
            "created_at",
        ],
    )
    payload["courier_label"] = courier_label(so.courier)
    payload["items"] = [
        row(
            d,
            [
                "id",
                "item_id",
                "item_code",
                "item_name",
                "quantity",
                "unit_price",
                "net_line_total",
                "gst_rate",
                "gst_amount",
            ],
        )
        for d in details
    ]
    return success("Order", payload)
