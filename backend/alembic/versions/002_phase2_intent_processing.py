"""Alembic migration v002 — Phase 2 intent processing tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("usl_items", sa.Column("match_status", sa.String(32), server_default="queued", nullable=False))
    op.create_index("ix_usl_items_match_status", "usl_items", ["match_status"])

    op.create_table(
        "usl_item_metadata",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usl_items.item_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("attributes", postgresql.JSONB()),
        sa.Column("intent_confidence", sa.Float()),
        sa.Column("tags", postgresql.JSONB()),
        sa.Column("shortlist_size", sa.Integer()),
        sa.Column("processing_latency_ms", sa.Integer()),
        sa.Column("last_processed_at", sa.DateTime(timezone=True)),
        sa.Column("last_error", sa.Text()),
    )

    op.create_table(
        "catalog_matches",
        sa.Column("match_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("usl_items.item_id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku_id", sa.String(64), sa.ForeignKey("catalog_products.sku_id", ondelete="CASCADE"), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("availability_status", sa.String(32), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("matched_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_catalog_matches_item_id", "catalog_matches", ["item_id"])

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE catalog_product_embeddings (
            sku_id VARCHAR(64) PRIMARY KEY REFERENCES catalog_products(sku_id) ON DELETE CASCADE,
            embedding vector(384) NOT NULL,
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.drop_table("catalog_product_embeddings")
    op.drop_index("ix_catalog_matches_item_id", table_name="catalog_matches")
    op.drop_table("catalog_matches")
    op.drop_table("usl_item_metadata")
    op.drop_index("ix_usl_items_match_status", table_name="usl_items")
    op.drop_column("usl_items", "match_status")
