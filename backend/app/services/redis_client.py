import redis

from app.config import Settings, get_settings


def get_redis_client(settings: Settings | None = None) -> redis.Redis:
    settings = settings or get_settings()
    return redis.from_url(settings.redis_url, decode_responses=True)


def check_redis_connection(settings: Settings | None = None) -> bool:
    try:
        client = get_redis_client(settings)
        return client.ping()
    except Exception:
        return False
