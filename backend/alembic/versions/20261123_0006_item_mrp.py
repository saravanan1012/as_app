"""Add items.mrp for store strikethrough display pricing

Revision ID: 20261123_0006
Revises: 20261006_0005
Create Date: 2026-11-23

Backfills mrp = sale_price so existing catalog is unchanged in the UI
(no false “sale” badges). Does not require re-seeding.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261123_0006"
down_revision: Union[str, None] = "20261006_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("items", sa.Column("mrp", sa.Numeric(14, 2), nullable=True))
    op.execute(sa.text("UPDATE items SET mrp = sale_price WHERE mrp IS NULL"))
    op.alter_column(
        "items",
        "mrp",
        existing_type=sa.Numeric(14, 2),
        nullable=False,
        server_default="0",
    )


def downgrade() -> None:
    op.drop_column("items", "mrp")
