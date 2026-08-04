from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class UslItemStatus(StrEnum):
    PENDING = "pending"
    SAVED_FOR_LATER = "saved_for_later"
    DISMISSED = "dismissed"
    PURCHASED = "purchased"


class MatchStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    MATCHED = "matched"
    UNMATCHED = "unmatched"


class UslItemCreate(BaseModel):
    raw_intent: str = Field(..., min_length=1, max_length=500)
    priority: int | None = Field(default=None, ge=1, le=5)
    event_date: datetime | None = None


class UslItemUpdate(BaseModel):
    raw_intent: str | None = Field(default=None, min_length=1, max_length=500)
    status: UslItemStatus | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    event_date: datetime | None = None


class CatalogMatchResponse(BaseModel):
    match_id: UUID
    sku_id: str
    product_name: str | None = None
    category: str | None = None
    price: float | None = None
    image_url: str | None = None
    match_confidence: float
    availability_status: str
    pincode: str
    rank: int
    matched_at: datetime

    model_config = {"from_attributes": True}


class UslItemMetadataResponse(BaseModel):
    attributes: dict | None = None
    intent_confidence: float | None = None
    tags: list | None = None
    shortlist_size: int | None = None
    processing_latency_ms: int | None = None
    last_processed_at: datetime | None = None
    last_error: str | None = None

    model_config = {"from_attributes": True}


class UslItemResponse(BaseModel):
    item_id: UUID
    raw_intent: str
    normalized_name: str | None = None
    category: str | None = None
    status: UslItemStatus
    match_status: MatchStatus
    priority: int | None
    event_date: datetime | None = None
    created_at: datetime
    updated_at: datetime
    purchased_at: datetime | None
    catalog_matches: list[CatalogMatchResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class UslItemDetailResponse(UslItemResponse):
    metadata: UslItemMetadataResponse | None = None


class UslItemListResponse(BaseModel):
    items: list[UslItemResponse]
    total: int
