"""Unit tests for new-order SMTP notify (no real network)."""

from datetime import date
from unittest.mock import MagicMock, patch

from app.config import get_settings
from app.services import email as email_svc


def test_smtp_configured_false_without_host(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.setenv("SMTP_PASSWORD", "x")
    monkeypatch.setenv("ORDER_NOTIFY_TO", "a@b.com")
    get_settings.cache_clear()
    assert email_svc.smtp_configured() is False
    get_settings.cache_clear()


def test_send_email_uses_smtp(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "587")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_FROM", "AS Signature <user@example.com>")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    get_settings.cache_clear()

    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)

    with patch("app.services.email.smtplib.SMTP", return_value=mock_server) as smtp_cls:
        ok = email_svc.send_email(
            to=["ops@example.com"],
            subject="Test",
            text_body="hello",
            html_body="<p>hello</p>",
        )

    assert ok is True
    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("user@example.com", "secret")
    mock_server.sendmail.assert_called_once()
    get_settings.cache_clear()


def test_notify_new_order_builds_and_sends(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("ORDER_NOTIFY_TO", "ops@example.com")
    get_settings.cache_clear()

    so = MagicMock()
    so.id = 1
    so.vendor_id = 1
    so.order_code = "SO-TEST-1"
    so.order_date = date(2026, 11, 15)
    so.status = "CONFIRMED"
    so.payment_status = "UNPAID"
    so.payment_method = "COD"
    so.sales_channel = "ECOMMERCE"
    so.total_order_value = 500
    so.shipping_charge = 40
    so.customer_id = 9
    so.shipping_name = "Priya"
    so.shipping_street = "12 Main"
    so.shipping_city = "Chennai"
    so.shipping_state = "TN"
    so.shipping_zip = "600001"
    so.shipping_phone = "9999999999"

    detail = MagicMock()
    detail.item_name = "Neem Oil"
    detail.item_code = "DEMO-1"
    detail.item_id = 1
    detail.quantity = 2
    detail.unit_price = 200

    customer = MagicMock()
    customer.name = "Priya"
    customer.email = "priya@example.com"
    customer.phone = None

    db = MagicMock()
    db.scalars.return_value.all.return_value = [detail]
    db.get.return_value = customer

    with patch("app.services.email.send_email", return_value=True) as send:
        ok = email_svc.notify_new_order(db, so)

    assert ok is True
    send.assert_called_once()
    kwargs = send.call_args.kwargs
    assert kwargs["to"] == ["ops@example.com"]
    assert "SO-TEST-1" in kwargs["subject"]
    assert "Neem Oil" in kwargs["text_body"]
    assert "Priya" in kwargs["text_body"]
    get_settings.cache_clear()


def test_notify_contact_enquiry_builds_and_sends(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_USER", "user@example.com")
    monkeypatch.setenv("ORDER_NOTIFY_TO", "ops@example.com")
    get_settings.cache_clear()

    with patch("app.services.email.send_email", return_value=True) as send:
        ok = email_svc.notify_contact_enquiry(
            name="Karthik",
            email="karthik@example.com",
            phone="9000000001",
            subject="Wholesale",
            message="Need dealer pricing",
            vendor_name="AS Demo",
        )

    assert ok is True
    send.assert_called_once()
    kwargs = send.call_args.kwargs
    assert kwargs["to"] == ["ops@example.com"]
    assert kwargs["reply_to"] == "karthik@example.com"
    assert "Wholesale" in kwargs["subject"]
    assert "Karthik" in kwargs["text_body"]
    assert "Need dealer pricing" in kwargs["text_body"]
    get_settings.cache_clear()
