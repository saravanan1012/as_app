from unittest.mock import patch

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


@pytest.mark.usefixtures("db_ready")
def test_public_contact_sends_email(client, monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("ORDER_NOTIFY_TO", "ops@example.com")
    from app.config import get_settings

    get_settings.cache_clear()
    with patch("app.services.email.notify_contact_enquiry", return_value=True) as notify:
        r = client.post(
            "/api/public/contact",
            headers={"x-vendor-slug": "as-demo"},
            json={
                "name": "Meena",
                "email": "meena@example.com",
                "phone": "9000000002",
                "subject": "Product question",
                "message": "Do you ship to Chennai?",
            },
        )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["sent"] is True
    notify.assert_called_once()
    get_settings.cache_clear()


@pytest.mark.usefixtures("db_ready")
def test_public_contact_requires_message(client):
    r = client.post(
        "/api/public/contact",
        headers={"x-vendor-slug": "as-demo"},
        json={"name": "Meena", "message": ""},
    )
    assert r.status_code == 422
