import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.config import Settings
from app.db.models import CatalogMatch, CatalogProduct, ProductAvailability, PurchaseHistory, RecommendationEvent, User, UserLocation, UslItem
from app.integrations.mock_blinkit import get_cart_adapter
from app.pipeline.path_a import PathAProcessor
from app.pipeline.path_b import PathBProcessor
from app.services.purchase_history_service import PurchaseHistoryService
from app.services.ranker_config import RankerConfigService
from app.services.recommendation_service import RecommendationService
from app.services.replenishment_service import ReplenishmentService
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
def phase5_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        match_confidence_threshold=0.35,
        dismiss_cooldown_days=7,
        frequency_cap_days=7,
        max_checkout_recommendations=5,
        max_checkout_shortlist=80,
        replenishment_due_threshold=1.0,
        groq_api_key="",
    )


def test_order_completed_records_purchase_history(db_session, phase5_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase5_settings, "Face Wash")
    match = db_session.scalars(
        __import__("sqlalchemy").select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)
    ).first()

    purchased, history_count = RecommendationService(db_session, phase5_settings).handle_order_completed(
        TEST_USER_ID, [match.sku_id], "ord_phase5"
    )
    assert purchased == 1
    assert history_count == 1

    rows = db_session.scalars(
        __import__("sqlalchemy").select(PurchaseHistory).where(PurchaseHistory.user_id == TEST_USER_ID)
    ).all()
    assert len(rows) == 1
    assert rows[0].sku_id == match.sku_id


def test_r2_replenishment_for_face_wash_after_30_days(db_session, phase5_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase5_settings, "Face Wash")
    match = db_session.scalars(
        __import__("sqlalchemy").select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)
    ).first()

    purchased_at = datetime.now(timezone.utc) - timedelta(days=35)
    item.status = "purchased"
    item.purchased_at = purchased_at
    PurchaseHistoryService(db_session).record_order_purchases(
        TEST_USER_ID,
        [match.sku_id],
        "ord_old",
        purchased_at=purchased_at,
    )
    db_session.commit()

    get_cart_adapter().add_item(str(TEST_USER_ID), "sku_milk_001")
    result = PathBProcessor(db_session, phase5_settings).process(TEST_USER_ID, "chk_replenish")

    replenishment = [r for r in result["recommendations"] if r["reason_type"] == "replenishment_reminder"]
    assert replenishment, "Expected replenishment reminder for face wash purchased 35 days ago"
    assert "35" in replenishment[0]["reason_text"] or "restock" in replenishment[0]["reason_text"].lower()


def test_replenishment_service_default_cycle(db_session, phase5_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)

    service = ReplenishmentService(PurchaseHistoryService(db_session), phase5_settings)
    when = datetime.now(timezone.utc)
    purchased_at = when - timedelta(days=35)

    PurchaseHistoryService(db_session).record_order_purchases(
        TEST_USER_ID,
        ["sku_face_wash_001"],
        "ord_cycle",
        purchased_at=purchased_at,
    )
    db_session.commit()

    result = service.compute_due_score(
        TEST_USER_ID,
        "sku_face_wash_001",
        "Personal Care",
        purchased_at=purchased_at,
        now=when,
    )
    assert result.cycle_days == 30
    assert result.due_score >= 1.0


def test_frequency_cap_excludes_dismissed_sku(db_session, phase5_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)
    item = process_usl_item(db_session, phase5_settings, "Moisturizer")
    match = db_session.scalars(
        __import__("sqlalchemy").select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)
    ).first()

    db_session.add(
        RecommendationEvent(
            user_id=TEST_USER_ID,
            checkout_session_id="chk_cap",
            recommendation_id="rec_cap",
            item_id=item.item_id,
            sku_id=match.sku_id,
            reason_type="memory_reminder",
            reason_text="test",
            action="dismissed",
            created_at=datetime.now(timezone.utc),
        )
    )
    db_session.commit()

    result = PathBProcessor(db_session, phase5_settings).process(TEST_USER_ID, "chk_cap2")
    skus = {r["sku_id"] for r in result["recommendations"]}
    assert match.sku_id not in skus


def test_ranker_weights_loaded_from_config(phase5_settings):
    weights = RankerConfigService(phase5_settings).get_weights()
    assert weights.replenishment_reminder > weights.memory_reminder
    assert weights.acceptance_boost > 0


def test_import_order_history_api(client, db_session, phase5_settings):
    seed_catalog(db_session)
    seed_user_with_location(db_session)

    purchased_at = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    response = client.post(
        "/v1/integrations/orders/history/import",
        json={
            "purchases": [
                {"sku_id": "sku_face_wash_001", "purchased_at": purchased_at, "order_id": "blinkit_hist_1"}
            ]
        },
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json()["recorded"] == 1


def test_admin_ranker_weights_endpoint(client, phase5_settings):
    response = client.get("/v1/admin/ranker/weights")
    assert response.status_code == 200
    data = response.json()
    assert data["replenishment_reminder"] == 1.2
    assert "acceptance_boost" in data
