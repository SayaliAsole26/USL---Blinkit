import json
from pathlib import Path

import pytest

from app.config import Settings
from app.db.models import CatalogProduct, ProductAvailability, User, UserLocation, UslItem
from app.pipeline.llm import GroqLLMService
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


@pytest.fixture
def phase2_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        match_confidence_threshold=0.35,
        max_catalog_shortlist=80,
        max_catalog_matches=3,
        groq_api_key="",
    )


def test_path_a_llm_shortlist_invariant(phase2_settings):
    candidates = [{"sku_id": f"sku_{i}", "product_name": f"Product {i}", "category": "Test", "score": 0.5} for i in range(120)]
    llm = GroqLLMService(phase2_settings)
    selected = llm.select_matches_from_shortlist("Face Wash", {"normalized_name": "Face Wash"}, candidates, max_matches=3)
    assert len(selected) <= 3
    assert phase2_settings.max_catalog_shortlist == 80


def test_common_intents_match_catalog(db_session, phase2_settings):
    seed_catalog(db_session)
    user = User(user_id=TEST_USER_ID, onboarding_completed=True)
    db_session.add(user)
    db_session.add(UserLocation(user_id=TEST_USER_ID, city="Bangalore", state="KA", pincode="560001"))
    item = UslItem(user_id=TEST_USER_ID, raw_intent="Face Wash", status="pending", match_status="queued")
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    processor = PathAProcessor(db_session, phase2_settings)
    result = processor.process(item.item_id, TEST_USER_ID, trigger="test")
    assert result["ok"] is True
    assert result["match_status"] == "matched"
    assert result["matches"] >= 1
    assert result["llm_candidate_size"] <= 80


def test_common_intents_airpods_and_dog_food(db_session, phase2_settings):
    seed_catalog(db_session)
    user = User(user_id=TEST_USER_ID, onboarding_completed=True)
    db_session.add(user)
    db_session.add(UserLocation(user_id=TEST_USER_ID, city="Bangalore", state="KA", pincode="560001"))
    db_session.commit()

    processor = PathAProcessor(db_session, phase2_settings)
    for intent in ["AirPods", "Dog Food"]:
        item = UslItem(user_id=TEST_USER_ID, raw_intent=intent, status="pending", match_status="queued")
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        result = processor.process(item.item_id, TEST_USER_ID, trigger="test")
        assert result["match_status"] == "matched", intent


def test_admin_debug_endpoints(client, monkeypatch):
    from app.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("ADMIN_DEBUG_ENABLED", "true")
    get_settings.cache_clear()

    metrics = client.get("/v1/admin/pipeline/metrics")
    assert metrics.status_code == 200
    assert "path_a" in metrics.json()
    assert "path_b" in metrics.json()

    matches = client.get("/v1/admin/matches")
    assert matches.status_code == 200
    get_settings.cache_clear()


def test_item_detail_endpoint(client, db_session, monkeypatch):
    seed_catalog(db_session)
    client.post(
        "/v1/users/location",
        json={"city": "Bangalore", "state": "Karnataka", "pincode": "560001"},
        headers=auth_headers(),
    )
    created = client.post("/v1/usl/items", json={"raw_intent": "Moisturizer"}, headers=auth_headers()).json()
    detail = client.get(f"/v1/usl/items/{created['item_id']}", headers=auth_headers())
    assert detail.status_code == 200
    assert detail.json()["raw_intent"] == "Moisturizer"
