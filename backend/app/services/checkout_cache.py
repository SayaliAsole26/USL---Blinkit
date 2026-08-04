"""Checkout recommendation caching (Phase 6)."""

from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from app.config import Settings
from app.services.redis_client import get_redis_client, is_redis_available


def checkout_cache_key(
    user_id: uuid.UUID,
    pincode: str,
    cart_sku_ids: list[str] | None,
) -> str:
    cart_part = ",".join(sorted(cart_sku_ids or []))
    digest = hashlib.sha256(cart_part.encode()).hexdigest()[:16]
    return f"checkout:recs:{user_id}:{pincode}:{digest}"


def read_checkout_cache(settings: Settings, key: str) -> dict[str, Any] | None:
    if settings.checkout_cache_ttl_seconds <= 0 or not is_redis_available(settings):
        return None
    try:
        client = get_redis_client(settings)
        raw = client.get(key)
        if raw:
            return json.loads(raw)
    except Exception:
        pass
    return None


def write_checkout_cache(settings: Settings, key: str, payload: dict[str, Any]) -> None:
    if settings.checkout_cache_ttl_seconds <= 0 or not is_redis_available(settings):
        return
    try:
        client = get_redis_client(settings)
        client.setex(key, settings.checkout_cache_ttl_seconds, json.dumps(payload))
    except Exception:
        pass
