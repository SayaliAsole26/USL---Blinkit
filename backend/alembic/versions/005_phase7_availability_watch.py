"""Phase 7 — notify when available subscriptions."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "availability_watches",
        sa.Column("watch_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usl_items.item_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku_id", sa.String(64), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("notified_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_availability_watches_user_id", "availability_watches", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_availability_watches_user_id", "availability_watches")
    op.drop_table("availability_watches")
