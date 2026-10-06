"""Phase 10 — B2B hierarchy, pricing, shipping qty tiers, tracking."""

import uuid

from app.services.pricing import resolve_trade_price, shipping_charge_for_qty


def _uid():
    return uuid.uuid4().hex[:8]


def _login(client, email, password="User@123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r


def test_resolve_trade_price_modes():
    assert resolve_trade_price(100, "PERCENT_OFF", 30) == 70.0
    assert resolve_trade_price(100, "FIXED_OFF", 15) == 85.0
    assert resolve_trade_price(100, "FIXED_PRICE", 55) == 55.0
    assert resolve_trade_price(100, None, None) == 100.0


def test_shipping_qty_tiers():
    settings = {
        "shipping": {
            "qty_tiers": [
                {"max_qty": 2, "charge": 80},
                {"max_qty": 9, "charge": 40},
                {"max_qty": None, "charge": 0},
            ]
        }
    }
    assert shipping_charge_for_qty(settings, total_qty=1, subtotal=100) == 80.0
    assert shipping_charge_for_qty(settings, total_qty=5, subtotal=100) == 40.0
    assert shipping_charge_for_qty(settings, total_qty=10, subtotal=100) == 0.0


def test_retailer_hierarchy(client):
    _login(client, "admin@as.com")
    suf = _uid()
    dist = client.post(
        "/api/customers",
        json={"name": f"Dist {suf}", "party_type": "DISTRIBUTOR"},
    )
    assert dist.status_code == 201, dist.text
    dist_id = dist.json()["data"]["id"]

    dealer = client.post(
        "/api/customers",
        json={"name": f"Dealer {suf}", "party_type": "DEALER", "parent_id": dist_id},
    )
    assert dealer.status_code == 201, dealer.text
    dealer_id = dealer.json()["data"]["id"]

    retailer = client.post(
        "/api/customers",
        json={"name": f"Retailer {suf}", "party_type": "RETAILER", "parent_id": dealer_id},
    )
    assert retailer.status_code == 201, retailer.text
    retailer_id = retailer.json()["data"]["id"]

    cust = client.post(
        "/api/customers",
        json={"name": f"Cust {suf}", "party_type": "CUSTOMER", "parent_id": retailer_id},
    )
    assert cust.status_code == 201, cust.text

    # CUSTOMER cannot be parent
    bad = client.post(
        "/api/customers",
        json={
            "name": f"Bad {suf}",
            "party_type": "CUSTOMER",
            "parent_id": cust.json()["data"]["id"],
        },
    )
    assert bad.status_code == 400


def test_party_price_rule_and_b2b_floor(client):
    _login(client, "admin@as.com")
    suf = _uid()
    item = client.post(
        "/api/items",
        json={
            "code": f"B2B{suf}"[:50],
            "name": f"B2B Item {suf}",
            "sale_price": 200,
            "cost_price": 50,
            "is_sellable": True,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]

    rule = client.post(
        "/api/party-price-rules",
        json={
            "item_id": item_id,
            "party_type": "DISTRIBUTOR",
            "mode": "PERCENT_OFF",
            "value": 25,
        },
    )
    assert rule.status_code == 201, rule.text
    assert float(rule.json()["data"]["value"]) == 25

    # seed distributor login
    _login(client, "distributor@as.com")
    cat = client.get("/api/b2b/catalog")
    assert cat.status_code == 200, cat.text
    rows = cat.json()["data"]["data"]
    match = next((r for r in rows if r["id"] == item_id), None)
    assert match is not None
    assert match["trade_unit_price"] == 150.0

    down = client.get("/api/b2b/downline")
    assert down.status_code == 200
    parties = down.json()["data"]["data"]
    assert any(p["party_type"] == "CUSTOMER" for p in parties)
    buyer = next(p for p in parties if p["party_type"] == "CUSTOMER")

    # below trade rejected
    bad = client.post(
        "/api/b2b/orders",
        json={
            "customer_id": buyer["id"],
            "items": [{"item_id": item_id, "quantity": 1, "unit_price": 100}],
        },
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/b2b/orders",
        json={
            "customer_id": buyer["id"],
            "items": [{"item_id": item_id, "quantity": 1, "unit_price": 200}],
            "status": "DRAFT",
        },
    )
    assert ok.status_code == 201, ok.text
    assert ok.json()["data"]["sales_channel"] == "B2B"
    line = ok.json()["data"]["items"][0]
    assert float(line["trade_unit_price"]) == 150.0
    assert float(line["unit_price"]) == 200.0


def test_shipment_courier_allowlist(client):
    _login(client, "admin@as.com")
    suf = _uid()
    cust = client.post(
        "/api/customers",
        json={"name": f"Ship Cust {suf}", "party_type": "CUSTOMER", "acquisition_source": "WALK_IN"},
    )
    assert cust.status_code == 201
    item = client.post(
        "/api/items",
        json={"code": f"SH{suf}"[:50], "name": f"Ship {suf}", "sale_price": 50, "is_sellable": True},
    )
    assert item.status_code == 201
    so = client.post(
        "/api/sale-orders",
        json={
            "order_code": f"SO-SHIP-{suf}",
            "order_date": "2026-10-06",
            "customer_id": cust.json()["data"]["id"],
            "status": "DRAFT",
            "items": [{"item_id": item.json()["data"]["id"], "quantity": 1, "unit_price": 50}],
        },
    )
    assert so.status_code == 201, so.text
    so_id = so.json()["data"]["id"]

    bad = client.patch(
        f"/api/sale-orders/{so_id}/shipment",
        json={"courier": "DHL", "tracking_number": "X1"},
    )
    assert bad.status_code == 400

    good = client.patch(
        f"/api/sale-orders/{so_id}/shipment",
        json={"courier": "AKR_PARCEL", "tracking_number": "AKR-99"},
    )
    assert good.status_code == 200, good.text
    body = good.json()["data"]
    assert body["courier"] == "AKR_PARCEL"
    assert body["tracking_number"] == "AKR-99"
    assert body["fulfillment_status"] == "SHIPPED"
    assert body["courier_label"] == "AKR Parcel"


def test_customer_cannot_see_others_orders(client):
    _login(client, "retail-customer@as.com")
    headers = {"x-vendor-slug": "as-demo"}
    mine = client.get("/api/store/my-orders", headers=headers)
    assert mine.status_code == 200, mine.text
    # seeded demo tracking order should be visible to linked customer
    codes = {o["order_code"] for o in mine.json()["data"]["data"]}
    assert "SO-DEMO-TRACK-1" in codes
    demo = next(o for o in mine.json()["data"]["data"] if o["order_code"] == "SO-DEMO-TRACK-1")
    assert demo["courier"] == "AKR_PARCEL"
    assert demo["tracking_number"] == "AKR-DEMO-1001"

    # cannot open foreign order id (admin-created unrelated)
    foreign = client.get("/api/store/my-orders/99999999", headers=headers)
    assert foreign.status_code == 404
