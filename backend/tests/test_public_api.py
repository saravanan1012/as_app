import pytest


@pytest.mark.usefixtures("db_ready")
def test_public_vendor_without_store(client):
    # Store may be on/off — public vendor always works
    r = client.get("/api/public/vendor", headers={"x-vendor-slug": "as-demo"})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["slug"] == "as-demo"
    assert "store_enabled" in data
    assert "branding" in data
    assert data["branding"]["theme_id"] == "matte_gold"


@pytest.mark.usefixtures("db_ready")
def test_public_products_list(client):
    r = client.get("/api/public/products", headers={"x-vendor-slug": "as-demo"})
    assert r.status_code == 200
    assert "data" in r.json()["data"]
