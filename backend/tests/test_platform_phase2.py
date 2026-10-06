import pytest


def _login(client, email="superadmin@as.com", password="User@123"):
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return r


@pytest.mark.usefixtures("db_ready")
def test_dashboard_requires_super_admin(client):
    _login(client, "staff@as.com")
    r = client.get("/api/platform/dashboard")
    assert r.status_code == 403


@pytest.mark.usefixtures("db_ready")
def test_dashboard_ok(client):
    _login(client)
    r = client.get("/api/platform/dashboard")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["vendors"]["total"] >= 2
    assert "vendors_detail" in data


@pytest.mark.usefixtures("db_ready")
def test_toggle_store_and_settings(client):
    _login(client)
    vendors = client.get("/api/platform/vendors").json()["data"]
    vid = vendors[0]["id"]

    r = client.patch(f"/api/platform/vendors/{vid}/store", json={"store_enabled": True})
    assert r.status_code == 200
    assert r.json()["data"]["store_enabled"] is True

    r = client.patch(
        f"/api/platform/vendors/{vid}/settings",
        json={
            "branding": {
                "theme_id": "matte_gold",
                "company_blurb": "Phase 2 test blurb",
                "primary": "#D4AF7C",
            },
            "shipping": {"flat_rate": 40},
        },
    )
    assert r.status_code == 200
    settings = r.json()["data"]["settings"]
    assert settings["features"]["store_enabled"] is True
    assert settings["branding"]["company_blurb"] == "Phase 2 test blurb"
    assert settings["shipping"]["flat_rate"] == 40
    assert r.json()["data"]["store_enabled"] is True

    # disable store
    r = client.patch(f"/api/platform/vendors/{vid}/store", json={"store_enabled": False})
    assert r.status_code == 200
    assert r.json()["data"]["store_enabled"] is False


@pytest.mark.usefixtures("db_ready")
def test_create_vendor_with_admin_and_bootstrap(client):
    import uuid

    _login(client)
    suffix = uuid.uuid4().hex[:8]
    slug = f"phase2-{suffix}"
    admin_email = f"p2admin-{suffix}@as.com"

    r = client.post(
        "/api/platform/vendors",
        json={
            "name": "Phase 2 Shop",
            "slug": slug,
            "plan": "BASIC",
            "admin_email": admin_email,
            "admin_name": "P2 Admin",
            "admin_password": "User@12345",
            "settings": {"branding": {"theme_id": "matte_gold", "store_name": "P2"}},
        },
    )
    assert r.status_code == 201, r.text
    vendor = r.json()["data"]
    assert vendor["slug"] == slug
    assert vendor["theme_id"] == "matte_gold"
    assert vendor["default_location_id"] is not None

    detail = client.get(f"/api/platform/vendors/{vendor['id']}").json()["data"]
    assert "storage_path" in detail
    assert str(vendor["id"]) in detail["storage_path"]

    client.post("/api/auth/logout")
    login = client.post(
        "/api/auth/login",
        json={"email": admin_email, "password": "User@12345"},
    )
    assert login.status_code == 200
    assert login.json()["data"]["role"] == "ADMIN"
    assert login.json()["data"]["vendor_id"] == vendor["id"]


@pytest.mark.usefixtures("db_ready")
def test_suspend_activate(client):
    _login(client)
    vendors = client.get("/api/platform/vendors").json()["data"]
    vid = next(v["id"] for v in vendors if v["slug"] == "vendor-two")

    r = client.post(f"/api/platform/vendors/{vid}/suspend")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "SUSPENDED"
    assert r.json()["data"]["suspended_at"] is not None

    r = client.post(f"/api/platform/vendors/{vid}/activate")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ACTIVE"


@pytest.mark.usefixtures("db_ready")
def test_bootstrap_admin_endpoint(client):
    _login(client)
    vendors = client.get("/api/platform/vendors").json()["data"]
    vid = next(v["id"] for v in vendors if v["slug"] == "as-demo")
    r = client.post(
        f"/api/platform/vendors/{vid}/bootstrap-admin",
        json={
            "email": "as-demo-mgr@as.com",
            "name": "Demo Manager",
            "password": "User@12345",
            "role": "MANAGER",
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["data"]["role"] == "MANAGER"
