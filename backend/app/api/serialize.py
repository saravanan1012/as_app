from datetime import date, datetime
from decimal import Decimal
from typing import Any


def row(obj: Any, fields: list[str]) -> dict:
    out: dict[str, Any] = {}
    for f in fields:
        val = getattr(obj, f, None)
        if isinstance(val, Decimal):
            val = float(val)
        elif isinstance(val, (datetime, date)):
            val = val.isoformat()
        out[f] = val
    return out
