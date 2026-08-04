from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.schemas.location import LocationCreate, LocationResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["location"])


@router.get("/location", response_model=LocationResponse)
def get_location(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    location = UserService(db).get_location(user.user_id)
    return location


@router.post("/location", response_model=LocationResponse, status_code=201)
def set_location(
    payload: LocationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    location = UserService(db).set_location(user.user_id, payload)
    return location
