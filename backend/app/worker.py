from __future__ import annotations

import json
import logging
import uuid

from celery import Celery

from app.config import get_settings
from app.db.session import SessionLocal
from app.pipeline.path_a import PathAProcessor
from app.services.redis_client import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()

celery_app = Celery("usl_worker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    task_default_queue="usl-intent",
    task_routes={"usl.process_intent": {"queue": "usl-intent"}},
)

DLQ_KEY = "usl:intent:dlq"


def push_to_dlq(item_id: str, user_id: str, trigger: str, error: str) -> None:
    try:
        client = get_redis_client(settings)
        client.lpush(
            DLQ_KEY,
            json.dumps(
                {
                    "item_id": item_id,
                    "user_id": user_id,
                    "trigger": trigger,
                    "error": error,
                }
            ),
        )
    except Exception as exc:
        logger.error("Failed to push DLQ entry: %s", exc)


@celery_app.task(name="usl.process_intent", bind=True, max_retries=3, default_retry_delay=5)
def process_intent_task(self, item_id: str, user_id: str, trigger: str = "created") -> dict:
    db = SessionLocal()
    try:
        processor = PathAProcessor(db, settings)
        return processor.process(uuid.UUID(item_id), uuid.UUID(user_id), trigger=trigger)
    except Exception as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            push_to_dlq(item_id, user_id, trigger, str(exc))
            raise
    finally:
        db.close()
