import uuid
from datetime import date

import pytest


def _uid() -> str:
    return uuid.uuid4().hex[:8]


def _login_admin(client):
    r = client.post("/api/auth/login", json={"email": "admin@as.com", "password": "User@123"})
    assert r.status_code == 200, r.text
    return r


def _setup_catalog(client, suffix: str):
    tax = client.post(
        "/api/tax-categories",
        json={"code": f"G18{suffix}", "name": "GST 18", "gst_rate": 18},
    )
    assert tax.status_code == 201, tax.text
    tax_id = tax.json()["data"]["id"]

    item = client.post(
        "/api/items",
        json={
            "code": f"P4{suffix}",
            "name": f"Phase4 Item {suffix}",
            "sale_price": 118,
            "cost_price": 50,
            "sale_price_includes_gst": True,
            "tax_category_id": tax_id,
        },
    )
    assert item.status_code == 201, item.text
    item_id = item.json()["data"]["id"]

    locs = client.get("/api/locations")
    loc_id = locs.json()["data"][0]["id"]

    sup = client.post(
        "/api/suppliers",
        json={"code": f"S{suffix}"[:20], "name": f"Supplier {suffix}"},
    )
    assert sup.status_code == 201, sup.text
    supplier_id = sup.json()["data"]["id"]

    cust = client.post(
        "/api/customers",
        json={"name": f"Buyer {suffix}", "party_type": "CUSTOMER", "acquisition_source": "WALK_IN"},
    )
    assert cust.status_code == 201, cust.text
    customer_id = cust.json()["data"]["id"]

    return item_id, loc_id, supplier_id, customer_id


@pytest.mark.usefixtures("db_ready")
def test_po_grn_so_stock_ledger(client):
    _login_admin(client)
    suf = _uid()
    item_id, loc_id, supplier_id, customer_id = _setup_catalog(client, suf)

    # Set vendor state via platform? Use shipping_state match — vendor may have null state.
    # Force CGST path by leaving vendor state empty → IGST; still fine for stock test.

    po = client.post(
        "/api/purchase-orders",
        json={
            "order_code": f"PO-{suf}",
            "order_date": str(date.today()),
            "supplier_id": supplier_id,
            "status": "ORDERED",
            "items": [
                {
                    "item_id": item_id,
                    "location_id": loc_id,
                    "quantity_ordered": 20,
                    "cost_price": 50,
                }
            ],
        },
    )
    assert po.status_code == 201, po.text
    po_body = po.json()["data"]
    assert po_body["status"] == "ORDERED"
    assert float(po_body["total_tax_amount"]) == 180.0  # 20*50 exclusive 18%
    po_id = po_body["id"]
    detail_id = po_body["items"][0]["id"]

    # Stock still zero before GRN
    stock = client.get("/api/stock")
    qty_before = next(
        (s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id),
        0,
    )
    assert qty_before == 0

    grn = client.post(
        f"/api/purchase-orders/{po_id}/receive",
        json={
            "receipt_code": f"GRN-{suf}",
            "lines": [{"purchase_order_detail_id": detail_id, "quantity": 10}],
        },
    )
    assert grn.status_code == 201, grn.text
    assert grn.json()["data"]["purchase_order"]["status"] == "PARTIAL_RECEIVED"

    stock = client.get("/api/stock")
    qty = next(s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id)
    assert qty == 10

    grn2 = client.post(
        f"/api/purchase-orders/{po_id}/receive",
        json={
            "receipt_code": f"GRN2-{suf}",
            "lines": [{"purchase_order_detail_id": detail_id, "quantity": 10}],
        },
    )
    assert grn2.status_code == 201, grn2.text
    assert grn2.json()["data"]["purchase_order"]["status"] == "RECEIVED"

    # Confirmed SO deducts
    so = client.post(
        "/api/sale-orders",
        json={
            "order_code": f"SO-{suf}",
            "order_date": str(date.today()),
            "customer_id": customer_id,
            "status": "CONFIRMED",
            "shipping_state": "TN",
            "items": [
                {
                    "item_id": item_id,
                    "location_id": loc_id,
                    "quantity": 5,
                    "unit_price": 118,
                }
            ],
        },
    )
    assert so.status_code == 201, so.text
    so_body = so.json()["data"]
    assert so_body["status"] == "CONFIRMED"
    assert float(so_body["items"][0]["gst_amount"]) == 90.0  # 5*118 inclusive → taxable 500, gst 90
    so_id = so_body["id"]

    stock = client.get("/api/stock")
    qty = next(s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id)
    assert qty == 15

    # Cancel restores
    cancel = client.post(f"/api/sale-orders/{so_id}/cancel", json={"reason": "test"})
    assert cancel.status_code == 200, cancel.text
    assert cancel.json()["data"]["status"] == "CANCELLED"

    stock = client.get("/api/stock")
    qty = next(s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id)
    assert qty == 20

    mov = client.get(f"/api/stock-movements?item_id={item_id}")
    assert mov.status_code == 200
    reasons = {m["reason"] for m in mov.json()["data"]["data"]}
    assert "PO_RECEIVE" in reasons
    assert "SO_SALE" in reasons
    assert "SO_CANCEL" in reasons


@pytest.mark.usefixtures("db_ready")
def test_so_insufficient_stock_and_draft_confirm(client):
    _login_admin(client)
    suf = _uid()
    item_id, loc_id, _, customer_id = _setup_catalog(client, suf)

    # Draft does not deduct
    draft = client.post(
        "/api/sale-orders",
        json={
            "order_code": f"SOD-{suf}",
            "order_date": str(date.today()),
            "customer_id": customer_id,
            "status": "DRAFT",
            "items": [{"item_id": item_id, "location_id": loc_id, "quantity": 3, "unit_price": 118}],
        },
    )
    assert draft.status_code == 201, draft.text
    so_id = draft.json()["data"]["id"]

    # Confirm without stock fails
    bad = client.post(f"/api/sale-orders/{so_id}/confirm")
    assert bad.status_code == 400
    assert "Insufficient" in bad.json()["message"]

    # Adjust stock up
    adj = client.post(
        "/api/stock-adjustments",
        json={
            "code": f"ADJ-{suf}",
            "adjustment_date": str(date.today()),
            "items": [{"item_id": item_id, "location_id": loc_id, "qty_delta": 10}],
        },
    )
    assert adj.status_code == 201, adj.text

    ok = client.post(f"/api/sale-orders/{so_id}/confirm")
    assert ok.status_code == 200, ok.text
    assert ok.json()["data"]["status"] == "CONFIRMED"

    stock = client.get("/api/stock")
    qty = next(s["quantity_on_hand"] for s in stock.json()["data"] if s["item_id"] == item_id)
    assert qty == 7
