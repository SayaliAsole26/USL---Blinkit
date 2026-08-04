"""Checkout filtering rules R1, R2, R3–R7 for Path B."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.personalization_service import PersonalizationContext


@dataclass
class CheckoutContextSignals:
    season: str = "general"
    season_label: str = "General"
    weather: dict[str, Any] = field(default_factory=dict)
    upcoming_event_item_ids: set[uuid.UUID] = field(default_factory=set)
    event_details: dict[uuid.UUID, dict[str, Any]] = field(default_factory=dict)


@dataclass
class CheckoutCandidate:
    usl_item_id: uuid.UUID
    sku_id: str
    product_name: str
    category: str
    price: float
    image_url: str | None
    raw_intent: str
    reason_type: str
    score: float
    match_confidence: float
    context_signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckoutFilterContext:
    pincode: str
    cart_sku_ids: set[str]
    cart_categories: set[str]
    dismissed_item_ids: set[uuid.UUID]
    available_usl_count: int = 0
    context: CheckoutContextSignals | None = None
    personalization: PersonalizationContext | None = None


class CheckoutRulesEngine:
    ACTIVE_RULES = {"R1", "R2", "R3", "R4", "R5", "R6", "R7"}

    def build_candidates(
        self,
        usl_rows: list[dict],
        context: CheckoutFilterContext,
        max_shortlist: int = 80,
    ) -> list[CheckoutCandidate]:
        candidates: list[CheckoutCandidate] = []
        personalization = context.personalization

        for row in usl_rows:
            is_replenishment_row = row.get("status") == "purchased" and row.get("replenishment_due")

            if is_replenishment_row:
                if row["match_status"] != "matched":
                    continue
            elif row["status"] not in {"pending", "saved_for_later"}:
                continue

            if row["item_id"] in context.dismissed_item_ids:
                continue
            if row["match_status"] != "matched":
                continue

            top_match = row.get("top_match")
            if not top_match:
                continue

            sku_id = top_match["sku_id"]
            if sku_id in context.cart_sku_ids:
                continue
            if top_match.get("availability_status") != "available":
                continue
            if personalization and sku_id in personalization.capped_sku_ids:
                continue
            if personalization and sku_id in personalization.recently_shown_sku_ids:
                continue

            category = top_match.get("category") or row.get("category") or "unknown"

            if is_replenishment_row:
                replenishment = row["replenishment_due"]
                reason_type = "replenishment_reminder"
                context_signals = {
                    "days_since_purchase": replenishment.days_since_purchase,
                    "cycle_days": replenishment.cycle_days,
                    "due_score": replenishment.due_score,
                }
                score = float(replenishment.due_score)
            else:
                reason_type, context_signals = self._resolve_reason_type(row, category, context, top_match)
                score = float(top_match.get("match_confidence", 0.5))
                if reason_type == "event_based":
                    score += 0.25
                elif reason_type == "weather_context":
                    score += 0.2
                elif reason_type == "seasonal_context":
                    score += 0.18
                elif reason_type == "cross_category_discovery":
                    score += 0.15
                elif reason_type == "shopping_completion" and context.available_usl_count > 1:
                    score += 0.1

            candidates.append(
                CheckoutCandidate(
                    usl_item_id=row["item_id"],
                    sku_id=sku_id,
                    product_name=top_match["product_name"],
                    category=category,
                    price=float(top_match["price"]),
                    image_url=top_match.get("image_url"),
                    raw_intent=row["raw_intent"],
                    reason_type=reason_type,
                    score=min(score, 1.0),
                    match_confidence=float(top_match.get("match_confidence", 0.5)),
                    context_signals=context_signals,
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:max_shortlist]

    def _resolve_reason_type(
        self,
        row: dict,
        usl_category: str,
        context: CheckoutFilterContext,
        top_match: dict,
    ) -> tuple[str, dict[str, Any]]:
        ctx = context.context
        item_id = row["item_id"]
        text_fields = {
            "raw_intent": row.get("raw_intent", ""),
            "normalized_name": row.get("normalized_name") or "",
            "category": usl_category,
            "product_name": top_match.get("product_name") or "",
        }

        if ctx and item_id in ctx.upcoming_event_item_ids:
            details = ctx.event_details.get(item_id, {})
            return "event_based", {
                "event_date": details.get("event_date"),
                "days_until": details.get("days_until"),
                "event_label": details.get("label", row.get("raw_intent")),
            }

        if ctx and self._matches_weather_rule(text_fields, ctx):
            return "weather_context", {
                "forecast": ctx.weather.get("forecast"),
                "severity": ctx.weather.get("severity"),
                "days_ahead": ctx.weather.get("days_ahead"),
            }

        if ctx and self._matches_seasonal_rule(text_fields, ctx):
            return "seasonal_context", {
                "season": ctx.season,
                "season_label": ctx.season_label,
            }

        normalized = usl_category.lower()
        cart_categories = {c.lower() for c in context.cart_categories}

        if cart_categories and normalized not in cart_categories and not cart_categories.intersection({normalized}):
            if any(normalized not in c and c not in normalized for c in cart_categories):
                return "cross_category_discovery", {}

        if context.available_usl_count > 1:
            return "shopping_completion", {}

        return "memory_reminder", {}

    @staticmethod
    def _matches_weather_rule(text_fields: dict[str, str], ctx: CheckoutContextSignals) -> bool:
        from app.context.weather_provider import WeatherProvider

        forecast = ctx.weather.get("forecast", "clear")
        if forecast not in {"rain", "heavy_rain"}:
            return False
        return WeatherProvider().is_weather_relevant_item(**text_fields)

    @staticmethod
    def _matches_seasonal_rule(text_fields: dict[str, str], ctx: CheckoutContextSignals) -> bool:
        from app.context.season_provider import SeasonProvider

        if ctx.season == "general":
            return False
        return SeasonProvider().is_seasonal_match(ctx.season, **text_fields)

    @staticmethod
    def get_dismissed_item_ids(events: list[dict], cooldown_days: int) -> set[uuid.UUID]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
        dismissed: set[uuid.UUID] = set()
        for event in events:
            if event.get("action") != "dismissed":
                continue
            created_at = event.get("created_at")
            if created_at:
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)
                if created_at < cutoff:
                    continue
            item_id = event.get("item_id")
            if item_id:
                dismissed.add(item_id)
        return dismissed
