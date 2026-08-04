"""Externalized ranker weights — loaded from JSON without code deploy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config import Settings, get_settings


def _weights_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "ranker-weights.json"


@dataclass
class RankerWeights:
    memory_reminder: float = 1.0
    replenishment_reminder: float = 1.2
    weather_context: float = 1.0
    seasonal_context: float = 0.9
    event_based: float = 1.1
    cross_category_discovery: float = 0.85
    shopping_completion: float = 0.8
    acceptance_boost: float = 0.15
    dismissal_penalty: float = 0.2

    def for_reason_type(self, reason_type: str) -> float:
        return getattr(self, reason_type, 1.0)


class RankerConfigService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def get_weights(self) -> RankerWeights:
        payload = self._load_payload()
        return RankerWeights(
            memory_reminder=float(payload.get("memory_reminder", 1.0)),
            replenishment_reminder=float(payload.get("replenishment_reminder", 1.2)),
            weather_context=float(payload.get("weather_context", 1.0)),
            seasonal_context=float(payload.get("seasonal_context", 0.9)),
            event_based=float(payload.get("event_based", 1.1)),
            cross_category_discovery=float(payload.get("cross_category_discovery", 0.85)),
            shopping_completion=float(payload.get("shopping_completion", 0.8)),
            acceptance_boost=float(payload.get("acceptance_boost", 0.15)),
            dismissal_penalty=float(payload.get("dismissal_penalty", 0.2)),
        )

    def _load_payload(self) -> dict[str, Any]:
        if self.settings.ranker_weights_json:
            try:
                return json.loads(self.settings.ranker_weights_json)
            except json.JSONDecodeError:
                pass

        path = _weights_path()
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}
