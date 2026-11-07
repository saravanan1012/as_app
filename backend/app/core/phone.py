"""Normalize and match mobile numbers for login / registration."""

from __future__ import annotations

import re

_DIGITS = re.compile(r"\D+")


def normalize_phone(raw: str | None) -> str | None:
    """Return a compact digit phone (prefer last 10 for IN +91), or None if too short."""
    if not raw:
        return None
    digits = _DIGITS.sub("", raw.strip())
    if not digits:
        return None
    if len(digits) >= 12 and digits.startswith("91"):
        digits = digits[-10:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) < 8:
        return None
    return digits


def phone_lookup_variants(raw: str | None) -> list[str]:
    """Variants to match against User.phone / Customer.phone storage styles."""
    phone = normalize_phone(raw)
    if not phone:
        return []
    variants = {phone, f"91{phone}", f"+91{phone}", f"0{phone}"}
    return list(variants)


def looks_like_email(value: str) -> bool:
    return "@" in (value or "").strip()
