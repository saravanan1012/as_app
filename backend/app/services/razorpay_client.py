"""Razorpay helpers — real API or mock for local/CI."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from typing import Any

import httpx

from app.config import get_settings


class RazorpayError(Exception):
    pass


def credentials_for_vendor(vendor_settings: dict | None) -> tuple[str, str, bool]:
    """Return (key_id, key_secret, mock). Vendor settings override env when set."""
    settings = get_settings()
    payments = (vendor_settings or {}).get("payments") or {}
    key_id = (payments.get("razorpay_key_id") or settings.razorpay_key_id or "").strip()
    secret_ref = (payments.get("razorpay_key_secret_ref") or "").strip()
    # secret_ref may be literal secret for staging, or empty → env
    key_secret = secret_ref if secret_ref and not secret_ref.startswith("env:") else settings.razorpay_key_secret
    if secret_ref.startswith("env:"):
        # e.g. env:RAZORPAY_KEY_SECRET — already on settings
        key_secret = settings.razorpay_key_secret
    mock = bool(settings.razorpay_mock) or not (key_id and key_secret)
    return key_id, key_secret, mock


def verify_payment_signature(
    *,
    order_id: str,
    payment_id: str,
    signature: str,
    secret: str,
) -> bool:
    body = f"{order_id}|{payment_id}"
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_webhook_signature(*, body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def create_order(
    *,
    amount_paise: int,
    currency: str,
    receipt: str,
    notes: dict[str, Any] | None,
    key_id: str,
    key_secret: str,
    mock: bool,
) -> dict[str, Any]:
    if amount_paise < 100:
        raise RazorpayError("Order total must be at least ₹1")
    if mock:
        oid = f"order_mock_{uuid.uuid4().hex[:16]}"
        return {
            "id": oid,
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
            "mock": True,
        }
    auth = (key_id, key_secret)
    payload = {
        "amount": amount_paise,
        "currency": currency,
        "receipt": receipt,
        "notes": notes or {},
    }
    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post("https://api.razorpay.com/v1/orders", json=payload, auth=auth)
        if r.status_code >= 400:
            raise RazorpayError(r.json().get("error", {}).get("description") or r.text)
        data = r.json()
        data["mock"] = False
        return data
    except httpx.HTTPError as e:
        raise RazorpayError(str(e)) from e


def mock_signature(order_id: str, payment_id: str, secret: str = "mock-secret") -> str:
    return hmac.new(secret.encode(), f"{order_id}|{payment_id}".encode(), hashlib.sha256).hexdigest()


def parse_webhook_event(body: bytes) -> dict[str, Any]:
    return json.loads(body.decode("utf-8"))
