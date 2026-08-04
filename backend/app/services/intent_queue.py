"""Enqueue Path A intent processing jobs."""

from __future__ import annotations

import logging
import uuid

from app.config import Settings, get_settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def _process_intent_sync(item_id: uuid.UUID, user_id: uuid.UUID, trigger: str, settings: Settings) -> None:
    from app.pipeline.path_a import PathAProcessor

    db = SessionLocal()
    try:
        PathAProcessor(db, settings).process(item_id, user_id, trigger=trigger)
    finally:
        db.close()


def enqueue_intent_processing(
    item_id: uuid.UUID,
    user_id: uuid.UUID,
    trigger: str = "created",
    settings: Settings | None = None,
) -> None:
    settings = settings or get_settings()
    if settings.intent_worker_sync:
        _process_intent_sync(item_id, user_id, trigger, settings)
        return

    try:
        from app.worker import process_intent_task

        process_intent_task.delay(str(item_id), str(user_id), trigger)
    except Exception as exc:
        # Redis/Celery unavailable — fall back inline so API stays responsive.
        logger.warning("Celery enqueue failed (%s); running Path A synchronously", exc)
        _process_intent_sync(item_id, user_id, trigger, settings)


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
