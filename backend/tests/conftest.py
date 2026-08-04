import uuid

import pytest
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.db.models import Base
from app.db.session import get_db
from app.integrations.mock_blinkit import get_cart_adapter
from app.main import app

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@pytest.fixture(autouse=True)
def disable_async_intent_by_default(monkeypatch):
    noop = lambda *args, **kwargs: None
    monkeypatch.setattr("app.services.usl_service.enqueue_intent_processing", noop)
    monkeypatch.setattr("app.services.intent_queue.enqueue_intent_processing", noop)
    monkeypatch.setattr("app.services.intent_queue.enqueue_rematch_for_user", lambda *args, **kwargs: 0)
    get_cart_adapter()._carts.clear()


@pytest.fixture
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    tables = [
        Base.metadata.tables["users"],
        Base.metadata.tables["user_locations"],
        Base.metadata.tables["usl_items"],
        Base.metadata.tables["usl_item_metadata"],
        Base.metadata.tables["catalog_products"],
        Base.metadata.tables["product_availability"],
        Base.metadata.tables["catalog_matches"],
        Base.metadata.tables["recommendation_events"],
    ]
    Base.metadata.create_all(bind=engine, tables=tables)
    yield engine
    Base.metadata.drop_all(bind=engine, tables=tables)


@pytest.fixture
def db_session(db_engine):
    session = sessionmaker(bind=db_engine)()
    yield session
    session.close()


@pytest.fixture
def client(db_engine):
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def auth_headers(user_id: uuid.UUID = TEST_USER_ID) -> dict[str, str]:
    settings = get_settings()
    token = jwt.encode({"sub": str(user_id)}, settings.jwt_secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}
