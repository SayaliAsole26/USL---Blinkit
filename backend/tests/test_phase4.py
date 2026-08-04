import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

import pytest

from app.config import Settings
from app.context.season_provider import SeasonProvider
from app.context.weather_provider import WeatherProvider
from app.db.models import CatalogMatch, CatalogProduct, ProductAvailability, User, UserLocation, UslItem
from app.integrations.mock_blinkit import get_cart_adapter
from app.pipeline.path_a import PathAProcessor
from app.pipeline.path_b import PathBProcessor
from app.services.context_service import ContextService
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


def process_usl_item(db, settings, raw_intent: str, event_date: datetime | None = None) -> UslItem:
    item = UslItem(
        user_id=TEST_USER_ID,
        raw_intent=raw_intent,
        status="pending",
        match_status="queued",
        event_date=event_date,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    PathAProcessor(db, settings).process(item.item_id, TEST_USER_ID, trigger="test")
    db.refresh(item)
    return item


@pytest.fixture
def phase4_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        match_confidence_threshold=0.35,
        dismiss_cooldown_days=7,
        max_checkout_recommendations=5,
        max_checkout_shortlist=80,
        event_window_days=14,
        context_cache_ttl_seconds=0,
        weather_cache_ttl_seconds=0,
        groq_api_key="",
    )


def test_season_provider_summer_match():
    provider = SeasonProvider()
    summer = datetime(2026, 5, 15, tzinfo=timezone.utc)
    current = provider.get_current_season(summer)
    assert current["id"] == "summer"
    assert provider.is_seasonal_match("summer", raw_intent="Sunscreen SPF 50", category="Personal Care")


def test_weather_provider_detects_rain_relevant_items():
    provider = WeatherProvider(Settings())
    assert provider.is_weather_relevant_item(raw_intent="Compact umbrella")
    assert not provider.is_weather_relevant_item(raw_intent="Face Wash")


def test_context_checkout_endpoint(client, db_session, phase4_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    process_usl_item(db_session, phase4_settings, "Umbrella")

    response = client.get("/v1/context/checkout", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert "season" in data
    assert "weather" in data
    assert "forecast" in data["weather"]
    assert isinstance(data["cart_categories"], list)


def test_r4_weather_context_for_umbrella(db_session, phase4_settings, monkeypatch):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    process_usl_item(db_session, phase4_settings, "Rain umbrella")

    rain_forecast = {"forecast": "rain", "severity": "moderate", "days_ahead": 3, "max_precipitation_mm": 5.0}
    monkeypatch.setattr(WeatherProvider, "get_forecast", lambda self, pincode, when=None: rain_forecast)

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    result = PathBProcessor(db_session, phase4_settings).process(TEST_USER_ID, "chk_weather")

    weather_recs = [r for r in result["recommendations"] if r["reason_type"] == "weather_context"]
    assert weather_recs, "Expected weather_context recommendation for umbrella when rain is forecast"
    assert weather_recs[0]["reason_text"]


def test_r3_seasonal_context_for_sunscreen(db_session, phase4_settings, monkeypatch):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    process_usl_item(db_session, phase4_settings, "Sunscreen SPF 50")

    monkeypatch.setattr(
        SeasonProvider,
        "get_current_season",
        lambda self, when=None: {"id": "summer", "name": "Summer", "month": 5},
    )

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    result = PathBProcessor(db_session, phase4_settings).process(TEST_USER_ID, "chk_season")

    seasonal_recs = [r for r in result["recommendations"] if r["reason_type"] == "seasonal_context"]
    assert seasonal_recs, "Expected seasonal_context recommendation for sunscreen in summer"
    assert "Summer" in seasonal_recs[0]["reason_text"] or seasonal_recs[0]["reason_text"]


def test_r5_event_based_within_window(db_session, phase4_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    event_date = datetime.now(timezone.utc) + timedelta(days=7)
    process_usl_item(db_session, phase4_settings, "Birthday gift hamper", event_date=event_date)

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    result = PathBProcessor(db_session, phase4_settings).process(TEST_USER_ID, "chk_event")

    event_recs = [r for r in result["recommendations"] if r["reason_type"] == "event_based"]
    assert event_recs, "Expected event_based recommendation for gift with upcoming event_date"
    assert event_recs[0]["reason_text"]


def test_usl_create_with_event_date(client, db_session, phase4_settings):
    seed_user_with_location(db_session)

    response = client.post(
        "/v1/usl/items",
        json={"raw_intent": "Anniversary gift", "event_date": "2026-08-20T00:00:00Z"},
        headers=auth_headers(),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["event_date"] is not None


def test_context_service_collects_upcoming_events(db_session, phase4_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    event_date = datetime.now(timezone.utc) + timedelta(days=5)
    item = process_usl_item(db_session, phase4_settings, "Friend birthday gift", event_date=event_date)

    from app.services.checkout_dataset import CheckoutDatasetService

    bundle = CheckoutDatasetService(db_session, phase4_settings).load(TEST_USER_ID)
    context = ContextService(phase4_settings).get_checkout_context(
        user_id=TEST_USER_ID,
        pincode=bundle.pincode,
        usl_rows=bundle.usl_rows,
        cart_categories=bundle.cart_categories,
    )

    assert context.upcoming_events
    assert context.upcoming_events[0]["item_id"] == str(item.item_id)
    assert 0 <= context.upcoming_events[0]["days_until"] <= 5
