import uuid

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import User
from app.db.session import get_db
from app.services.user_service import UserService


def get_current_user_id(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    """Mock JWT auth — accepts Bearer dev token or valid JWT with sub claim."""
    if not authorization:
        return uuid.UUID("00000000-0000-0000-0000-000000000001")

    if authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        if token == "dev":
            return uuid.UUID("00000000-0000-0000-0000-000000000001")
        try:
            payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
            sub = payload.get("sub")
            if sub:
                return uuid.UUID(str(sub))
        except (JWTError, ValueError) as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> User:
    return UserService(db).get_or_create_user(user_id)
