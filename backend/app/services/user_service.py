import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User, UserLocation
from app.schemas.location import LocationCreate


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, user_id: uuid.UUID) -> User:
        user = self.db.get(User, user_id)
        if user:
            return user

        user = User(user_id=user_id, onboarding_completed=False)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_location(self, user_id: uuid.UUID) -> UserLocation:
        location = self.db.get(UserLocation, user_id)
        if not location:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not set")
        return location

    def set_location(self, user_id: uuid.UUID, payload: LocationCreate) -> UserLocation:
        user = self.get_or_create_user(user_id)
        location = self.db.get(UserLocation, user_id)
        old_pincode = location.pincode if location else None

        if location:
            location.city = payload.city.strip()
            location.state = payload.state.strip()
            location.pincode = payload.pincode.strip()
        else:
            location = UserLocation(
                user_id=user_id,
                city=payload.city.strip(),
                state=payload.state.strip(),
                pincode=payload.pincode.strip(),
            )
            self.db.add(location)

        user.onboarding_completed = True
        self.db.commit()
        self.db.refresh(location)

        if old_pincode and old_pincode != location.pincode:
            from app.services.intent_queue import enqueue_rematch_for_user

            enqueue_rematch_for_user(user_id)

        return location
