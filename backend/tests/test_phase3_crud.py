import uuid

import pytest


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _login_admin(client):
    r = client.post("/api/auth/login", json={"email": "admin@as.com", "password": "User@123"})
    assert r.status_code == 200, r.text
    return r


@pytest.mark.usefixtures("db_ready")
def test_customer_hierarchy_and_filters(client):
    _login_admin(client)

    dist = client.post(
        "/api/customers",
        json={
            "name": "North Dist",
            "party_type": "DISTRIBUTOR",
            "acquisition_source": "WALK_IN",
        },
    )
    assert dist.status_code == 201, dist.text
    dist_id = dist.json()["data"]["id"]

    # DISTRIBUTOR cannot have parent
    bad = client.post(
        "/api/customers",
        json={"name": "Bad Dist", "party_type": "DISTRIBUTOR", "parent_id": dist_id},
    )
    assert bad.status_code == 400

    dealer = client.post(
        "/api/customers",
        json={
            "name": "City Dealer",
            "party_type": "DEALER",
            "parent_id": dist_id,
            "acquisition_source": "REFERRAL",
        },
    )
    assert dealer.status_code == 201, dealer.text
    dealer_id = dealer.json()["data"]["id"]

    cust = client.post(
        "/api/customers",
        json={
            "name": "End Customer",
            "party_type": "CUSTOMER",
            "parent_id": dealer_id,
            "acquisition_source": "FB_LEAD",
            "acquisition_meta": {"campaign": "fb-spring"},
            "address": {"street": "1 Main", "city": "Chennai", "state": "TN", "zip": "600001"},
        },
    )
    assert cust.status_code == 201, cust.text

    # independent online customer
    online = client.post(
        "/api/customers",
        json={
            "name": "Online Buyer",
            "party_type": "CUSTOMER",
            "acquisition_source": "ONLINE",
        },
    )
    assert online.status_code == 201

    # CUSTOMER cannot be parent
    bad_parent = client.post(
        "/api/customers",
        json={
            "name": "Orphan",
            "party_type": "CUSTOMER",
            "parent_id": cust.json()["data"]["id"],
        },
    )
    assert bad_parent.status_code == 400

    filtered = client.get("/api/customers?party_type=DEALER")
    assert filtered.status_code == 200
    types = {c["party_type"] for c in filtered.json()["data"]["data"]}
    assert types == {"DEALER"}

    detail = client.get(f"/api/customers/{dist_id}")
    assert detail.status_code == 200
    assert any(ch["id"] == dealer_id for ch in detail.json()["data"]["children"])


@pytest.mark.usefixtures("db_ready")
def test_items_stock_isolation(client):
    _login_admin(client)
    code = f"P3-{_uid()}"
    item = client.post(
        "/api/items",
        json={"code": code, "name": f"Phase3 Item {code}", "sale_price": 100, "cost_price": 50},
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]

    locs = client.get("/api/locations")
    assert locs.status_code == 200
    loc_id = locs.json()["data"][0]["id"]

    stock = client.post(
        "/api/stock",
        json={"item_id": item_id, "location_id": loc_id, "quantity_on_hand": 25, "reorder_level": 5},
    )
    assert stock.status_code in (200, 201), stock.text

    # staff of vendor 1 cannot see vendor 2 via admin2 — create item as admin2
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "admin2@as.com", "password": "User@123"})
    items_v2 = client.get("/api/items")
    assert items_v2.status_code == 200
    codes = {i["code"] for i in items_v2.json()["data"]["data"]}
    assert code not in codes


@pytest.mark.usefixtures("db_ready")
def test_vendor_dashboard_and_supplier(client):
    _login_admin(client)
    dash = client.get("/api/dashboard")
    assert dash.status_code == 200
    assert "customers_by_party_type" in dash.json()["data"]

    suf = _uid()
    sup = client.post(
        "/api/suppliers",
        json={"code": f"S{suf}"[:20], "name": "Acme Supplies", "phone": "999"},
    )
    assert sup.status_code == 201, sup.text

    offer = client.post(
        "/api/offers",
        json={"code": f"SAVE{suf}"[:50], "discount_percentage": 10, "customer_type": "CUSTOMER"},
    )
    assert offer.status_code == 201, offer.text
