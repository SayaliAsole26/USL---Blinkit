"""Alembic migration v004 — Phase 5 purchase history."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "purchase_history",
        sa.Column("history_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sku_id", sa.String(64), nullable=False),
        sa.Column("product_name", sa.String(512), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("order_id", sa.String(128), nullable=True),
        sa.Column("source", sa.String(32), nullable=False, server_default="order"),
        sa.Column("purchased_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_purchase_history_user_id", "purchase_history", ["user_id"])
    op.create_index("ix_purchase_history_user_sku", "purchase_history", ["user_id", "sku_id"])
    op.create_index("ix_purchase_history_purchased_at", "purchase_history", ["purchased_at"])


def downgrade() -> None:
    op.drop_index("ix_purchase_history_purchased_at", table_name="purchase_history")
    op.drop_index("ix_purchase_history_user_sku", table_name="purchase_history")
    op.drop_index("ix_purchase_history_user_id", table_name="purchase_history")
    op.drop_table("purchase_history")
