import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover - optional for SQLite tests
    Vector = None


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    location: Mapped["UserLocation | None"] = relationship(back_populates="user", uselist=False)
    usl_items: Mapped[list["UslItem"]] = relationship(back_populates="user")


class UserLocation(Base):
    __tablename__ = "user_locations"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True
    )
    city: Mapped[str] = mapped_column(String(128), nullable=False)
    state: Mapped[str] = mapped_column(String(128), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="location")


class UslItem(Base):
    __tablename__ = "usl_items"

    item_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    raw_intent: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(256))
    category: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    priority: Mapped[int | None] = mapped_column(Integer)
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    purchased_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    match_status: Mapped[str] = mapped_column(String(32), default="queued", index=True)

    user: Mapped["User"] = relationship(back_populates="usl_items")
    metadata_row: Mapped["UslItemMetadata | None"] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    catalog_matches: Mapped[list["CatalogMatch"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    availability_watches: Mapped[list["AvailabilityWatch"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )


class CatalogProduct(Base):
    __tablename__ = "catalog_products"

    sku_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text)
    attributes: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    matches: Mapped[list["CatalogMatch"]] = relationship(back_populates="product")
    embedding_row: Mapped["CatalogProductEmbedding | None"] = relationship(back_populates="product", uselist=False)


class ProductAvailability(Base):
    __tablename__ = "product_availability"

    sku_id: Mapped[str] = mapped_column(String(64), ForeignKey("catalog_products.sku_id", ondelete="CASCADE"), primary_key=True)
    pincode: Mapped[str] = mapped_column(String(10), primary_key=True)
    availability_status: Mapped[str] = mapped_column(String(32), default="available")
    quantity: Mapped[int] = mapped_column(Integer, default=10)


class UslItemMetadata(Base):
    __tablename__ = "usl_item_metadata"

    item_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usl_items.item_id", ondelete="CASCADE"), primary_key=True
    )
    attributes: Mapped[dict | None] = mapped_column(JSONB)
    intent_confidence: Mapped[float | None] = mapped_column(Float)
    tags: Mapped[list | None] = mapped_column(JSONB)
    shortlist_size: Mapped[int | None] = mapped_column(Integer)
    processing_latency_ms: Mapped[int | None] = mapped_column(Integer)
    last_processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)

    item: Mapped["UslItem"] = relationship(back_populates="metadata_row")


class CatalogMatch(Base):
    __tablename__ = "catalog_matches"

    match_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("usl_items.item_id", ondelete="CASCADE"))
    sku_id: Mapped[str] = mapped_column(String(64), ForeignKey("catalog_products.sku_id", ondelete="CASCADE"))
    match_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    availability_status: Mapped[str] = mapped_column(String(32), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    matched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    item: Mapped["UslItem"] = relationship(back_populates="catalog_matches")
    product: Mapped["CatalogProduct"] = relationship(back_populates="matches")


class CatalogProductEmbedding(Base):
    __tablename__ = "catalog_product_embeddings"

    sku_id: Mapped[str] = mapped_column(String(64), ForeignKey("catalog_products.sku_id", ondelete="CASCADE"), primary_key=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(384) if Vector else Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["CatalogProduct"] = relationship(back_populates="embedding_row")


class RecommendationEvent(Base):
    __tablename__ = "recommendation_events"

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    checkout_session_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recommendation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    item_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("usl_items.item_id", ondelete="SET NULL"), nullable=True
    )
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_type: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PurchaseHistory(Base):
    __tablename__ = "purchase_history"

    history_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    order_id: Mapped[str | None] = mapped_column(String(128))
    source: Mapped[str] = mapped_column(String(32), default="order")
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AvailabilityWatch(Base):
    __tablename__ = "availability_watches"

    watch_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    item_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("usl_items.item_id", ondelete="CASCADE"))
    sku_id: Mapped[str] = mapped_column(String(64), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    item: Mapped["UslItem"] = relationship(back_populates="availability_watches")
