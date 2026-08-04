import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.schemas.recommendations import (
    CheckoutRecommendationsResponse,
    OrderCompletedRequest,
    OrderCompletedResponse,
    RecommendationActionRequest,
    RecommendationActionResponse,
)
from app.services.recommendation_service import RecommendationService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def _require_checkout_enabled(settings: Settings = Depends(get_settings)) -> None:
    if not settings.usl_checkout_recommendations:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout recommendations disabled")


@router.get("/checkout", response_model=CheckoutRecommendationsResponse)
def get_checkout_recommendations(
    checkout_session_id: str | None = Query(default=None),
    cart_skus: str | None = Query(default=None, description="Comma-separated SKU IDs already in cart"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_checkout_enabled),
):
    session_id = checkout_session_id or f"chk_{uuid.uuid4().hex[:12]}"
    cart_sku_ids = [s.strip() for s in cart_skus.split(",") if s.strip()] if cart_skus else None
    result = RecommendationService(db, settings).get_checkout_recommendations(
        user.user_id,
        session_id,
        cart_sku_ids=cart_sku_ids,
    )
    return CheckoutRecommendationsResponse(**result)


@router.post("/{recommendation_id}/actions", response_model=RecommendationActionResponse)
def recommendation_action(
    recommendation_id: str,
    payload: RecommendationActionRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_checkout_enabled),
):
    result = RecommendationService(db, settings).handle_action(
        user.user_id,
        recommendation_id,
        payload.action,
        payload.checkout_session_id,
    )
    return RecommendationActionResponse(**result)
