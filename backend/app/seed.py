"""Seed permissions, role grants, 2 vendors, SUPER_ADMIN + vendor admins + demo catalog + B2B."""

import re
import shutil
from copy import deepcopy
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session, attributes

from app.core.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.core.storage import vendor_item_storage
from app.models import (
    DEFAULT_VENDOR_SETTINGS,
    Customer,
    Item,
    ItemImage,
    ItemReview,
    Location,
    PartyPriceRule,
    Permission,
    RolePermission,
    SaleOrder,
    Stock,
    TaxCategory,
    User,
    Vendor,
)


SEED_PASSWORD = "User@123"

# Size folders under seed_assets/napkins/ (M is placeholder until real images are added)
NAPKIN_ITEMS = [
    {
        "code": "NAPKIN-M",
        "folder": "M",
        "name": "M Napkins",
        "description": (
            "AS Organic sanitary napkins — Medium. Soft cotton cover, secure wings, "
            "and everyday absorbency for regular flow. Breathable and skin-friendly."
        ),
        "sale_price": 179,
        "cost_price": 90,
        "category": "NAPKINS",
        "is_online_sale": True,
        "qty": 120,
    },
    {
        "code": "NAPKIN-L",
        "folder": "L",
        "name": "L Napkins",
        "description": (
            "AS Organic sanitary napkins — Large. Extra length and coverage for comfort "
            "through the day. Anion strip support with a cotton-feel top sheet."
        ),
        "sale_price": 199,
        "cost_price": 100,
        "category": "NAPKINS",
        "is_online_sale": True,
        "qty": 120,
    },
    {
        "code": "NAPKIN-XL",
        "folder": "XL",
        "name": "XL Napkins",
        "description": (
            "AS Organic sanitary napkins — XL. Wider wings and higher absorbency for "
            "heavier days. Leak-guard edges for confident all-day wear."
        ),
        "sale_price": 229,
        "cost_price": 115,
        "category": "NAPKINS",
        "is_online_sale": True,
        "qty": 100,
    },
    {
        "code": "NAPKIN-XXL",
        "folder": "XXL",
        "name": "XXL Napkins",
        "description": (
            "AS Organic sanitary napkins — XXL. Maximum daytime coverage with a soft "
            "pouch-ready pack. Ideal when you want longer wear and full protection."
        ),
        "sale_price": 259,
        "cost_price": 130,
        "category": "NAPKINS",
        "is_online_sale": True,
        "qty": 100,
    },
    {
        "code": "NAPKIN-XXXL",
        "folder": "XXXL",
        "name": "XXXL Napkins",
        "description": (
            "AS Organic sanitary napkins — XXXL. Our largest size for overnight and "
            "extra-heavy flow. Thick core, secure fit, and gentle organic materials."
        ),
        "sale_price": 289,
        "cost_price": 145,
        "category": "NAPKINS",
        "is_online_sale": True,
        "qty": 80,
    },
]

NAPKIN_CODES = {spec["code"] for spec in NAPKIN_ITEMS}

# Trade discounts applied to every NAPKIN-* item (party_type → % off MSRP)
TRADE_PRICE_PCT = {
    "DISTRIBUTOR": 30,
    "DEALER": 20,
    "RETAILER": 10,
}

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def _napkin_assets_root() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "seed_assets" / "napkins",
        Path("/app/seed_assets/napkins"),
    ]
    for path in candidates:
        if path.is_dir():
            return path
    return candidates[0]


def _media_url(rel_path: str) -> str:
    return f"/api/media/{rel_path.lstrip('/')}"


def _safe_image_name(src: Path, index: int) -> str:
    ext = src.suffix.lower() if src.suffix.lower() in _IMAGE_EXTS else ".jpeg"
    stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", src.stem).strip("-").lower() or f"img-{index:02d}"
    return f"{index:02d}-{stem[:40]}{ext}"

# Full demo tree: key → (email, display name, party_type, parent_key|None, phone)
# Password for all linked users: User@123
B2B_PARTY_SPECS: list[tuple[str, str, str, str, str | None, str]] = [
    # key, email, name, party_type, parent_key, phone
    ("dist1", "distributor@as.com", "Chennai Distributor", "DISTRIBUTOR", None, "9000000001"),
    ("dist2", "distributor2@as.com", "Coimbatore Distributor", "DISTRIBUTOR", None, "9000000002"),
    ("deal1", "dealer@as.com", "Anna Nagar Dealer", "DEALER", "dist1", "9000000011"),
    ("deal2", "dealer2@as.com", "T Nagar Dealer", "DEALER", "dist1", "9000000012"),
    ("deal3", "dealer3@as.com", "Coimbatore Dealer", "DEALER", "dist2", "9000000013"),
    ("ret1", "retailer@as.com", "Pondy Bazaar Retailer", "RETAILER", "deal1", "9000000021"),
    ("ret2", "retailer2@as.com", "Adyar Retailer", "RETAILER", "deal1", "9000000022"),
    ("ret3", "retailer3@as.com", "RS Puram Retailer", "RETAILER", "deal3", "9000000023"),
    ("cust1", "retail-customer@as.com", "Priya End Customer", "CUSTOMER", "ret1", "9000000031"),
    ("cust2", "customer2@as.com", "Karthik End Customer", "CUSTOMER", "ret1", "9000000032"),
    ("cust3", "customer3@as.com", "Meena End Customer", "CUSTOMER", "ret2", "9000000033"),
    ("direct", "direct@as.com", "Walk-in Direct Customer", "CUSTOMER", None, "9000000040"),
]


def seed_permissions(db: Session) -> None:
    existing = {p.code: p for p in db.scalars(select(Permission)).all()}
    for code, desc in ALL_PERMISSIONS:
        if code not in existing:
            db.add(Permission(code=code, description=desc))
    db.flush()

    code_to_id = {p.code: p.id for p in db.scalars(select(Permission)).all()}
    existing_rp = {
        (rp.role, rp.permission_id)
        for rp in db.scalars(select(RolePermission)).all()
    }
    for role, codes in ROLE_PERMISSIONS.items():
        for code in codes:
            pid = code_to_id.get(code)
            if pid and (role, pid) not in existing_rp:
                db.add(RolePermission(role=role, permission_id=pid))
    db.commit()


def seed_vendors_and_users(db: Session) -> None:
    vendors_spec = [
        ("AS Organic Demo", "as-demo", "BASIC"),
        ("Second Vendor", "vendor-two", "BASIC"),
    ]
    for name, slug, plan in vendors_spec:
        vendor = db.scalar(select(Vendor).where(Vendor.slug == slug))
        if not vendor:
            settings = deepcopy(DEFAULT_VENDOR_SETTINGS)
            if slug == "as-demo":
                settings["branding"] = {
                    **settings["branding"],
                    "store_name": "AS Organic",
                    "company_tagline": "Pure botanicals for everyday rituals",
                    "company_blurb": (
                        "AS Organic crafts plant-based essentials with care — "
                        "from farm-sourced ingredients to small-batch finishing."
                    ),
                    "theme_id": "matte_gold",
                    "primary": "#D4AF7C",
                }
                settings["shipping"] = {
                    "ecommerce": {
                        "enabled": True,
                        "flat_rate": 80,
                        "free_over_enabled": True,
                        "free_over": 500,
                    },
                    "b2b": {
                        "qty_tiers": [
                            {"max_qty": 2, "charge": 80},
                            {"max_qty": 9, "charge": 40},
                            {"max_qty": None, "charge": 0},
                        ],
                    },
                    "couriers": ["AKR_PARCEL", "MARUTHI_PARCEL"],
                }
                settings.setdefault("features", {})["store_enabled"] = True
            vendor = Vendor(
                name=name,
                slug=slug,
                plan=plan,
                status="ACTIVE",
                settings=settings,
                state_code="TN",
            )
            db.add(vendor)
            db.flush()
        elif slug == "as-demo":
            branding = (vendor.settings or {}).get("branding") or {}
            s = deepcopy(vendor.settings or DEFAULT_VENDOR_SETTINGS)
            changed = False
            if not branding.get("company_tagline"):
                s.setdefault("branding", {})
                s["branding"].update(
                    {
                        "store_name": s["branding"].get("store_name") or "AS Organic",
                        "company_tagline": "Pure botanicals for everyday rituals",
                        "company_blurb": (
                            "AS Organic crafts plant-based essentials with care — "
                            "from farm-sourced ingredients to small-batch finishing."
                        ),
                        "theme_id": "matte_gold",
                        "primary": "#D4AF7C",
                    }
                )
                changed = True
            ship = s.setdefault("shipping", {})
            if "ecommerce" not in ship:
                ship["ecommerce"] = {
                    "enabled": True,
                    "flat_rate": float(ship.get("flat_rate") or 80),
                    "free_over_enabled": True,
                    "free_over": float(ship["free_over"])
                    if ship.get("free_over") is not None
                    else 500,
                }
                changed = True
            b2b_ship = ship.setdefault("b2b", {})
            if not b2b_ship.get("qty_tiers"):
                legacy_tiers = ship.get("qty_tiers") or [
                    {"max_qty": 2, "charge": 80},
                    {"max_qty": 9, "charge": 40},
                    {"max_qty": None, "charge": 0},
                ]
                b2b_ship["qty_tiers"] = legacy_tiers
                changed = True
            if not ship.get("couriers"):
                ship["couriers"] = ["AKR_PARCEL", "MARUTHI_PARCEL"]
                changed = True
            feats = s.setdefault("features", {})
            if not feats.get("store_enabled"):
                feats["store_enabled"] = True
                changed = True
            if changed:
                vendor.settings = s
                attributes.flag_modified(vendor, "settings")
            if not vendor.state_code:
                vendor.state_code = "TN"
        loc = db.scalar(
            select(Location).where(Location.vendor_id == vendor.id, Location.code == "MAIN")
        )
        if not loc:
            loc = Location(
                vendor_id=vendor.id,
                code="MAIN",
                name="Main Warehouse",
                type="WAREHOUSE",
            )
            db.add(loc)
            db.flush()
            vendor.default_location_id = loc.id

    super_email = "superadmin@as.com"
    if not db.scalar(select(User).where(User.email == super_email)):
        db.add(
            User(
                email=super_email,
                name="Super Admin",
                role="SUPER_ADMIN",
                status="ACTIVE",
                vendor_id=None,
                password=hash_password(SEED_PASSWORD),
            )
        )

    v1 = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
    v2 = db.scalar(select(Vendor).where(Vendor.slug == "vendor-two"))
    for email, name, role, vendor in [
        ("admin@as.com", "Vendor One Admin", "ADMIN", v1),
        ("manager@as.com", "Vendor One Manager", "MANAGER", v1),
        ("staff@as.com", "Vendor One Staff", "STAFF", v1),
        ("admin2@as.com", "Vendor Two Admin", "ADMIN", v2),
    ]:
        if vendor and not db.scalar(select(User).where(User.email == email)):
            db.add(
                User(
                    email=email,
                    name=name,
                    role=role,
                    status="ACTIVE",
                    vendor_id=vendor.id,
                    password=hash_password(SEED_PASSWORD),
                )
            )
    db.commit()


def _deactivate_legacy_demo_items(db: Session, vendor_id: int) -> None:
    """Hide botanical DEMO-* (and other non-napkin) SKUs from store/public catalogs."""
    for item in db.scalars(select(Item).where(Item.vendor_id == vendor_id)).all():
        if item.code in NAPKIN_CODES:
            continue
        item.status = "INACTIVE"
        item.is_sellable = False
        item.is_online_sale = False


def _seed_item_images(db: Session, vendor: Vendor, item: Item, folder: str) -> None:
    src_dir = _napkin_assets_root() / folder
    if not src_dir.is_dir():
        return

    sources = sorted(
        p for p in src_dir.iterdir() if p.is_file() and p.suffix.lower() in _IMAGE_EXTS
    )
    if not sources:
        return

    existing = list(
        db.scalars(
            select(ItemImage).where(
                ItemImage.vendor_id == vendor.id, ItemImage.item_id == item.id
            )
        ).all()
    )
    # Re-seed when missing, or when paths are not under /api/media
    needs_refresh = (not existing) or any(
        not (img.path or "").startswith("/api/media/") for img in existing
    )
    if not needs_refresh and item.primary_image and item.primary_image.startswith("/api/media/"):
        return

    for img in existing:
        db.delete(img)
    db.flush()

    dest_dir = vendor_item_storage(vendor.id, item.id)
    # Clear previous seed files for this item directory
    if dest_dir.exists():
        for old in dest_dir.iterdir():
            if old.is_file():
                old.unlink()

    primary_url: str | None = None
    for idx, src in enumerate(sources):
        fname = _safe_image_name(src, idx)
        dest = dest_dir / fname
        shutil.copy2(src, dest)
        rel = f"{vendor.id}/items/{item.id}/{fname}"
        url = _media_url(rel)
        is_primary = idx == 0
        if is_primary:
            primary_url = url
        db.add(
            ItemImage(
                vendor_id=vendor.id,
                item_id=item.id,
                path=url,
                sort_order=idx,
                is_primary=is_primary,
            )
        )
    if primary_url:
        item.primary_image = primary_url


def seed_demo_catalog(db: Session) -> None:
    """Idempotent napkin SKUs + images + stock for as-demo (Store / landing)."""
    vendor = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
    if not vendor:
        return
    loc = db.scalar(
        select(Location).where(Location.vendor_id == vendor.id, Location.code == "MAIN")
    )
    if not loc:
        return

    _deactivate_legacy_demo_items(db, vendor.id)

    # Ensure GST settings + napkin tax category (12%)
    s = deepcopy(vendor.settings or DEFAULT_VENDOR_SETTINGS)
    tax = s.setdefault("tax", {})
    tax_changed = False
    if "gst_enabled" not in tax:
        tax["gst_enabled"] = True
        tax_changed = True
    if not tax.get("state_code"):
        tax["state_code"] = vendor.state_code or "TN"
        tax_changed = True
    if tax_changed:
        vendor.settings = s
        attributes.flag_modified(vendor, "settings")
    if not vendor.state_code:
        vendor.state_code = "TN"

    gst12 = db.scalar(
        select(TaxCategory).where(TaxCategory.vendor_id == vendor.id, TaxCategory.code == "GST12")
    )
    if not gst12:
        gst12 = TaxCategory(
            vendor_id=vendor.id,
            code="GST12",
            name="GST 12% — Sanitary napkins",
            gst_rate=12,
            hsn_sac="961900",
            description="Organic sanitary napkins (illustrative HSN)",
        )
        db.add(gst12)
        db.flush()

    for spec in NAPKIN_ITEMS:
        item = db.scalar(
            select(Item).where(Item.vendor_id == vendor.id, Item.code == spec["code"])
        )
        if not item:
            item = Item(
                vendor_id=vendor.id,
                code=spec["code"],
                name=spec["name"],
                description=spec["description"],
                unit_of_measure="PCS",
                cost_price=spec["cost_price"],
                sale_price=spec["sale_price"],
                category=spec["category"],
                type="PRODUCT",
                status="ACTIVE",
                is_sellable=True,
                is_online_sale=spec["is_online_sale"],
                sale_price_includes_gst=True,
                tax_category_id=gst12.id,
            )
            db.add(item)
            db.flush()
        else:
            item.name = spec["name"]
            item.description = spec["description"]
            item.cost_price = spec["cost_price"]
            item.sale_price = spec["sale_price"]
            item.category = spec["category"]
            item.status = "ACTIVE"
            item.is_sellable = True
            item.is_online_sale = spec["is_online_sale"]
            item.sale_price_includes_gst = True
            if not item.tax_category_id:
                item.tax_category_id = gst12.id

        stock = db.scalar(
            select(Stock).where(Stock.item_id == item.id, Stock.location_id == loc.id)
        )
        if not stock:
            db.add(
                Stock(
                    vendor_id=vendor.id,
                    item_id=item.id,
                    location_id=loc.id,
                    quantity_on_hand=spec["qty"],
                    quantity_reserved=0,
                    reorder_level=10,
                    reorder_qty=25,
                )
            )
        elif stock.quantity_on_hand <= 0:
            stock.quantity_on_hand = spec["qty"]

        _seed_item_images(db, vendor, item, spec["folder"])

    db.commit()


def seed_demo_reviews(db: Session) -> None:
    """Sample ratings for napkin SKUs (idempotent per customer+item)."""
    vendor = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
    if not vendor:
        return

    items = {
        i.code: i
        for i in db.scalars(
            select(Item).where(Item.vendor_id == vendor.id, Item.code.in_(NAPKIN_CODES))
        ).all()
    }
    if not items:
        return

    review_specs: list[tuple[str, str, int, str]] = [
        ("retail-customer@as.com", "NAPKIN-M", 5, "Soft and comfortable for everyday use."),
        ("customer2@as.com", "NAPKIN-M", 4, "Good fit — waiting for more pack photos."),
        ("retail-customer@as.com", "NAPKIN-L", 5, "Excellent absorbency, no irritation."),
        ("customer2@as.com", "NAPKIN-L", 4, "Quality pack, wings hold well."),
        ("retail-customer@as.com", "NAPKIN-XL", 5, "Perfect for heavier days."),
        ("customer2@as.com", "NAPKIN-XL", 5, "True XL coverage, highly recommend."),
        ("retail-customer@as.com", "NAPKIN-XXL", 4, "Great protection through long days."),
        ("customer2@as.com", "NAPKIN-XXL", 5, "Best size in the range for me."),
        ("retail-customer@as.com", "NAPKIN-XXXL", 5, "Overnight peace of mind."),
        ("customer2@as.com", "NAPKIN-XXXL", 4, "Thick core, still soft on skin."),
    ]

    for email, code, rating, comment in review_specs:
        item = items.get(code)
        if not item:
            continue
        customer = db.scalar(
            select(Customer).where(Customer.vendor_id == vendor.id, Customer.email == email)
        )
        if not customer:
            continue
        existing = db.scalar(
            select(ItemReview).where(
                ItemReview.vendor_id == vendor.id,
                ItemReview.item_id == item.id,
                ItemReview.customer_id == customer.id,
            )
        )
        if existing:
            existing.rating = rating
            existing.comment = comment
            existing.is_verified_purchase = True
            continue
        db.add(
            ItemReview(
                vendor_id=vendor.id,
                item_id=item.id,
                customer_id=customer.id,
                user_id=customer.user_id,
                rating=rating,
                comment=comment,
                is_verified_purchase=True,
            )
        )
    db.commit()


def _upsert_party_user(
    db: Session,
    *,
    vendor_id: int,
    email: str,
    name: str,
    party_type: str,
    parent_id: int | None,
    phone: str | None,
) -> Customer:
    """Create/link User + Customer for a trade party (idempotent)."""
    role = party_type if party_type != "CUSTOMER" else "CUSTOMER"
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            email=email,
            name=name,
            role=role,
            status="ACTIVE",
            vendor_id=vendor_id,
            phone=phone,
            password=hash_password(SEED_PASSWORD),
        )
        db.add(user)
        db.flush()
    else:
        if user.role != role and user.role in (
            "DISTRIBUTOR",
            "DEALER",
            "RETAILER",
            "CUSTOMER",
        ):
            user.role = role
        if not user.phone and phone:
            user.phone = phone

    party = db.scalar(
        select(Customer).where(Customer.vendor_id == vendor_id, Customer.email == email)
    )
    acquisition = "WALK_IN" if parent_id is None and party_type == "CUSTOMER" else "OTHER"
    if not party:
        party = Customer(
            vendor_id=vendor_id,
            name=name,
            email=email,
            phone=phone,
            party_type=party_type,
            parent_id=parent_id,
            acquisition_source=acquisition,
            status="ACTIVE",
            user_id=user.id,
            member_since=date.today(),
        )
        db.add(party)
        db.flush()
    else:
        party.name = name
        party.party_type = party_type
        if parent_id and not party.parent_id:
            party.parent_id = parent_id
        if not party.user_id:
            party.user_id = user.id
        if phone and not party.phone:
            party.phone = phone
    return party


def _ensure_price_rules(db: Session, vendor_id: int) -> None:
    items = db.scalars(
        select(Item).where(Item.vendor_id == vendor_id, Item.code.like("NAPKIN-%"))
    ).all()
    for item in items:
        for ptype, pct in TRADE_PRICE_PCT.items():
            existing = db.scalar(
                select(PartyPriceRule).where(
                    PartyPriceRule.vendor_id == vendor_id,
                    PartyPriceRule.item_id == item.id,
                    PartyPriceRule.party_type == ptype,
                )
            )
            if not existing:
                db.add(
                    PartyPriceRule(
                        vendor_id=vendor_id,
                        item_id=item.id,
                        party_type=ptype,
                        mode="PERCENT_OFF",
                        value=pct,
                        status="ACTIVE",
                    )
                )
            else:
                existing.mode = "PERCENT_OFF"
                existing.value = pct
                existing.status = "ACTIVE"


def _seed_demo_order(
    db: Session,
    *,
    vendor_id: int,
    order_code: str,
    buyer: Customer,
    seller: Customer | None,
    item: Item,
    qty: int,
    sell_price: float,
    trade_price: float,
    shipping_charge: float,
    payment_status: str,
    fulfillment_status: str,
    courier: str | None = None,
    tracking_number: str | None = None,
) -> None:
    if db.scalar(
        select(SaleOrder).where(
            SaleOrder.vendor_id == vendor_id, SaleOrder.order_code == order_code
        )
    ):
        return

    from datetime import datetime, timezone

    from app.services.sales_orders import create_sale_order

    so = create_sale_order(
        db,
        vendor_id=vendor_id,
        data={
            "order_code": order_code,
            "order_date": date.today(),
            "customer_id": buyer.id,
            "placed_for_customer_id": buyer.id,
            "ordered_by_party_id": seller.id if seller else None,
            "sales_channel": "B2B" if seller else "COUNTER",
            "status": "CONFIRMED",
            "payment_status": payment_status,
            "fulfillment_status": fulfillment_status,
            "shipping_charge": shipping_charge,
            "shipping_name": buyer.name,
            "shipping_phone": buyer.phone,
            "shipping_city": "Chennai",
            "shipping_state": "TN",
            "items": [
                {
                    "item_id": item.id,
                    "quantity": qty,
                    "unit_price": sell_price,
                    "trade_unit_price": trade_price,
                }
            ],
        },
        created_by="seed",
        stock_mode="none",
    )
    if courier and tracking_number:
        so.courier = courier
        so.tracking_number = tracking_number
        so.shipped_at = datetime.now(timezone.utc)
        so.fulfillment_status = "SHIPPED"


def seed_b2b_demo(db: Session) -> None:
    """Full hierarchy users, parties, trade prices, and sample orders for as-demo."""
    vendor = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
    if not vendor:
        return

    parties: dict[str, Customer] = {}
    for key, email, name, ptype, parent_key, phone in B2B_PARTY_SPECS:
        parent_id = parties[parent_key].id if parent_key else None
        parties[key] = _upsert_party_user(
            db,
            vendor_id=vendor.id,
            email=email,
            name=name,
            party_type=ptype,
            parent_id=parent_id,
            phone=phone,
        )
    db.flush()

    _ensure_price_rules(db, vendor.id)

    items = {
        i.code: i
        for i in db.scalars(
            select(Item).where(Item.vendor_id == vendor.id, Item.code.like("NAPKIN-%"))
        ).all()
    }
    napkin_m = items.get("NAPKIN-M")
    napkin_l = items.get("NAPKIN-L")
    napkin_xl = items.get("NAPKIN-XL")
    napkin_xxl = items.get("NAPKIN-XXL")
    napkin_xxxl = items.get("NAPKIN-XXXL")

    # Helper: trade = MSRP * (1 - pct/100)
    def trade(msrp: float, ptype: str) -> float:
        pct = TRADE_PRICE_PCT.get(ptype, 0)
        return round(float(msrp) * (1 - pct / 100), 2)

    if napkin_l and parties.get("ret1") and parties.get("cust1"):
        # Retailer → end customer (shipped, AKR)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-TRACK-1",
            buyer=parties["cust1"],
            seller=parties["ret1"],
            item=napkin_l,
            qty=2,
            sell_price=float(napkin_l.sale_price),
            trade_price=trade(napkin_l.sale_price, "RETAILER"),
            shipping_charge=80,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="AKR_PARCEL",
            tracking_number="AKR-DEMO-1001",
        )

    if napkin_xl and parties.get("deal1") and parties.get("ret1"):
        # Dealer → retailer (shipped, Maruthi)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DEALER-1",
            buyer=parties["ret1"],
            seller=parties["deal1"],
            item=napkin_xl,
            qty=5,
            sell_price=float(napkin_xl.sale_price),
            trade_price=trade(napkin_xl.sale_price, "DEALER"),
            shipping_charge=40,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="MARUTHI_PARCEL",
            tracking_number="MRT-DEMO-2002",
        )

    if napkin_xxxl and parties.get("dist1") and parties.get("deal1"):
        # Distributor → dealer (confirmed, awaiting ship)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DIST-1",
            buyer=parties["deal1"],
            seller=parties["dist1"],
            item=napkin_xxxl,
            qty=3,
            sell_price=float(napkin_xxxl.sale_price),
            trade_price=trade(napkin_xxxl.sale_price, "DISTRIBUTOR"),
            shipping_charge=40,
            payment_status="UNPAID",
            fulfillment_status="UNFULFILLED",
        )

    if napkin_xxl and parties.get("cust2") and parties.get("ret1"):
        # Second customer under same retailer
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-TRACK-2",
            buyer=parties["cust2"],
            seller=parties["ret1"],
            item=napkin_xxl,
            qty=4,
            sell_price=float(napkin_xxl.sale_price),
            trade_price=trade(napkin_xxl.sale_price, "RETAILER"),
            shipping_charge=40,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="AKR_PARCEL",
            tracking_number="AKR-DEMO-1002",
        )

    if napkin_m and parties.get("direct"):
        # Independent / direct customer (counter)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DIRECT-1",
            buyer=parties["direct"],
            seller=None,
            item=napkin_m,
            qty=1,
            sell_price=float(napkin_m.sale_price),
            trade_price=float(napkin_m.sale_price),
            shipping_charge=0,
            payment_status="PAID",
            fulfillment_status="UNFULFILLED",
        )

    db.commit()


def run_seed(db: Session) -> None:
    seed_permissions(db)
    seed_vendors_and_users(db)
    seed_demo_catalog(db)
    seed_b2b_demo(db)
    seed_demo_reviews(db)
