"""India PIN → GST state helpers (static 3-digit prefix map)."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_PIN_RE = re.compile(r"^\d{6}$")

STATE_NAMES: dict[str, str] = {
    "AN": "Andaman and Nicobar Islands",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CH": "Chandigarh",
    "CT": "Chhattisgarh",
    "DL": "Delhi",
    "DN": "Dadra and Nagar Haveli and Daman and Diu",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HP": "Himachal Pradesh",
    "HR": "Haryana",
    "JH": "Jharkhand",
    "JK": "Jammu and Kashmir",
    "KA": "Karnataka",
    "KL": "Kerala",
    "LA": "Ladakh",
    "LD": "Lakshadweep",
    "MH": "Maharashtra",
    "ML": "Meghalaya",
    "MN": "Manipur",
    "MP": "Madhya Pradesh",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OR": "Odisha",
    "PB": "Punjab",
    "PY": "Puducherry",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TR": "Tripura",
    "TS": "Telangana",
    "UK": "Uttarakhand",
    "UP": "Uttar Pradesh",
    "WB": "West Bengal",
}


def normalize_pin(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) != 6:
        return None
    if not _PIN_RE.match(digits):
        return None
    return digits


@lru_cache(maxsize=1)
def _prefix_map() -> dict[str, str]:
    path = Path(__file__).resolve().parent.parent / "data" / "pin_prefix_to_state.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): str(v).strip().upper()[:2] for k, v in raw.items() if k and v}


def state_from_pin(pin: str | None) -> str | None:
    normalized = normalize_pin(pin)
    if not normalized:
        return None
    return _prefix_map().get(normalized[:3])


def state_name(code: str | None) -> str | None:
    if not code:
        return None
    return STATE_NAMES.get(code.strip().upper()[:2])


def lookup_pin(pin: str | None) -> dict[str, str | None] | None:
    normalized = normalize_pin(pin)
    if not normalized:
        return None
    code = state_from_pin(normalized)
    if not code:
        return {
            "pin": normalized,
            "state_code": None,
            "state_name": None,
        }
    return {
        "pin": normalized,
        "state_code": code,
        "state_name": state_name(code),
    }
