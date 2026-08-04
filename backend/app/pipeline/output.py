"""Output stage — validation gate and Top N response."""

import uuid
from dataclasses import dataclass
from typing import Any

VALID_REASON_TYPES = {
    "memory_reminder",
    "replenishment_reminder",
    "weather_context",
    "seasonal_context",
    "event_based",
    "cross_category_discovery",
    "shopping_completion",
}


@dataclass
class RecommendationOutput:
    recommendation_id: str
    sku_id: str
    product_name: str
    reason_type: str
    reason_text: str
    confidence: float


class OutputService:
    def __init__(self, max_output: int = 5):
        self.MAX_OUTPUT = max_output

    def build_recommendations(
        self,
        candidates: list[Any],
        reason_texts: dict[str, str],
    ) -> list[RecommendationOutput]:
        outputs: list[RecommendationOutput] = []

        for candidate in candidates[: self.MAX_OUTPUT]:
            reason_type = getattr(candidate, "reason_type", "memory_reminder")
            reason_text = reason_texts.get(candidate.sku_id, "")

            if reason_type not in VALID_REASON_TYPES:
                continue
            if not reason_text.strip():
                continue

            outputs.append(
                RecommendationOutput(
                    recommendation_id=f"rec_{uuid.uuid4().hex[:12]}",
                    sku_id=candidate.sku_id,
                    product_name=candidate.product_name,
                    reason_type=reason_type,
                    reason_text=reason_text,
                    confidence=getattr(candidate, "score", 0.5),
                )
            )

        return outputs
