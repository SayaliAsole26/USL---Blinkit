import json
from pathlib import Path

import pytest

from app.config import Settings
from app.db.models import CatalogProduct, ProductAvailability, User, UserLocation, UslItem
from app.integrations.mock_blinkit import get_cart_adapter
from app.pipeline.path_a import PathAProcessor
from tests.conftest import TEST_USER_ID, auth_headers

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = json.loads((ROOT / "data" / "catalog-fixtures.json").read_text(encoding="utf-8"))


def seed_catalog(db):
    for item in FIXTURES:
        if not db.get(CatalogProduct, item["sku_id"]):
            db.add(
                CatalogProduct(
                    sku_id=item["sku_id"],
                    product_name=item["product_name"],
                    category=item["category"],
                    price=item["price"],
                    image_url=item.get("image_url"),
                )
            )
        for pincode in item.get("pincodes", []):
            existing = (
                db.query(ProductAvailability)
                .filter(ProductAvailability.sku_id == item["sku_id"], ProductAvailability.pincode == pincode)
                .first()
            )
            if not existing:
                db.add(
                    ProductAvailability(
                        sku_id=item["sku_id"],
                        pincode=pincode,
                        availability_status="available",
                    )
                )
    db.commit()


def seed_user_with_location(db):
    if not db.get(User, TEST_USER_ID):
        db.add(User(user_id=TEST_USER_ID, onboarding_completed=True))
    if not db.get(UserLocation, TEST_USER_ID):
        db.add(UserLocation(user_id=TEST_USER_ID, city="Bangalore", state="KA", pincode="560001"))
    db.commit()


@pytest.fixture
def checkout_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        groq_api_key="test-key",
        max_checkout_recommendations=5,
    )


def test_checkout_api_without_redis_uses_templates(client, db_session, checkout_settings, monkeypatch):
    seed_catalog(db_session)
    seed_user_with_location(db_session)

    item = UslItem(user_id=TEST_USER_ID, raw_intent="Face Wash", status="pending", match_status="queued")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    PathAProcessor(db_session, checkout_settings).process(item.item_id, TEST_USER_ID, trigger="test")

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    monkeypatch.setattr("app.pipeline.llm.is_redis_available", lambda _s=None: False)
    monkeypatch.setattr("app.context.weather_provider.is_redis_available", lambda _s=None: False)
    monkeypatch.setattr("app.services.checkout_cache.is_redis_available", lambda _s=None: False)

    response = client.get("/v1/recommendations/checkout?checkout_session_id=chk_fast", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["checkout_session_id"] == "chk_fast"
    if data["recommendations"]:
        assert data["recommendations"][0]["reason_text"]
