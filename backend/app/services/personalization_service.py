"""Personalization signals from recommendation history."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import CatalogProduct, RecommendationEvent


@dataclass
class PersonalizationContext:
    category_acceptance: dict[str, float] = field(default_factory=dict)
    category_dismissal: dict[str, float] = field(default_factory=dict)
    capped_sku_ids: set[str] = field(default_factory=set)
    recently_shown_sku_ids: set[str] = field(default_factory=set)


class PersonalizationService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()

    def load(self, user_id: uuid.UUID) -> PersonalizationContext:
        events = list(
            self.db.scalars(
                select(RecommendationEvent)
                .where(RecommendationEvent.user_id == user_id)
                .order_by(RecommendationEvent.created_at.desc())
            ).all()
        )

        category_shown: dict[str, int] = {}
        category_accepted: dict[str, int] = {}
        category_dismissed: dict[str, int] = {}
        capped_skus: set[str] = set()
        recently_shown: set[str] = set()

        freq_cutoff = datetime.now(timezone.utc) - timedelta(days=self.settings.frequency_cap_days)
        dismiss_cutoff = datetime.now(timezone.utc) - timedelta(days=self.settings.dismiss_cooldown_days)

        sku_to_category = self._build_sku_category_map(events)

        for event in events:
            category = sku_to_category.get(event.sku_id, "unknown")

            if event.action == "shown":
                category_shown[category] = category_shown.get(category, 0) + 1
                created_at = event.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at >= freq_cutoff:
                    recently_shown.add(event.sku_id)

            if event.action == "added_to_cart":
                category_accepted[category] = category_accepted.get(category, 0) + 1

            if event.action == "dismissed":
                category_dismissed[category] = category_dismissed.get(category, 0) + 1
                created_at = event.created_at
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at >= dismiss_cutoff:
                    capped_skus.add(event.sku_id)

        acceptance_rates: dict[str, float] = {}
        for category, shown in category_shown.items():
            accepted = category_accepted.get(category, 0)
            acceptance_rates[category] = accepted / shown if shown else 0.0

        dismissal_rates: dict[str, float] = {}
        for category, shown in category_shown.items():
            dismissed = category_dismissed.get(category, 0)
            dismissal_rates[category] = dismissed / shown if shown else 0.0

        return PersonalizationContext(
            category_acceptance=acceptance_rates,
            category_dismissal=dismissal_rates,
            capped_sku_ids=capped_skus,
            recently_shown_sku_ids=recently_shown,
        )

    def _build_sku_category_map(self, events: list[RecommendationEvent]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        for event in events:
            if event.sku_id in mapping:
                continue
            product = self.db.get(CatalogProduct, event.sku_id)
            mapping[event.sku_id] = product.category if product else "unknown"
        return mapping
