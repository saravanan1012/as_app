from app.core.gst import (
    aggregate_purchase_lines,
    aggregate_sale_lines,
    compute_line_gst_parts,
    round_money,
    split_gst,
)


def test_inclusive_gst_line():
    parts = compute_line_gst_parts(
        line_gross_total=118,
        discount_amount=0,
        gst_rate_percent=18,
        price_includes_gst=True,
    )
    assert parts.taxable_amount == 100.0
    assert parts.gst_amount == 18.0
    assert parts.net_line_total == 118.0


def test_exclusive_gst_line():
    parts = compute_line_gst_parts(
        line_gross_total=100,
        discount_amount=0,
        gst_rate_percent=18,
        price_includes_gst=False,
    )
    assert parts.taxable_amount == 100.0
    assert parts.gst_amount == 18.0
    assert parts.net_line_total == 118.0


def test_split_cgst_sgst_same_state():
    cgst, sgst, igst = split_gst(18, vendor_state="TN", place_state="TN")
    assert cgst == 9.0
    assert sgst == 9.0
    assert igst == 0.0


def test_split_igst_interstate():
    cgst, sgst, igst = split_gst(18, vendor_state="TN", place_state="KA")
    assert cgst == 0.0
    assert sgst == 0.0
    assert igst == 18.0


def test_aggregate_sale_and_purchase():
    sale = aggregate_sale_lines(
        [{"item_id": 1, "quantity": 2, "unit_price": 118, "discount_amount": 0}],
        {1: {"rate": 18, "includes": True}},
        vendor_state="TN",
        place_state="TN",
    )
    assert sale["sum_gross"] == 236.0
    assert sale["lines"][0]["cgst_amount"] == round_money(sale["lines"][0]["gst_amount"] / 2)

    po = aggregate_purchase_lines(
        [{"item_id": 1, "quantity_ordered": 10, "cost_price": 50, "discount_percentage": 10}],
        {1: {"rate": 5}},
    )
    # 500 gross, 50 disc → taxable 450, gst 22.5, net 472.5
    assert po["sum_gross"] == 500.0
    assert po["sum_discount"] == 50.0
    assert po["sum_tax"] == 22.5
    assert po["sum_net"] == 472.5
