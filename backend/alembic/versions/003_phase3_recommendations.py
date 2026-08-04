"""Alembic migration v003 — Phase 3 recommendation events."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendation_events",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("checkout_session_id", sa.String(128), nullable=False),
        sa.Column("recommendation_id", sa.String(64), nullable=False, index=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usl_items.item_id", ondelete="SET NULL"), nullable=True),
        sa.Column("sku_id", sa.String(64), nullable=False),
        sa.Column("reason_type", sa.String(64), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_recommendation_events_user_id", "recommendation_events", ["user_id"])
    op.create_index("ix_recommendation_events_checkout_session", "recommendation_events", ["checkout_session_id"])


def downgrade() -> None:
    op.drop_index("ix_recommendation_events_checkout_session", table_name="recommendation_events")
    op.drop_index("ix_recommendation_events_user_id", table_name="recommendation_events")
    op.drop_table("recommendation_events")
