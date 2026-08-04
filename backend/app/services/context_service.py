"""Aggregated checkout context signals."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from app.config import Settings, get_settings
from app.context.season_provider import SeasonProvider
from app.context.weather_provider import WeatherProvider
from app.services.redis_client import get_redis_client


@dataclass
class CheckoutContextBundle:
    season: str
    season_label: str
    weather: dict[str, Any]
    cart_categories: list[str] = field(default_factory=list)
    upcoming_events: list[dict[str, Any]] = field(default_factory=list)
    festival: str | None = None


class ContextService:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.season = SeasonProvider()
        self.weather = WeatherProvider(self.settings)

    def get_checkout_context(
        self,
        *,
        user_id: uuid.UUID,
        pincode: str,
        usl_rows: list[dict],
        cart_categories: set[str],
        when: datetime | None = None,
    ) -> CheckoutContextBundle:
        now = when or datetime.now(timezone.utc)
        day = now.date()
        cache_key = f"context:checkout:{user_id}:{pincode}:{day.isoformat()}"

        cached = self._read_cache(cache_key)
        if cached:
            return CheckoutContextBundle(**cached)

        current_season = self.season.get_current_season(now)
        weather = self.weather.get_forecast(pincode, day)
        upcoming_events = self._collect_upcoming_events(usl_rows, now)

        bundle = CheckoutContextBundle(
            season=current_season["id"],
            season_label=current_season["name"],
            weather=weather,
            cart_categories=sorted(cart_categories),
            upcoming_events=upcoming_events,
            festival=self.season.get_active_festival(now),
        )

        self._write_cache(cache_key, bundle)
        return bundle

    def _collect_upcoming_events(self, usl_rows: list[dict], now: datetime) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        window = self.settings.event_window_days

        for row in usl_rows:
            event_date = row.get("event_date")
            if not event_date:
                continue
            if isinstance(event_date, str):
                event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))
            if event_date.tzinfo is None:
                event_date = event_date.replace(tzinfo=timezone.utc)

            days_until = (event_date.date() - now.date()).days
            if 0 <= days_until <= window:
                events.append(
                    {
                        "item_id": str(row["item_id"]),
                        "event_date": event_date.date().isoformat(),
                        "days_until": days_until,
                        "label": row.get("raw_intent", "event"),
                    }
                )

        events.sort(key=lambda e: e["days_until"])
        return events

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        try:
            client = get_redis_client(self.settings)
            raw = client.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return None

    def _write_cache(self, key: str, bundle: CheckoutContextBundle) -> None:
        payload = {
            "season": bundle.season,
            "season_label": bundle.season_label,
            "weather": bundle.weather,
            "cart_categories": bundle.cart_categories,
            "upcoming_events": bundle.upcoming_events,
            "festival": bundle.festival,
        }
        try:
            client = get_redis_client(self.settings)
            client.setex(key, self.settings.context_cache_ttl_seconds, json.dumps(payload))
        except Exception:
            pass
