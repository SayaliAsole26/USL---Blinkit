import time

import redis

from app.config import Settings, get_settings

_REDIS_SOCKET_CONNECT_TIMEOUT = 2
_REDIS_SOCKET_TIMEOUT = 2
_availability_cache: tuple[float, bool] | None = None
_AVAILABILITY_CACHE_TTL_SECONDS = 60.0


def get_redis_client(settings: Settings | None = None) -> redis.Redis:
    settings = settings or get_settings()
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=_REDIS_SOCKET_CONNECT_TIMEOUT,
        socket_timeout=_REDIS_SOCKET_TIMEOUT,
    )


def check_redis_connection(settings: Settings | None = None) -> bool:
    try:
        return get_redis_client(settings).ping()
    except Exception:
        return False


def is_redis_available(settings: Settings | None = None, *, force_refresh: bool = False) -> bool:
    """Cached Redis health check — avoids blocking checkout on dead Redis."""
    global _availability_cache
    settings = settings or get_settings()
    if not settings.redis_url.strip():
        return False

    now = time.monotonic()
    if (
        not force_refresh
        and _availability_cache is not None
        and now - _availability_cache[0] < _AVAILABILITY_CACHE_TTL_SECONDS
    ):
        return _availability_cache[1]

    ok = check_redis_connection(settings)
    _availability_cache = (now, ok)
    return ok


def reset_redis_availability_cache() -> None:
    global _availability_cache
    _availability_cache = None
