import uuid

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.schemas.usl import UslItemCreate, UslItemDetailResponse, UslItemListResponse, UslItemResponse, UslItemUpdate
from app.services.usl_service import UslService

router = APIRouter(prefix="/usl", tags=["usl"])


def _require_usl_enabled(settings: Settings = Depends(get_settings)) -> None:
    if not settings.usl_enabled:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="USL is disabled")


@router.get("/items", response_model=UslItemListResponse)
def list_usl_items(
    status_filter: str | None = Query(default=None, alias="status"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_usl_enabled),
):
    items = UslService(db).list_items(user.user_id, status_filter=status_filter)
    return UslItemListResponse(items=items, total=len(items))


@router.post("/items", response_model=UslItemResponse, status_code=201)
def create_usl_item(
    payload: UslItemCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_usl_enabled),
):
    return UslService(db).create_item(user.user_id, payload)


@router.get("/items/{item_id}", response_model=UslItemDetailResponse)
def get_usl_item(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_usl_enabled),
):
    return UslService(db).get_item_detail(user.user_id, item_id)


@router.patch("/items/{item_id}", response_model=UslItemResponse)
def update_usl_item(
    item_id: uuid.UUID,
    payload: UslItemUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_usl_enabled),
):
    return UslService(db).update_item(user.user_id, item_id, payload)


@router.delete("/items/{item_id}", status_code=204)
def delete_usl_item(
    item_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(_require_usl_enabled),
):
    UslService(db).delete_item(user.user_id, item_id)
    return Response(status_code=204)
