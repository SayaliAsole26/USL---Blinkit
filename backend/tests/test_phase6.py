import hashlib
import json
import uuid
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.services.checkout_cache import checkout_cache_key, read_checkout_cache, write_checkout_cache
from app.services.recommendation_service import RecommendationService
from tests.conftest import TEST_USER_ID, auth_headers


@pytest.fixture
def phase6_settings():
    return Settings(
        embeddings_enabled=False,
        meili_url="",
        usl_checkout_recommendations=True,
        checkout_cache_ttl_seconds=60,
        rollout_percentage=100,
        groq_api_key="",
    )


def test_checkout_cache_key_is_stable():
    user_id = TEST_USER_ID
    key_a = checkout_cache_key(user_id, "560001", ["sku_a", "sku_b"])
    key_b = checkout_cache_key(user_id, "560001", ["sku_b", "sku_a"])
    assert key_a == key_b
    assert "560001" in key_a


def test_checkout_cache_round_trip(monkeypatch, phase6_settings):
    store: dict[str, str] = {}
    mock_client = MagicMock()
    mock_client.get.side_effect = lambda k: store.get(k)
    mock_client.setex.side_effect = lambda k, ttl, val: store.__setitem__(k, val)
    monkeypatch.setattr("app.services.checkout_cache.get_redis_client", lambda _s: mock_client)
    monkeypatch.setattr("app.services.checkout_cache.is_redis_available", lambda _s=None: True)

    key = "checkout:recs:test"
    payload = {"recommendations": [], "shortlist_size": 0, "latency_ms": 12}
    write_checkout_cache(phase6_settings, key, payload)
    cached = read_checkout_cache(phase6_settings, key)
    assert cached == payload


def test_checkout_cache_disabled_when_ttl_zero(monkeypatch, phase6_settings):
    phase6_settings.checkout_cache_ttl_seconds = 0
    mock_client = MagicMock()
    monkeypatch.setattr("app.services.checkout_cache.get_redis_client", lambda _s: mock_client)

    write_checkout_cache(phase6_settings, "k", {"x": 1})
    assert read_checkout_cache(phase6_settings, "k") is None
    mock_client.setex.assert_not_called()


def test_rollout_percentage_zero_returns_empty(db_session, phase6_settings):
    phase6_settings.rollout_percentage = 0
    result = RecommendationService(db_session, phase6_settings).get_checkout_recommendations(
        TEST_USER_ID, "chk_rollout"
    )
    assert result["recommendations"] == []


def test_rollout_percentage_deterministic(db_session, phase6_settings):
    phase6_settings.rollout_percentage = 50
    service = RecommendationService(db_session, phase6_settings)
    in_rollout = service._is_in_rollout(TEST_USER_ID)
    assert service._is_in_rollout(TEST_USER_ID) == in_rollout


def test_feature_flags_expose_rollout(client, phase6_settings, monkeypatch):
    monkeypatch.setattr("app.api.v1.flags.get_settings", lambda: phase6_settings)
    response = client.get("/v1/flags")
    assert response.status_code == 200
    data = response.json()
    assert data["usl_enabled"] is True
    assert "rollout_percentage" in data
    assert "experiments_enabled" in data


def test_explanation_cache_key_is_deterministic():
    from app.pipeline.llm import GroqLLMService

    settings = Settings(groq_api_key="", explanation_cache_ttl_seconds=3600)
    llm = GroqLLMService(settings)
    key_a = llm._explanation_cache_key("weather_context", {"forecast": "rain"})
    key_b = llm._explanation_cache_key("weather_context", {"forecast": "rain"})
    assert key_a == key_b
    assert key_a.startswith("llm:explain:")
