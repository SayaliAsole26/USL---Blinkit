import uuid
from unittest.mock import patch

import pytest

from app.config import Settings
from app.services.intent_queue import _dispatch_intent_processing

TEST_ITEM_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def async_settings():
    return Settings(
        intent_worker_sync=False,
        embeddings_enabled=False,
        meili_url="",
        groq_api_key="",
    )


def test_skips_celery_when_redis_unavailable(async_settings):
    with patch("app.services.intent_queue.is_redis_available", return_value=False):
        with patch("app.services.intent_queue._process_intent_sync") as sync_mock:
            _dispatch_intent_processing(TEST_ITEM_ID, TEST_USER_ID, "created", async_settings)
            sync_mock.assert_called_once_with(TEST_ITEM_ID, TEST_USER_ID, "created", async_settings)


def test_falls_back_to_sync_when_celery_unavailable(async_settings):
    with patch("app.services.intent_queue.is_redis_available", return_value=True):
        with patch("app.worker.process_intent_task.delay", side_effect=ConnectionError("redis down")):
            with patch("app.services.intent_queue._process_intent_sync") as sync_mock:
                _dispatch_intent_processing(TEST_ITEM_ID, TEST_USER_ID, "created", async_settings)
                sync_mock.assert_called_once_with(TEST_ITEM_ID, TEST_USER_ID, "created", async_settings)
