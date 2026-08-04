import pytest

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
