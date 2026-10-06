"""phase10 b2b retailer price rules trade fields

Revision ID: 20261006_0005
Revises: 20261005_0004
Create Date: 2026-10-06

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261006_0005"
down_revision: Union[str, None] = "20261005_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "party_price_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("party_type", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("value", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACTIVE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "vendor_id", "item_id", "party_type", name="uq_party_price_vendor_item_type"
        ),
    )
    op.create_index("ix_party_price_rules_vendor_id", "party_price_rules", ["vendor_id"])
    op.create_index("ix_party_price_rules_item_id", "party_price_rules", ["item_id"])
    op.create_index("ix_party_price_rules_party_type", "party_price_rules", ["party_type"])

    op.add_column(
        "sale_orders",
        sa.Column("placed_for_customer_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "sale_orders",
        sa.Column("ordered_by_party_id", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_so_placed_for_customer",
        "sale_orders",
        "customers",
        ["placed_for_customer_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_so_ordered_by_party",
        "sale_orders",
        "customers",
        ["ordered_by_party_id"],
        ["id"],
    )
    op.create_index("ix_sale_orders_placed_for_customer_id", "sale_orders", ["placed_for_customer_id"])
    op.create_index("ix_sale_orders_ordered_by_party_id", "sale_orders", ["ordered_by_party_id"])

    op.add_column(
        "sale_order_details",
        sa.Column("trade_unit_price", sa.Numeric(14, 2), nullable=True),
    )
    op.add_column(
        "sale_order_details",
        sa.Column("margin_amount", sa.Numeric(14, 2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sale_order_details", "margin_amount")
    op.drop_column("sale_order_details", "trade_unit_price")
    op.drop_index("ix_sale_orders_ordered_by_party_id", table_name="sale_orders")
    op.drop_index("ix_sale_orders_placed_for_customer_id", table_name="sale_orders")
    op.drop_constraint("fk_so_ordered_by_party", "sale_orders", type_="foreignkey")
    op.drop_constraint("fk_so_placed_for_customer", "sale_orders", type_="foreignkey")
    op.drop_column("sale_orders", "ordered_by_party_id")
    op.drop_column("sale_orders", "placed_for_customer_id")
    op.drop_index("ix_party_price_rules_party_type", table_name="party_price_rules")
    op.drop_index("ix_party_price_rules_item_id", table_name="party_price_rules")
    op.drop_index("ix_party_price_rules_vendor_id", table_name="party_price_rules")
    op.drop_table("party_price_rules")
