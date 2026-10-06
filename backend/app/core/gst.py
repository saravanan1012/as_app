"""GST helpers ported from legacy src/utils/gst.ts"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def round_money(n: float) -> float:
    return round(float(n) * 100) / 100


def normalize_gstin(value: str | None) -> str | None:
    if value is None:
        return None
    s = "".join(str(value).split()).upper()
    return s or None


@dataclass
class LineGstBreakdown:
    taxable_amount: float
    gst_amount: float
    net_line_total: float


def compute_line_gst_parts(
    *,
    line_gross_total: float,
    discount_amount: float,
    gst_rate_percent: float,
    price_includes_gst: bool,
) -> LineGstBreakdown:
    L = round_money(line_gross_total - discount_amount)
    r = gst_rate_percent / 100
    if price_includes_gst:
        if r <= 0:
            return LineGstBreakdown(L, 0, L)
        taxable = round_money(L / (1 + r))
        gst = round_money(L - taxable)
        return LineGstBreakdown(taxable, gst, L)
    taxable = L
    gst = 0 if r <= 0 else round_money(taxable * r)
    return LineGstBreakdown(taxable, gst, round_money(taxable + gst))


def split_gst(
    gst_amount: float,
    *,
    vendor_state: str | None,
    place_state: str | None,
) -> tuple[float, float, float]:
    """Return (cgst, sgst, igst)."""
    g = round_money(gst_amount)
    vs = (vendor_state or "").strip().upper()
    ps = (place_state or "").strip().upper()
    if g <= 0:
        return 0.0, 0.0, 0.0
    if vs and ps and vs == ps:
        half = round_money(g / 2)
        # fix rounding on second half
        return half, round_money(g - half), 0.0
    return 0.0, 0.0, g


def aggregate_sale_lines(
    raw_items: list[dict[str, Any]],
    gst_by_item: dict[int, dict[str, Any]],
    *,
    vendor_state: str | None = None,
    place_state: str | None = None,
) -> dict[str, Any]:
    sum_gross = sum_discount = sum_net = sum_tax = 0.0
    lines = []
    for item in raw_items:
        qty = int(item.get("quantity") or 0)
        unit = float(item.get("unit_price") or 0)
        line_gross = round_money(qty * unit)
        disc = round_money(float(item.get("discount_amount") or 0))
        meta = gst_by_item.get(int(item["item_id"]), {"rate": 0, "includes": True})
        parts = compute_line_gst_parts(
            line_gross_total=line_gross,
            discount_amount=disc,
            gst_rate_percent=float(meta.get("rate") or 0),
            price_includes_gst=bool(meta.get("includes", True)),
        )
        cgst, sgst, igst = split_gst(
            parts.gst_amount, vendor_state=vendor_state, place_state=place_state
        )
        sum_gross += line_gross
        sum_discount += disc
        sum_net += parts.net_line_total
        sum_tax += parts.gst_amount
        lines.append(
            {
                **item,
                "quantity": qty,
                "unit_price": unit,
                "line_gross_total": line_gross,
                "discount_percentage": float(item.get("discount_percentage") or 0),
                "discount_amount": disc,
                "net_line_total": parts.net_line_total,
                "gst_rate": float(meta.get("rate") or 0),
                "taxable_amount": parts.taxable_amount,
                "gst_amount": parts.gst_amount,
                "cgst_amount": cgst,
                "sgst_amount": sgst,
                "igst_amount": igst,
            }
        )
    return {
        "lines": lines,
        "sum_gross": round_money(sum_gross),
        "sum_discount": round_money(sum_discount),
        "sum_net": round_money(sum_net),
        "sum_tax": round_money(sum_tax),
    }


def allocate_order_discount_to_lines(
    items: list[dict[str, Any]],
    order_discount: float,
) -> list[dict[str, Any]]:
    """Spread order-level discount across lines by gross share."""
    discount = round_money(max(0.0, float(order_discount or 0)))
    if discount <= 0 or not items:
        return [
            {**item, "discount_amount": round_money(float(item.get("discount_amount") or 0))}
            for item in items
        ]
    grosses = [
        round_money(int(item.get("quantity") or 0) * float(item.get("unit_price") or 0))
        for item in items
    ]
    total_gross = round_money(sum(grosses))
    if total_gross <= 0:
        return items
    capped = min(discount, total_gross)
    allocated = 0.0
    out = []
    for idx, item in enumerate(items):
        is_last = idx == len(items) - 1
        share = round_money(capped - allocated) if is_last else round_money((grosses[idx] / total_gross) * capped)
        allocated = round_money(allocated + share)
        out.append(
            {
                **item,
                "discount_amount": round_money(float(item.get("discount_amount") or 0) + share),
            }
        )
    return out


def aggregate_purchase_lines(
    raw_items: list[dict[str, Any]],
    gst_by_item: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    sum_gross = sum_discount = sum_net = sum_tax = 0.0
    lines = []
    for item in raw_items:
        qty = int(item.get("quantity_ordered") or 0)
        cost = float(item.get("cost_price") or 0)
        line_gross = round_money(qty * cost)
        disc = round_money(float(item.get("discount_amount") or 0))
        pct = float(item.get("discount_percentage") or 0)
        if not disc and pct > 0:
            disc = round_money((line_gross * pct) / 100)
        rate = float(gst_by_item.get(int(item["item_id"]), {}).get("rate") or 0)
        parts = compute_line_gst_parts(
            line_gross_total=line_gross,
            discount_amount=disc,
            gst_rate_percent=rate,
            price_includes_gst=False,
        )
        sum_gross += line_gross
        sum_discount += disc
        sum_net += parts.net_line_total
        sum_tax += parts.gst_amount
        out_pct = round_money((disc / line_gross) * 100) if line_gross > 0 else pct
        lines.append(
            {
                **item,
                "quantity_ordered": qty,
                "cost_price": cost,
                "line_gross_total": line_gross,
                "discount_percentage": out_pct,
                "discount_amount": disc,
                "net_line_total": parts.net_line_total,
                "gst_rate": rate,
                "taxable_amount": parts.taxable_amount,
                "gst_amount": parts.gst_amount,
            }
        )
    return {
        "lines": lines,
        "sum_gross": round_money(sum_gross),
        "sum_discount": round_money(sum_discount),
        "sum_net": round_money(sum_net),
        "sum_tax": round_money(sum_tax),
    }
