"""Alembic migration v001 — core Phase 0 tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("onboarding_completed", sa.Boolean(), server_default=sa.text("false")),
    )

    op.create_table(
        "user_locations",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("city", sa.String(128), nullable=False),
        sa.Column("state", sa.String(128), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_user_locations_pincode", "user_locations", ["pincode"])

    op.create_table(
        "usl_items",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("raw_intent", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.String(256)),
        sa.Column("category", sa.String(128)),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column("priority", sa.Integer()),
        sa.Column("event_date", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("purchased_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_usl_items_status", "usl_items", ["status"])

    op.create_table(
        "catalog_products",
        sa.Column("sku_id", sa.String(64), primary_key=True),
        sa.Column("product_name", sa.String(512), nullable=False),
        sa.Column("category", sa.String(128), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("image_url", sa.Text()),
        sa.Column("attributes", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_catalog_products_category", "catalog_products", ["category"])

    op.create_table(
        "product_availability",
        sa.Column("sku_id", sa.String(64), sa.ForeignKey("catalog_products.sku_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("pincode", sa.String(10), primary_key=True),
        sa.Column("availability_status", sa.String(32), server_default="available"),
        sa.Column("quantity", sa.Integer(), server_default="10"),
    )


def downgrade() -> None:
    op.drop_table("product_availability")
    op.drop_table("catalog_products")
    op.drop_table("usl_items")
    op.drop_table("user_locations")
    op.drop_table("users")
