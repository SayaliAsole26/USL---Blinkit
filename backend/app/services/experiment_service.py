"""Phase 7 — lightweight A/B experiment assignment for ranker weights."""

from __future__ import annotations

import hashlib
import uuid

from dataclasses import replace

from app.config import Settings, get_settings
from app.services.ranker_config import RankerConfigService, RankerWeights


class ExperimentService:
    VARIANTS = ("control", "boost_context", "boost_memory")

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.ranker_config = RankerConfigService(self.settings)

    def assign_variant(self, user_id: uuid.UUID) -> str:
        if not self.settings.experiments_enabled:
            return "control"
        digest = hashlib.sha256(str(user_id).encode()).hexdigest()
        bucket = int(digest[:8], 16) % len(self.VARIANTS)
        return self.VARIANTS[bucket]

    def get_ranker_weights(self, user_id: uuid.UUID) -> RankerWeights:
        base = self.ranker_config.get_weights()
        variant = self.assign_variant(user_id)
        if variant == "boost_context":
            return replace(
                base,
                weather_context=base.weather_context * 1.25,
                seasonal_context=base.seasonal_context * 1.25,
                event_based=base.event_based * 1.25,
            )
        if variant == "boost_memory":
            return replace(
                base,
                memory_reminder=base.memory_reminder * 1.25,
                replenishment_reminder=base.replenishment_reminder * 1.25,
            )
        return base
