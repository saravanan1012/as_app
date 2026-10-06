"""Phase 9 hardening — isolation, RBAC denials, hierarchy, store gate, checkout idempotency."""

import uuid

import pytest
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Item, Vendor


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _login(client, email: str, password: str = "User@123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r


def _logout(client):
    client.post("/api/auth/logout")


def _enable_store(client, vendor_id: int = 1, enabled: bool = True):
    _logout(client)
    _login(client, "superadmin@as.com")
    r = client.patch(
        f"/api/platform/vendors/{vendor_id}/store",
        json={"store_enabled": enabled},
    )
    assert r.status_code == 200, r.text
    _logout(client)


@pytest.mark.usefixtures("db_ready")
def test_staff_rbac_denials(client):
    """STAFF can write sales/customers but not users, offers write, or platform."""
    _login(client, "staff@as.com")

    assert client.get("/api/platform/vendors").status_code == 403
    assert client.get("/api/users").status_code == 403
    assert client.get("/api/audit-logs").status_code == 403

    # offers.write denied
    r = client.post(
        "/api/offers",
        json={"code": f"X{_uid()}", "discount_percentage": 5},
    )
    assert r.status_code == 403

    # catalog write denied
    r = client.post(
        "/api/items",
        json={"code": f"ST{_uid()}", "name": f"Staff Item {_uid()}", "sale_price": 10},
    )
    assert r.status_code == 403

    # sales read/write allowed
    assert client.get("/api/sale-orders").status_code == 200
    assert client.get("/api/customers").status_code == 200


@pytest.mark.usefixtures("db_ready")
def test_cross_vendor_item_and_customer_isolation(client):
    """Vendor-two admin must not read vendor-one entities by id."""
    _login(client, "admin@as.com")
    suf = _uid()
    item = client.post(
        "/api/items",
        json={"code": f"V1{suf}", "name": f"V1 Only {suf}", "sale_price": 50},
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]

    cust = client.post(
        "/api/customers",
        json={"name": f"V1 Cust {suf}", "party_type": "CUSTOMER", "acquisition_source": "WALK_IN"},
    )
    assert cust.status_code == 201, cust.text
    cust_id = cust.json()["data"]["id"]

    _logout(client)
    _login(client, "admin2@as.com")

    assert client.get(f"/api/items/{item_id}").status_code == 404
    assert client.get(f"/api/customers/{cust_id}").status_code == 404
    assert client.patch(f"/api/items/{item_id}", json={"name": "hacked"}).status_code == 404


@pytest.mark.usefixtures("db_ready")
def test_superadmin_requires_vendor_id_for_scoped_apis(client):
    _login(client, "superadmin@as.com")
    r = client.get("/api/items")
    assert r.status_code == 400

    db = SessionLocal()
    try:
        v1 = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
        assert v1
        vid = v1.id
    finally:
        db.close()

    r = client.get(f"/api/items?vendor_id={vid}")
    assert r.status_code == 200


@pytest.mark.usefixtures("db_ready")
def test_hierarchy_invalid_parent_types(client):
    _login(client, "admin@as.com")
    suf = _uid()

    dist = client.post(
        "/api/customers",
        json={
            "name": f"Dist {suf}",
            "party_type": "DISTRIBUTOR",
            "acquisition_source": "WALK_IN",
        },
    )
    assert dist.status_code == 201, dist.text
    dist_id = dist.json()["data"]["id"]

    # DISTRIBUTOR cannot have a parent
    bad_dist = client.post(
        "/api/customers",
        json={
            "name": f"Bad Dist {suf}",
            "party_type": "DISTRIBUTOR",
            "parent_id": dist_id,
        },
    )
    assert bad_dist.status_code == 400

    cust = client.post(
        "/api/customers",
        json={
            "name": f"Leaf Cust {suf}",
            "party_type": "CUSTOMER",
            "acquisition_source": "WALK_IN",
        },
    )
    assert cust.status_code == 201
    cust_id = cust.json()["data"]["id"]

    # CUSTOMER cannot be a parent
    bad_parent = client.post(
        "/api/customers",
        json={
            "name": f"Child of Cust {suf}",
            "party_type": "CUSTOMER",
            "parent_id": cust_id,
            "acquisition_source": "WALK_IN",
        },
    )
    assert bad_parent.status_code == 400

    # Valid: dealer under distributor
    dealer = client.post(
        "/api/customers",
        json={
            "name": f"Ok Dealer {suf}",
            "party_type": "DEALER",
            "parent_id": dist_id,
            "acquisition_source": "REFERRAL",
        },
    )
    assert dealer.status_code == 201, dealer.text


@pytest.mark.usefixtures("db_ready")
def test_public_products_when_store_disabled(client):
    """Landing/product info stays available; Store APIs stay gated."""
    _enable_store(client, enabled=False)

    pub = client.get("/api/public/vendor", headers={"x-vendor-slug": "as-demo"})
    assert pub.status_code == 200
    assert pub.json()["data"]["store_enabled"] is False

    products = client.get("/api/public/products", headers={"x-vendor-slug": "as-demo"})
    assert products.status_code == 200

    store = client.get("/api/store/products", headers={"x-vendor-slug": "as-demo"})
    assert store.status_code == 403

    _enable_store(client, enabled=True)
    store_on = client.get("/api/store/meta", headers={"x-vendor-slug": "as-demo"})
    assert store_on.status_code == 200
    assert store_on.json()["data"]["slug"] == "as-demo"


@pytest.mark.usefixtures("db_ready")
def test_checkout_idempotent_payment_event(client):
    """Second verify with same payment_id must not double-deduct stock."""
    _enable_store(client, enabled=True)
    _login(client, "admin@as.com")
    suf = _uid()
    item = client.post(
        "/api/items",
        json={
            "code": f"ID{suf}",
            "name": f"Idem Item {suf}",
            "sale_price": 100,
            "is_online_sale": True,
            "sale_price_includes_gst": True,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]
    loc_id = client.get("/api/locations").json()["data"][0]["id"]
    client.post(
        "/api/stock",
        json={"item_id": item_id, "location_id": loc_id, "quantity_on_hand": 20},
    )

    _logout(client)
    email = f"idem_{suf}@example.com"
    client.post(
        "/api/store/auth/register",
        headers={"x-vendor-slug": "as-demo"},
        json={"email": email, "password": "User@123", "name": "Idem Buyer"},
    )

    create = client.post(
        "/api/store/checkout/razorpay/create",
        headers={"x-vendor-slug": "as-demo"},
        json={"items": [{"item_id": item_id, "quantity": 1}]},
    )
    assert create.status_code == 201, create.text
    data = create.json()["data"]
    order_id = data["razorpay_order_id"]
    order_code = data["order_code"]
    payment_id = f"pay_idem_{suf}"

    sig = client.get(
        f"/api/store/checkout/razorpay/mock-sign?order_id={order_id}&payment_id={payment_id}",
        headers={"x-vendor-slug": "as-demo"},
    ).json()["data"]["signature"]

    body = {
        "order_code": order_code,
        "razorpay_order_id": order_id,
        "razorpay_payment_id": payment_id,
        "razorpay_signature": sig,
    }
    v1 = client.post("/api/store/checkout/razorpay/verify", headers={"x-vendor-slug": "as-demo"}, json=body)
    assert v1.status_code == 200, v1.text
    v2 = client.post("/api/store/checkout/razorpay/verify", headers={"x-vendor-slug": "as-demo"}, json=body)
    assert v2.status_code == 200, v2.text

    _logout(client)
    _login(client, "admin@as.com")
    stock = client.get("/api/stock").json()["data"]
    row = next(s for s in stock if s["item_id"] == item_id)
    assert row["quantity_on_hand"] == 19
    assert row["quantity_reserved"] == 0


@pytest.mark.usefixtures("db_ready")
def test_login_redirects_by_role(client):
    mapping = {
        "superadmin@as.com": "/platform",
        "admin@as.com": "/admin/sales-orders",
        "staff@as.com": "/admin/sales-orders",
        "distributor@as.com": "/b2b",
    }
    for email, expected in mapping.items():
        _logout(client)
        r = _login(client, email)
        assert r.json()["data"]["default_redirect"] == expected, email

    # CUSTOMER home depends on store_enabled for the vendor
    _logout(client)
    r = _login(client, "retail-customer@as.com")
    assert r.json()["data"]["default_redirect"] in ("/store", "/store/orders")


@pytest.mark.usefixtures("db_ready")
def test_demo_seed_catalog_present(client):
    """Phase 9 seed polish — as-demo should have at least one sellable demo item after seed."""
    db = SessionLocal()
    try:
        v = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
        assert v
        count = len(
            db.scalars(
                select(Item).where(
                    Item.vendor_id == v.id,
                    Item.code.like("DEMO-%"),
                )
            ).all()
        )
    finally:
        db.close()
    assert count >= 1
