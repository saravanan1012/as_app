"""phase4 po so grn returns adjustments events

Revision ID: 20261005_0003
Revises: 20261005_0002
Create Date: 2026-10-05

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261005_0003"
down_revision: Union[str, None] = "20261005_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("order_code", sa.String(length=50), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("total_gross_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_discount_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("freight_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("packing_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_purchase_cost", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False),
        sa.Column("supplier_invoice_number", sa.String(length=100), nullable=True),
        sa.Column("supplier_invoice_date", sa.Date(), nullable=True),
        sa.Column("expected_delivery_date", sa.Date(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "order_code", name="uq_po_vendor_code"),
    )
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"])

    op.create_table(
        "purchase_order_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False),
        sa.Column("cost_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_gross_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_amount", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_order_details_vendor_id", "purchase_order_details", ["vendor_id"])
    op.create_index("ix_purchase_order_details_purchase_order_id", "purchase_order_details", ["purchase_order_id"])

    op.create_table(
        "goods_receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=False),
        sa.Column("receipt_code", sa.String(length=50), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("received_by", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "receipt_code", name="uq_grn_vendor_code"),
    )
    op.create_index("ix_goods_receipts_vendor_id", "goods_receipts", ["vendor_id"])
    op.create_index("ix_goods_receipts_purchase_order_id", "goods_receipts", ["purchase_order_id"])

    op.create_table(
        "goods_receipt_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("goods_receipt_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_detail_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["goods_receipt_id"], ["goods_receipts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["purchase_order_detail_id"], ["purchase_order_details.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_goods_receipt_lines_vendor_id", "goods_receipt_lines", ["vendor_id"])
    op.create_index("ix_goods_receipt_lines_goods_receipt_id", "goods_receipt_lines", ["goods_receipt_id"])

    op.create_table(
        "purchase_returns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("purchase_order_id", sa.Integer(), nullable=True),
        sa.Column("return_code", sa.String(length=50), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "return_code", name="uq_pr_vendor_code"),
    )
    op.create_index("ix_purchase_returns_vendor_id", "purchase_returns", ["vendor_id"])

    op.create_table(
        "purchase_return_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("purchase_return_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["purchase_return_id"], ["purchase_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_return_details_vendor_id", "purchase_return_details", ["vendor_id"])
    op.create_index(
        "ix_purchase_return_details_purchase_return_id", "purchase_return_details", ["purchase_return_id"]
    )

    op.create_table(
        "sale_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("order_code", sa.String(length=50), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=True),
        sa.Column("sales_channel", sa.String(length=30), nullable=True),
        sa.Column("order_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False),
        sa.Column("fulfillment_status", sa.String(length=30), nullable=False),
        sa.Column("total_gross_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_discount_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_net_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_tax_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("shipping_charge", sa.Numeric(14, 2), nullable=False),
        sa.Column("handling_charge", sa.Numeric(14, 2), nullable=False),
        sa.Column("total_order_value", sa.Numeric(14, 2), nullable=False),
        sa.Column("shipping_street", sa.String(length=150), nullable=True),
        sa.Column("shipping_city", sa.String(length=100), nullable=True),
        sa.Column("shipping_state", sa.String(length=100), nullable=True),
        sa.Column("shipping_zip", sa.String(length=20), nullable=True),
        sa.Column("shipping_phone", sa.String(length=20), nullable=True),
        sa.Column("shipping_name", sa.String(length=100), nullable=True),
        sa.Column("billing_street", sa.String(length=150), nullable=True),
        sa.Column("billing_city", sa.String(length=100), nullable=True),
        sa.Column("billing_state", sa.String(length=100), nullable=True),
        sa.Column("billing_zip", sa.String(length=20), nullable=True),
        sa.Column("invoice_number", sa.String(length=50), nullable=True),
        sa.Column("invoice_date", sa.Date(), nullable=True),
        sa.Column("offer_code", sa.String(length=50), nullable=True),
        sa.Column("payment_method", sa.String(length=50), nullable=True),
        sa.Column("razorpay_order_id", sa.String(length=100), nullable=True),
        sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True),
        sa.Column("placed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.Text(), nullable=True),
        sa.Column("courier", sa.String(length=100), nullable=True),
        sa.Column("tracking_number", sa.String(length=100), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.ForeignKeyConstraint(["placed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "order_code", name="uq_so_vendor_code"),
    )
    op.create_index("ix_sale_orders_vendor_id", "sale_orders", ["vendor_id"])
    op.create_index("ix_sale_orders_vendor_status_date", "sale_orders", ["vendor_id", "status", "order_date"])

    op.create_table(
        "sale_order_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("sale_order_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=50), nullable=True),
        sa.Column("item_name", sa.String(length=100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("line_gross_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount_percentage", sa.Numeric(5, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("net_line_total", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("taxable_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("gst_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("cgst_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("sgst_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("igst_amount", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["sale_order_id"], ["sale_orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sale_order_details_vendor_id", "sale_order_details", ["vendor_id"])
    op.create_index("ix_sale_order_details_sale_order_id", "sale_order_details", ["sale_order_id"])

    op.create_table(
        "sale_returns",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("sale_order_id", sa.Integer(), nullable=True),
        sa.Column("return_code", sa.String(length=50), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["sale_order_id"], ["sale_orders.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "return_code", name="uq_sr_vendor_code"),
    )
    op.create_index("ix_sale_returns_vendor_id", "sale_returns", ["vendor_id"])

    op.create_table(
        "sale_return_details",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("sale_return_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["sale_return_id"], ["sale_returns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sale_return_details_vendor_id", "sale_return_details", ["vendor_id"])
    op.create_index("ix_sale_return_details_sale_return_id", "sale_return_details", ["sale_return_id"])

    op.create_table(
        "order_status_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("order_type", sa.String(length=20), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=30), nullable=True),
        sa.Column("to_status", sa.String(length=30), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_status_events_vendor_id", "order_status_events", ["vendor_id"])
    op.create_index(
        "ix_order_status_events_order", "order_status_events", ["vendor_id", "order_type", "order_id"]
    )

    op.create_table(
        "stock_adjustments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("adjustment_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.String(length=40), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vendor_id", "code", name="uq_adj_vendor_code"),
    )
    op.create_index("ix_stock_adjustments_vendor_id", "stock_adjustments", ["vendor_id"])

    op.create_table(
        "stock_adjustment_lines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("stock_adjustment_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("location_id", sa.Integer(), nullable=False),
        sa.Column("qty_delta", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"]),
        sa.ForeignKeyConstraint(["stock_adjustment_id"], ["stock_adjustments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_adjustment_lines_vendor_id", "stock_adjustment_lines", ["vendor_id"])
    op.create_index(
        "ix_stock_adjustment_lines_stock_adjustment_id", "stock_adjustment_lines", ["stock_adjustment_id"]
    )


def downgrade() -> None:
    op.drop_table("stock_adjustment_lines")
    op.drop_table("stock_adjustments")
    op.drop_table("order_status_events")
    op.drop_table("sale_return_details")
    op.drop_table("sale_returns")
    op.drop_table("sale_order_details")
    op.drop_table("sale_orders")
    op.drop_table("purchase_return_details")
    op.drop_table("purchase_returns")
    op.drop_table("goods_receipt_lines")
    op.drop_table("goods_receipts")
    op.drop_table("purchase_order_details")
    op.drop_table("purchase_orders")
