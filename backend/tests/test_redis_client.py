import time

import pytest

from app.config import Settings
from app.pipeline.llm import GroqLLMService
from app.services.redis_client import is_redis_available, reset_redis_availability_cache


def test_is_redis_available_caches_result(monkeypatch):
    reset_redis_availability_cache()
    calls = {"count": 0}

    def fake_check(_settings=None):
        calls["count"] += 1
        return False

    monkeypatch.setattr("app.services.redis_client.check_redis_connection", fake_check)

    from app.config import Settings

    settings = Settings(redis_url="redis://localhost:6379")
    assert is_redis_available(settings) is False
    assert is_redis_available(settings) is False
    assert calls["count"] == 1


def test_generate_reason_text_skips_groq_without_redis(monkeypatch):
    monkeypatch.setattr("app.pipeline.llm.is_redis_available", lambda _s=None: False)
    settings = Settings(groq_api_key="test-key")
    text = GroqLLMService(settings).generate_reason_text(
        "memory_reminder",
        {"product_name": "Face Wash"},
    )
    assert "Face Wash" in text
    assert "Universal Shopping List" in text
