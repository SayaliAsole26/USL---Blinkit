import json
from pathlib import Path

import pytest

from app.config import Settings
from app.db.models import CatalogMatch, CatalogProduct, ProductAvailability, User, UserLocation, UslItem
from app.pipeline.path_a import PathAProcessor
from app.services.experiment_service import ExperimentService
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


def process_usl_item(db, settings, raw_intent: str) -> UslItem:
    item = UslItem(user_id=TEST_USER_ID, raw_intent=raw_intent, status="pending", match_status="queued")
    db.add(item)
    db.commit()
    db.refresh(item)
    PathAProcessor(db, settings).process(item.item_id, TEST_USER_ID, trigger="test")
    db.refresh(item)
    return item


@pytest.fixture
def phase7_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        experiments_enabled=True,
        groq_api_key="",
    )


def test_experiment_assign_variant_is_deterministic(phase7_settings):
    service = ExperimentService(phase7_settings)
    variant = service.assign_variant(TEST_USER_ID)
    assert variant in ExperimentService.VARIANTS
    assert service.assign_variant(TEST_USER_ID) == variant


def test_experiment_disabled_returns_control(phase7_settings):
    phase7_settings.experiments_enabled = False
    service = ExperimentService(phase7_settings)
    assert service.assign_variant(TEST_USER_ID) == "control"


def test_boost_context_variant_increases_weights(phase7_settings, monkeypatch):
    service = ExperimentService(phase7_settings)
    monkeypatch.setattr(service, "assign_variant", lambda _uid: "boost_context")
    base = service.ranker_config.get_weights()
    boosted = service.get_ranker_weights(TEST_USER_ID)
    assert boosted.weather_context > base.weather_context
    assert boosted.seasonal_context > base.seasonal_context


def test_watch_item_availability_api(client, db_session, phase7_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase7_settings, "Wireless Earbuds")

    response = client.post(f"/v1/usl/items/{item.item_id}/watch", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == str(item.item_id)
    assert data["pincode"] == "560001"
    assert "watch_id" in data


def test_watch_is_idempotent(client, db_session, phase7_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase7_settings, "Dog Food")

    first = client.post(f"/v1/usl/items/{item.item_id}/watch", headers=auth_headers()).json()
    second = client.post(f"/v1/usl/items/{item.item_id}/watch", headers=auth_headers()).json()
    assert first["watch_id"] == second["watch_id"]


def test_availability_notifications_endpoint(client, db_session, phase7_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase7_settings, "AirPods Pro")

    client.post(f"/v1/usl/items/{item.item_id}/watch", headers=auth_headers())
    response = client.get("/v1/usl/availability-notifications", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert isinstance(data["notifications"], list)
