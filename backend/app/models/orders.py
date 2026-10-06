"""Phase 4 — PO / SO / GRN / returns / adjustments / status events."""

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("vendor_id", "order_code", name="uq_po_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    order_code: Mapped[str] = mapped_column(String(50), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id"), nullable=False)
    total_gross_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_net_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    freight_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    packing_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_purchase_cost: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNPAID")
    supplier_invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    supplier_invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PurchaseOrderDetail(Base):
    __tablename__ = "purchase_order_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity_ordered: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_received: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    line_gross_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    net_line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    taxable_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    gst_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (UniqueConstraint("vendor_id", "receipt_code", name="uq_grn_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_orders.id"), nullable=False, index=True
    )
    receipt_code: Mapped[str] = mapped_column(String(50), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    received_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="POSTED")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class GoodsReceiptLine(Base):
    __tablename__ = "goods_receipt_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    goods_receipt_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("goods_receipts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    purchase_order_detail_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_order_details.id"), nullable=False
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"
    __table_args__ = (UniqueConstraint("vendor_id", "return_code", name="uq_pr_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    purchase_order_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("purchase_orders.id"), nullable=True
    )
    return_code: Mapped[str] = mapped_column(String(50), nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="POSTED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class PurchaseReturnDetail(Base):
    __tablename__ = "purchase_return_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    purchase_return_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("purchase_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class SaleOrder(Base):
    __tablename__ = "sale_orders"
    __table_args__ = (UniqueConstraint("vendor_id", "order_code", name="uq_so_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    order_code: Mapped[str] = mapped_column(String(50), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    customer_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("customers.id"), nullable=True)
    placed_for_customer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("customers.id"), nullable=True, index=True
    )
    ordered_by_party_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("customers.id"), nullable=True, index=True
    )
    sales_channel: Mapped[str | None] = mapped_column(String(30), nullable=True, default="COUNTER")
    order_type: Mapped[str] = mapped_column(String(30), nullable=False, default="SALE")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    payment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNPAID")
    fulfillment_status: Mapped[str] = mapped_column(String(30), nullable=False, default="UNFULFILLED")
    total_gross_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_net_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_tax_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    shipping_charge: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    handling_charge: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_order_value: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    shipping_street: Mapped[str | None] = mapped_column(String(150), nullable=True)
    shipping_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipping_zip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    shipping_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_street: Mapped[str | None] = mapped_column(String(150), nullable=True)
    billing_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    billing_zip: Mapped[str | None] = mapped_column(String(20), nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    offer_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    placed_by_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    courier: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tracking_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class SaleOrderDetail(Base):
    __tablename__ = "sale_order_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    sale_order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sale_orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    item_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    item_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    trade_unit_price: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    margin_amount: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    line_gross_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    discount_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    net_line_total: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False)
    gst_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    taxable_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    gst_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    cgst_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    sgst_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    igst_amount: Mapped[float] = mapped_column(Numeric(14, 2), nullable=False, default=0)


class SaleReturn(Base):
    __tablename__ = "sale_returns"
    __table_args__ = (UniqueConstraint("vendor_id", "return_code", name="uq_sr_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    sale_order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("sale_orders.id"), nullable=True)
    return_code: Mapped[str] = mapped_column(String(50), nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="POSTED")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class SaleReturnDetail(Base):
    __tablename__ = "sale_return_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    sale_return_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sale_returns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)


class OrderStatusEvent(Base):
    __tablename__ = "order_status_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # SALE | PURCHASE
    order_id: Mapped[int] = mapped_column(Integer, nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StockAdjustment(Base):
    __tablename__ = "stock_adjustments"
    __table_args__ = (UniqueConstraint("vendor_id", "code", name="uq_adj_vendor_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    adjustment_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(40), nullable=False, default="ADJUSTMENT")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StockAdjustmentLine(Base):
    __tablename__ = "stock_adjustment_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    stock_adjustment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stock_adjustments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    item_id: Mapped[int] = mapped_column(Integer, ForeignKey("items.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("locations.id"), nullable=False)
    qty_delta: Mapped[int] = mapped_column(Integer, nullable=False)
