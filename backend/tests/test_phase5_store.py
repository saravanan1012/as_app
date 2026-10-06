import uuid
from datetime import date

import pytest


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _login(client, email="admin@as.com", password="User@123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r


def _enable_store(client, vendor_id=1, enabled=True):
    client.post("/api/auth/logout")
    _login(client, "superadmin@as.com")
    r = client.patch(
        f"/api/platform/vendors/{vendor_id}/store",
        json={"store_enabled": enabled},
    )
    assert r.status_code == 200, r.text
    client.post("/api/auth/logout")


def _headers(slug="as-demo"):
    return {"x-vendor-slug": slug}


@pytest.mark.usefixtures("db_ready")
def test_store_gate_and_catalog(client):
    _enable_store(client, enabled=False)
    r = client.get("/api/store/products", headers=_headers())
    assert r.status_code == 403

    _enable_store(client, enabled=True)
    r = client.get("/api/store/meta", headers=_headers())
    assert r.status_code == 200
    assert r.json()["data"]["slug"] == "as-demo"

    _login(client)
    suf = _uid()
    item = client.post(
        "/api/items",
        json={
            "code": f"ONL{suf}",
            "name": f"Online {suf}",
            "sale_price": 118,
            "is_online_sale": True,
            "sale_price_includes_gst": True,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]

    client.post("/api/auth/logout")
    products = client.get("/api/store/products", headers=_headers())
    assert products.status_code == 200
    codes = {p["code"] for p in products.json()["data"]["data"]}
    assert f"ONL{suf}" in codes

    detail = client.get(f"/api/store/products/{item_id}", headers=_headers())
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == item_id


@pytest.mark.usefixtures("db_ready")
def test_cod_checkout_and_offer(client):
    _enable_store(client, enabled=True)
    _login(client)
    suf = _uid()

    tax = client.post(
        "/api/tax-categories",
        json={"code": f"T{suf}", "name": "GST18", "gst_rate": 18},
    )
    tax_id = tax.json()["data"]["id"]
    item = client.post(
        "/api/items",
        json={
            "code": f"COD{suf}",
            "name": f"COD Item {suf}",
            "sale_price": 118,
            "cost_price": 50,
            "is_online_sale": True,
            "sale_price_includes_gst": True,
            "tax_category_id": tax_id,
        },
    )
    item_id = item.json()["data"]["id"]
    loc_id = client.get("/api/locations").json()["data"][0]["id"]
    client.post(
        "/api/stock",
        json={"item_id": item_id, "location_id": loc_id, "quantity_on_hand": 50},
    )
    offer = client.post(
        "/api/offers",
        json={
            "code": f"OFF{suf}",
            "discount_amount": 10,
            "sales_channel": "ECOMMERCE",
            "customer_type": "CUSTOMER",
            "is_active": True,
        },
    )
    assert offer.status_code == 201, offer.text

    # Register store customer
    client.post("/api/auth/logout")
    email = f"cust_{suf}@example.com"
    reg = client.post(
        "/api/store/auth/register",
        headers=_headers(),
        json={"email": email, "password": "User@123", "name": "Store Buyer"},
    )
    assert reg.status_code == 201, reg.text

    val = client.post(
        "/api/store/offers/validate",
        headers=_headers(),
        json={"code": f"OFF{suf}", "subtotal": 118, "item_ids": [item_id]},
    )
    assert val.status_code == 200, val.text
    assert val.json()["data"]["discount_amount"] == 10.0

    co = client.post(
        "/api/store/checkout/cod",
        headers=_headers(),
        json={
            "items": [{"item_id": item_id, "quantity": 1}],
            "offer_code": f"OFF{suf}",
            "address": {"street": "1 Main", "city": "Chennai", "state": "TN", "zip": "600001"},
        },
    )
    assert co.status_code == 201, co.text
    assert co.json()["data"]["payment_status"] == "UNPAID"
    assert co.json()["data"]["order_code"].startswith("SO-ECO-")

    stock = client.post("/api/auth/logout")
    _login(client)
    stock = client.get("/api/stock")
    qty = next(s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id)
    assert qty == 49


@pytest.mark.usefixtures("db_ready")
def test_razorpay_mock_reserve_and_verify(client):
    _enable_store(client, enabled=True)
    _login(client)
    suf = _uid()
    item = client.post(
        "/api/items",
        json={
            "code": f"RZP{suf}",
            "name": f"RZP Item {suf}",
            "sale_price": 200,
            "is_online_sale": True,
            "sale_price_includes_gst": True,
        },
    )
    item_id = item.json()["data"]["id"]
    loc_id = client.get("/api/locations").json()["data"][0]["id"]
    client.post(
        "/api/stock",
        json={"item_id": item_id, "location_id": loc_id, "quantity_on_hand": 10},
    )

    client.post("/api/auth/logout")
    email = f"rzp_{suf}@example.com"
    client.post(
        "/api/store/auth/register",
        headers=_headers(),
        json={"email": email, "password": "User@123", "name": "RZP Buyer"},
    )

    create = client.post(
        "/api/store/checkout/razorpay/create",
        headers=_headers(),
        json={"items": [{"item_id": item_id, "quantity": 2}]},
    )
    assert create.status_code == 201, create.text
    data = create.json()["data"]
    assert data["mock"] is True
    # 2 × ₹200 (+ optional shipping from vendor settings)
    assert data["amount"] >= 40000
    assert data["amount"] % 100 == 0
    order_id = data["razorpay_order_id"]
    order_code = data["order_code"]

    # Reserved, not deducted
    client.post("/api/auth/logout")
    _login(client)
    stock = client.get("/api/stock")
    row = next(s for s in stock.json()["data"] if s["item_id"] == item_id)
    assert row["quantity_on_hand"] == 10
    assert row["quantity_reserved"] == 2

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": email, "password": "User@123"})

    payment_id = f"pay_mock_{suf}"
    sig = client.get(
        f"/api/store/checkout/razorpay/mock-sign?order_id={order_id}&payment_id={payment_id}",
        headers=_headers(),
    )
    assert sig.status_code == 200
    signature = sig.json()["data"]["signature"]

    verify = client.post(
        "/api/store/checkout/razorpay/verify",
        headers=_headers(),
        json={
            "order_code": order_code,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["data"]["payment_status"] == "PAID"

    # Idempotent second verify
    verify2 = client.post(
        "/api/store/checkout/razorpay/verify",
        headers=_headers(),
        json={
            "order_code": order_code,
            "razorpay_order_id": order_id,
            "razorpay_payment_id": payment_id,
            "razorpay_signature": signature,
        },
    )
    assert verify2.status_code == 200

    client.post("/api/auth/logout")
    _login(client)
    stock = client.get("/api/stock")
    row = next(s for s in stock.json()["data"] if s["item_id"] == item_id)
    assert row["quantity_on_hand"] == 8
    assert row["quantity_reserved"] == 0
