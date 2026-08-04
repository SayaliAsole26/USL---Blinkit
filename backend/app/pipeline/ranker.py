"""Deterministic recommendation ranker with externalized weights."""

from __future__ import annotations

from app.pipeline.checkout_rules import CheckoutCandidate
from app.services.personalization_service import PersonalizationContext
from app.services.ranker_config import RankerWeights


class RecommendationRanker:
    def __init__(self, weights: RankerWeights):
        self.weights = weights

    def rank(
        self,
        candidates: list[CheckoutCandidate],
        personalization: PersonalizationContext,
    ) -> list[CheckoutCandidate]:
        ranked: list[CheckoutCandidate] = []

        for candidate in candidates:
            reason_weight = self.weights.for_reason_type(candidate.reason_type)
            acceptance = personalization.category_acceptance.get(candidate.category.lower(), 0.0)
            if acceptance == 0.0:
                acceptance = personalization.category_acceptance.get(candidate.category, 0.0)

            dismissal = personalization.category_dismissal.get(candidate.category.lower(), 0.0)
            if dismissal == 0.0:
                dismissal = personalization.category_dismissal.get(candidate.category, 0.0)

            score = candidate.score * reason_weight
            score += acceptance * self.weights.acceptance_boost
            score -= dismissal * self.weights.dismissal_penalty

            candidate.score = max(0.0, min(score, 1.0))
            ranked.append(candidate)

        ranked.sort(key=lambda c: c.score, reverse=True)
        return ranked
