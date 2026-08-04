"""Static India season calendar — no external API."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any


def _calendar_path() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "season-calendar.json"


@lru_cache
def _load_calendar() -> dict[str, Any]:
    return json.loads(_calendar_path().read_text(encoding="utf-8"))


class SeasonProvider:
    def get_current_season(self, when: datetime | None = None) -> dict[str, Any]:
        now = when or datetime.now(timezone.utc)
        month = now.month
        seasons = _load_calendar()["seasons"]

        for season in seasons:
            if month in season["months"]:
                return {
                    "id": season["id"],
                    "name": season["name"],
                    "month": month,
                }

        return {"id": "general", "name": "General", "month": month}

    def is_seasonal_match(
        self,
        season_id: str,
        *,
        raw_intent: str = "",
        normalized_name: str = "",
        category: str = "",
        product_name: str = "",
    ) -> bool:
        seasons = _load_calendar()["seasons"]
        season = next((s for s in seasons if s["id"] == season_id), None)
        if not season:
            return False

        haystack = " ".join(
            part.lower()
            for part in (raw_intent, normalized_name, category, product_name)
            if part
        )
        if any(keyword in haystack for keyword in season.get("keywords", [])):
            return True

        normalized_category = category.lower()
        return normalized_category in {c.lower() for c in season.get("categories", [])}

    def get_active_festival(self, when: datetime | None = None) -> str | None:
        now = when or datetime.now(timezone.utc)
        for festival in _load_calendar().get("festivals", []):
            if now.month != festival["month"]:
                continue
            start, end = festival["day_range"]
            if start <= now.day <= end:
                return festival["name"]
        return None
