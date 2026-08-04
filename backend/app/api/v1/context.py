import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.schemas.context import CheckoutContextResponse, UpcomingEvent, WeatherContext
from app.services.checkout_dataset import CheckoutDatasetService
from app.services.context_service import ContextService

router = APIRouter(prefix="/context", tags=["context"])


@router.get("/checkout", response_model=CheckoutContextResponse)
def get_checkout_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    bundle = CheckoutDatasetService(db, settings).load(user.user_id)
    context = ContextService(settings).get_checkout_context(
        user_id=user.user_id,
        pincode=bundle.pincode,
        usl_rows=bundle.usl_rows,
        cart_categories=bundle.cart_categories,
    )

    return CheckoutContextResponse(
        season=context.season,
        season_label=context.season_label,
        weather=WeatherContext(**context.weather),
        cart_categories=context.cart_categories,
        upcoming_events=[
            UpcomingEvent(
                item_id=uuid.UUID(event["item_id"]),
                event_date=event["event_date"],
                days_until=event["days_until"],
                label=event["label"],
            )
            for event in context.upcoming_events
        ],
        festival=context.festival,
    )
