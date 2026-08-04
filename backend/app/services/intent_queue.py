"""Enqueue Path A intent processing jobs."""

from __future__ import annotations

import logging
import threading
import uuid

from app.config import Settings, get_settings
from app.db.session import SessionLocal
from app.services.redis_client import check_redis_connection

logger = logging.getLogger(__name__)


def _process_intent_sync(item_id: uuid.UUID, user_id: uuid.UUID, trigger: str, settings: Settings) -> None:
    from app.pipeline.path_a import PathAProcessor

    db = SessionLocal()
    try:
        PathAProcessor(db, settings).process(item_id, user_id, trigger=trigger)
    finally:
        db.close()


def _dispatch_intent_processing(
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    trigger: str,
    settings: Settings,
) -> None:
    """Run Path A via Celery when Redis is healthy, otherwise inline in this thread."""
    if settings.intent_worker_sync or not check_redis_connection(settings):
        if not settings.intent_worker_sync:
            logger.warning("Redis unavailable; running Path A in background thread")
        _process_intent_sync(item_id, user_id, trigger, settings)
        return

    try:
        from app.worker import process_intent_task

        process_intent_task.delay(str(item_id), str(user_id), trigger)
    except Exception as exc:
        logger.warning("Celery enqueue failed (%s); running Path A in background thread", exc)
        _process_intent_sync(item_id, user_id, trigger, settings)


def enqueue_intent_processing(
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    trigger: str = "created",
    settings: Settings | None = None,
) -> None:
    """Fire-and-forget — never block the HTTP response on Redis/Celery/LLM."""
    settings = settings or get_settings()
    thread = threading.Thread(
        target=_dispatch_intent_processing,
        args=(item_id, user_id, trigger, settings),
        daemon=True,
        name=f"usl-intent-{item_id}",
    )
    thread.start()


def enqueue_rematch_for_user(user_id: uuid.UUID, settings: Settings | None = None) -> int:
    settings = settings or get_settings()
    from sqlalchemy import select

    from app.db.models import UslItem

    db = SessionLocal()
    try:
        items = list(db.scalars(select(UslItem).where(UslItem.user_id == user_id)).all())
    finally:
        db.close()

    for item in items:
        enqueue_intent_processing(item.item_id, user_id, trigger="pincode_changed", settings=settings)
    return len(items)
