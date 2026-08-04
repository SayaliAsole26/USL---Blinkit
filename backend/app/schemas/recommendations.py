from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class RecommendationAction(StrEnum):
    ADDED_TO_CART = "added_to_cart"
    SAVED_FOR_LATER = "saved_for_later"
    DISMISSED = "dismissed"


class CheckoutRecommendation(BaseModel):
    recommendation_id: str
    usl_item_id: UUID
    sku_id: str
    product_name: str
    price: float
    image_url: str | None = None
    reason_type: str
    reason_text: str
    confidence: float


class CheckoutRecommendationsResponse(BaseModel):
    checkout_session_id: str
    recommendations: list[CheckoutRecommendation]
    shortlist_size: int
    latency_ms: int


class RecommendationActionRequest(BaseModel):
    action: RecommendationAction
    checkout_session_id: str = Field(..., min_length=1, max_length=128)


class RecommendationActionResponse(BaseModel):
    recommendation_id: str
    action: RecommendationAction
    usl_item_id: UUID | None = None
    sku_id: str
    message: str


class OrderCompletedRequest(BaseModel):
    order_id: str = Field(..., min_length=1)
    sku_ids: list[str] = Field(default_factory=list)
    checkout_session_id: str | None = None


class OrderCompletedResponse(BaseModel):
    order_id: str
    usl_items_marked_purchased: int
    purchase_history_recorded: int = 0


class OrderHistoryEntry(BaseModel):
    sku_id: str = Field(..., min_length=1)
    purchased_at: datetime | None = None
    quantity: int = Field(default=1, ge=1)
    order_id: str | None = None


class OrderHistoryImportRequest(BaseModel):
    purchases: list[OrderHistoryEntry] = Field(default_factory=list)


class OrderHistoryImportResponse(BaseModel):
    recorded: int
