import json
from pathlib import Path
from uuid import UUID

import pytest

from app.config import Settings, get_settings
from app.db.models import CatalogMatch, CatalogProduct, ProductAvailability, User, UserLocation, UslItem
from app.integrations.mock_blinkit import get_cart_adapter
from app.pipeline.path_a import PathAProcessor
from app.pipeline.path_b import PathBProcessor
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
def phase3_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        match_confidence_threshold=0.35,
        dismiss_cooldown_days=7,
        max_checkout_recommendations=5,
        max_checkout_shortlist=80,
        groq_api_key="",
    )


def test_path_b_returns_explainable_recommendations(db_session, phase3_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    process_usl_item(db_session, phase3_settings, "Face Wash")

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    result = PathBProcessor(db_session, phase3_settings).process(TEST_USER_ID, "chk_test")

    assert result["shortlist_size"] <= 80
    assert len(result["recommendations"]) <= 5
    for rec in result["recommendations"]:
        assert rec["reason_text"]
        assert rec["reason_type"] in {"memory_reminder", "cross_category_discovery", "shopping_completion"}
        assert rec["sku_id"] != "sku_milk_001"


def test_path_b_excludes_cart_skus(db_session, phase3_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase3_settings, "Face Wash")
    top_match = db_session.scalars(
        __import__("sqlalchemy").select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)
    ).first()
    assert top_match

    get_cart_adapter()._carts[str(TEST_USER_ID)] = []
    get_cart_adapter().add_item(str(TEST_USER_ID), top_match.sku_id)
    result = PathBProcessor(db_session, phase3_settings).process(TEST_USER_ID, "chk_cart")
    skus = {r["sku_id"] for r in result["recommendations"]}
    assert top_match.sku_id not in skus


def test_checkout_api(client, db_session, phase3_settings, monkeypatch):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    process_usl_item(db_session, phase3_settings, "Dog Food")

    get_settings.cache_clear()
    monkeypatch.setenv("USL_CHECKOUT_RECOMMENDATIONS", "true")
    get_settings.cache_clear()

    response = client.get("/v1/recommendations/checkout?checkout_session_id=chk_api", headers=auth_headers())
    assert response.status_code == 200
    data = response.json()
    assert data["checkout_session_id"] == "chk_api"
    if data["recommendations"]:
        assert data["recommendations"][0]["reason_text"]
    get_settings.cache_clear()


def test_recommendation_action_dismiss(client, db_session, phase3_settings, monkeypatch):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase3_settings, "Moisturizer")

    get_settings.cache_clear()
    monkeypatch.setenv("USL_CHECKOUT_RECOMMENDATIONS", "true")
    get_settings.cache_clear()

    checkout = client.get("/v1/recommendations/checkout?checkout_session_id=chk_dismiss", headers=auth_headers())
    recs = checkout.json()["recommendations"]
    if not recs:
        pytest.skip("No recommendations generated")

    rec_id = recs[0]["recommendation_id"]
    action = client.post(
        f"/v1/recommendations/{rec_id}/actions",
        json={"action": "dismissed", "checkout_session_id": "chk_dismiss"},
        headers=auth_headers(),
    )
    assert action.status_code == 200

    db_session.refresh(item)
    assert item.status == "dismissed"
    get_settings.cache_clear()


def test_order_completed_marks_purchased(db_session, phase3_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase3_settings, "Face Wash")
    match = db_session.scalars(
        __import__("sqlalchemy").select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)
    ).first()

    from app.services.recommendation_service import RecommendationService

    count = RecommendationService(db_session, phase3_settings).handle_order_completed(
        TEST_USER_ID,
        [match.sku_id],
        "ord_123",
    )
    assert count == 1
    db_session.refresh(item)
    assert item.status == "purchased"
