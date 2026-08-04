"""Checkout filtering rules R1, R6, R7 for Path B."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


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


@dataclass
class CheckoutFilterContext:
    pincode: str
    cart_sku_ids: set[str]
    cart_categories: set[str]
    dismissed_item_ids: set[uuid.UUID]
    available_usl_count: int = 0


class CheckoutRulesEngine:
    ACTIVE_RULES = {"R1", "R6", "R7"}

    def build_candidates(
        self,
        usl_rows: list[dict],
        context: CheckoutFilterContext,
        max_shortlist: int = 80,
    ) -> list[CheckoutCandidate]:
        candidates: list[CheckoutCandidate] = []

        for row in usl_rows:
            if row["item_id"] in context.dismissed_item_ids:
                continue
            if row["status"] not in {"pending", "saved_for_later"}:
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

            category = top_match.get("category") or row.get("category") or "unknown"
            reason_type = self._resolve_reason_type(category, context)
            score = float(top_match.get("match_confidence", 0.5))
            if reason_type == "cross_category_discovery":
                score += 0.15
            if reason_type == "shopping_completion" and context.available_usl_count > 1:
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
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:max_shortlist]

    def _resolve_reason_type(self, usl_category: str, context: CheckoutFilterContext) -> str:
        normalized = usl_category.lower()
        cart_categories = {c.lower() for c in context.cart_categories}

        if cart_categories and normalized not in cart_categories and not cart_categories.intersection({normalized}):
            if any(normalized not in c and c not in normalized for c in cart_categories):
                return "cross_category_discovery"

        if context.available_usl_count > 1:
            return "shopping_completion"

        return "memory_reminder"

    @staticmethod
    def get_dismissed_item_ids(events: list[dict], cooldown_days: int) -> set[uuid.UUID]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=cooldown_days)
        dismissed: set[uuid.UUID] = set()
        for event in events:
            if event.get("action") != "dismissed":
                continue
            if event.get("created_at") and event["created_at"] < cutoff:
                continue
            item_id = event.get("item_id")
            if item_id:
                dismissed.add(item_id)
        return dismissed
