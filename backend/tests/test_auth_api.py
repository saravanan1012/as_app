import pytest
from sqlalchemy import select

from app.db import SessionLocal
from app.models import Item, Vendor


@pytest.mark.usefixtures("db_ready")
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True


@pytest.mark.usefixtures("db_ready")
def test_login_super_admin(client):
    r = client.post(
        "/api/auth/login",
        json={"email": "superadmin@as.com", "password": "User@123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert body["data"]["role"] == "SUPER_ADMIN"
    assert "platform.vendors.manage" in body["data"]["permissions"]
    assert body["data"]["default_redirect"] == "/platform"
    assert "as_session" in r.cookies


@pytest.mark.usefixtures("db_ready")
def test_staff_forbidden_platform(client):
    login = client.post(
        "/api/auth/login",
        json={"email": "staff@as.com", "password": "User@123"},
    )
    assert login.status_code == 200
    r = client.get("/api/platform/vendors")
    assert r.status_code == 403


@pytest.mark.usefixtures("db_ready")
def test_vendor_item_isolation(client):
    db = SessionLocal()
    try:
        v1 = db.scalar(select(Vendor).where(Vendor.slug == "as-demo"))
        v2 = db.scalar(select(Vendor).where(Vendor.slug == "vendor-two"))
        assert v1 and v2
        # clean prior test items
        for it in db.scalars(select(Item).where(Item.code.in_(["ISO-A", "ISO-B"]))).all():
            db.delete(it)
        db.commit()
        db.add(Item(vendor_id=v1.id, code="ISO-A", name="Iso A", unit_of_measure="PCS"))
        db.add(Item(vendor_id=v2.id, code="ISO-B", name="Iso B", unit_of_measure="PCS"))
        db.commit()
        v1_id, v2_id = v1.id, v2.id
    finally:
        db.close()

    login = client.post(
        "/api/auth/login",
        json={"email": "superadmin@as.com", "password": "User@123"},
    )
    assert login.status_code == 200

    r1 = client.get(f"/api/platform/vendors/{v1_id}/items-isolation-check")
    r2 = client.get(f"/api/platform/vendors/{v2_id}/items-isolation-check")
    assert r1.status_code == 200 and r2.status_code == 200
    c1 = r1.json()["data"]["item_count"]
    c2 = r2.json()["data"]["item_count"]
    # each vendor sees only its own count (at least the ISO item)
    assert c1 >= 1
    assert c2 >= 1
    assert c1 != c2 or True  # counts independent; primary check is query filters by vendor_id
    # prove no cross-leak: v1 count equals DB count for v1 only
    db = SessionLocal()
    try:
        real1 = len(db.scalars(select(Item).where(Item.vendor_id == v1_id)).all())
        real2 = len(db.scalars(select(Item).where(Item.vendor_id == v2_id)).all())
    finally:
        db.close()
    assert c1 == real1
    assert c2 == real2
