"""Seed permissions, role grants, 2 vendors, SUPER_ADMIN + vendor admins + demo catalog + B2B."""

from copy import deepcopy
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, attributes

from app.core.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS
from app.core.security import hash_password
from app.models import (
    DEFAULT_VENDOR_SETTINGS,
    Customer,
    Item,
    Location,
    PartyPriceRule,
    Permission,
    RolePermission,
    SaleOrder,
    Stock,
    User,
    Vendor,
)


SEED_PASSWORD = "User@123"

DEMO_ITEMS = [
    {
        "code": "DEMO-NEEM",
        "name": "Neem Face Wash",
        "description": "Gentle botanical cleanser for daily use.",
        "sale_price": 249,
        "cost_price": 120,
        "category": "SKINCARE",
        "is_online_sale": True,
        "qty": 100,
    },
    {
        "code": "DEMO-TURMERIC",
        "name": "Turmeric Glow Soap",
        "description": "Handmade soap with turmeric and coconut oil.",
        "sale_price": 149,
        "cost_price": 60,
        "category": "BATH",
        "is_online_sale": True,
        "qty": 80,
    },
    {
        "code": "DEMO-OIL",
        "name": "Cold-Pressed Coconut Oil",
        "description": "Kitchen and hair care staple — 500 ml.",
        "sale_price": 399,
        "cost_price": 200,
        "category": "OILS",
        "is_online_sale": True,
        "qty": 50,
    },
    {
        "code": "DEMO-BULK-NEEM",
        "name": "Neem Face Wash — Trade Carton (12)",
        "description": "B2B-only carton pack; not listed on ecommerce store.",
        "sale_price": 2490,
        "cost_price": 1200,
        "category": "SKINCARE",
        "is_online_sale": False,
        "qty": 200,
    },
]

# Trade discounts applied to every DEMO-* item (party_type → % off MSRP)
TRADE_PRICE_PCT = {
    "DISTRIBUTOR": 30,
    "DEALER": 20,
    "RETAILER": 10,
}

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
                    "flat_rate": 0,
                    "free_over": None,
                    "qty_tiers": [
                        {"max_qty": 2, "charge": 80},
                        {"max_qty": 9, "charge": 40},
                        {"max_qty": None, "charge": 0},
                    ],
                    "couriers": ["AKR_PARCEL", "MARUTHI_PARCEL"],
                }
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
            if not ship.get("qty_tiers"):
                ship["qty_tiers"] = [
                    {"max_qty": 2, "charge": 80},
                    {"max_qty": 9, "charge": 40},
                    {"max_qty": None, "charge": 0},
                ]
                ship["couriers"] = ["AKR_PARCEL", "MARUTHI_PARCEL"]
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


def seed_demo_catalog(db: Session) -> None:
    """Idempotent demo SKUs + stock for as-demo (Store / landing smoke)."""
    vendor = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
    if not vendor:
        return
    loc = db.scalar(
        select(Location).where(Location.vendor_id == vendor.id, Location.code == "MAIN")
    )
    if not loc:
        return

    for spec in DEMO_ITEMS:
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
            )
            db.add(item)
            db.flush()

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
        select(Item).where(Item.vendor_id == vendor_id, Item.code.like("DEMO-%"))
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
            select(Item).where(Item.vendor_id == vendor.id, Item.code.like("DEMO-%"))
        ).all()
    }
    neem = items.get("DEMO-NEEM")
    oil = items.get("DEMO-OIL")
    bulk = items.get("DEMO-BULK-NEEM")
    turmeric = items.get("DEMO-TURMERIC")

    # Helper: trade = MSRP * (1 - pct/100)
    def trade(msrp: float, ptype: str) -> float:
        pct = TRADE_PRICE_PCT.get(ptype, 0)
        return round(float(msrp) * (1 - pct / 100), 2)

    if neem and oil and parties.get("ret1") and parties.get("cust1"):
        # Retailer → end customer (shipped, AKR)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-TRACK-1",
            buyer=parties["cust1"],
            seller=parties["ret1"],
            item=neem,
            qty=2,
            sell_price=float(neem.sale_price),
            trade_price=trade(neem.sale_price, "RETAILER"),
            shipping_charge=80,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="AKR_PARCEL",
            tracking_number="AKR-DEMO-1001",
        )

    if oil and parties.get("deal1") and parties.get("ret1"):
        # Dealer → retailer (shipped, Maruthi)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DEALER-1",
            buyer=parties["ret1"],
            seller=parties["deal1"],
            item=oil,
            qty=5,
            sell_price=float(oil.sale_price),
            trade_price=trade(oil.sale_price, "DEALER"),
            shipping_charge=40,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="MARUTHI_PARCEL",
            tracking_number="MRT-DEMO-2002",
        )

    if bulk and parties.get("dist1") and parties.get("deal1"):
        # Distributor → dealer (confirmed, awaiting ship)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DIST-1",
            buyer=parties["deal1"],
            seller=parties["dist1"],
            item=bulk,
            qty=3,
            sell_price=float(bulk.sale_price),
            trade_price=trade(bulk.sale_price, "DISTRIBUTOR"),
            shipping_charge=40,
            payment_status="UNPAID",
            fulfillment_status="UNFULFILLED",
        )

    if turmeric and parties.get("cust2") and parties.get("ret1"):
        # Second customer under same retailer
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-TRACK-2",
            buyer=parties["cust2"],
            seller=parties["ret1"],
            item=turmeric,
            qty=4,
            sell_price=float(turmeric.sale_price),
            trade_price=trade(turmeric.sale_price, "RETAILER"),
            shipping_charge=40,
            payment_status="PAID",
            fulfillment_status="SHIPPED",
            courier="AKR_PARCEL",
            tracking_number="AKR-DEMO-1002",
        )

    if neem and parties.get("direct"):
        # Independent / direct customer (counter)
        _seed_demo_order(
            db,
            vendor_id=vendor.id,
            order_code="SO-DEMO-DIRECT-1",
            buyer=parties["direct"],
            seller=None,
            item=neem,
            qty=1,
            sell_price=float(neem.sale_price),
            trade_price=float(neem.sale_price),
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
