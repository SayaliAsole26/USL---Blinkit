"""Replenishment scoring — inter-purchase intervals and default category cycles."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.services.purchase_history_service import PurchaseHistoryService


@dataclass
class ReplenishmentResult:
    due_score: float
    days_since_purchase: int
    cycle_days: int
    last_purchased_at: datetime | None


def _cycles_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "replenishment-cycles.json"


@lru_cache
def _load_cycles() -> dict[str, Any]:
    return json.loads(_cycles_path().read_text(encoding="utf-8"))


class ReplenishmentService:
    GIFT_CATEGORIES = {"Gifting"}

    def __init__(self, purchase_history: PurchaseHistoryService, settings: Settings | None = None):
        self.history = purchase_history
        self.settings = settings or get_settings()
        self._cycles = _load_cycles()

    def compute_due_score(
        self,
        user_id: uuid.UUID,
        sku_id: str,
        category: str,
        *,
        purchased_at: datetime | None = None,
        now: datetime | None = None,
    ) -> ReplenishmentResult:
        if category in self.GIFT_CATEGORIES:
            return ReplenishmentResult(0.0, 0, 0, None)

        current = now or datetime.now(timezone.utc)
        last_at = purchased_at

        if not last_at:
            last_row = self.history.get_last_purchase(user_id, sku_id)
            last_at = last_row.purchased_at if last_row else None

        if not last_at:
            return ReplenishmentResult(0.0, 0, 0, None)

        if last_at.tzinfo is None:
            last_at = last_at.replace(tzinfo=timezone.utc)

        days_since = (current.date() - last_at.date()).days
        cycle_days = self._resolve_cycle_days(user_id, sku_id, category)

        if days_since < cycle_days:
            return ReplenishmentResult(0.0, days_since, cycle_days, last_at)

        due_score = min(1.0, days_since / cycle_days)
        return ReplenishmentResult(due_score, days_since, cycle_days, last_at)

    def is_replenishment_due(
        self,
        user_id: uuid.UUID,
        sku_id: str,
        category: str,
        *,
        purchased_at: datetime | None = None,
        now: datetime | None = None,
    ) -> bool:
        result = self.compute_due_score(user_id, sku_id, category, purchased_at=purchased_at, now=now)
        return result.due_score >= self.settings.replenishment_due_threshold

    def _resolve_cycle_days(self, user_id: uuid.UUID, sku_id: str, category: str) -> int:
        dates = self.history.get_sku_purchase_dates(user_id, sku_id)
        if len(dates) >= 2:
            intervals = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
            positive = [d for d in intervals if d > 0]
            if positive:
                return max(int(sum(positive) / len(positive)), self._cycles.get("min_days_between_reminders", 7))

        categories = self._cycles.get("categories", {})
        return int(categories.get(category, self._cycles.get("default_days", 30)))
