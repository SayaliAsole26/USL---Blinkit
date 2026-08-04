"""Path B — checkout recommendation pipeline."""

from __future__ import annotations

import time
import uuid

from sqlalchemy.orm import Session

from app.config import Settings
from app.pipeline.checkout_rules import CheckoutCandidate, CheckoutFilterContext, CheckoutRulesEngine
from app.pipeline.llm import GroqLLMService
from app.pipeline.output import OutputService, VALID_REASON_TYPES
from app.services.checkout_dataset import CheckoutDatasetService
from app.services.pipeline_metrics import record_path_b_run


class PathBProcessor:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.dataset = CheckoutDatasetService(db)
        self.rules = CheckoutRulesEngine()
        self.llm = GroqLLMService(settings)
        self.output = OutputService(max_output=settings.max_checkout_recommendations)

    def process(
        self,
        user_id: uuid.UUID,
        checkout_session_id: str,
        cart_sku_ids: list[str] | None = None,
    ) -> dict:
        started = time.perf_counter()
        bundle = self.dataset.load(user_id, cart_sku_ids=cart_sku_ids)

        available_count = sum(
            1
            for row in bundle.usl_rows
            if row.get("top_match")
            and row["top_match"].get("availability_status") == "available"
            and row["top_match"]["sku_id"] not in bundle.cart_sku_ids
            and row["item_id"] not in bundle.dismissed_item_ids
        )

        context = CheckoutFilterContext(
            pincode=bundle.pincode,
            cart_sku_ids=bundle.cart_sku_ids,
            cart_categories=bundle.cart_categories,
            dismissed_item_ids=bundle.dismissed_item_ids,
            available_usl_count=available_count,
        )

        shortlist = self.rules.build_candidates(
            bundle.usl_rows,
            context,
            max_shortlist=self.settings.max_checkout_shortlist,
        )

        llm_targets = shortlist[: self.settings.max_checkout_recommendations]
        reason_texts = self._build_reason_texts(llm_targets, bundle.cart_categories)

        validated = self.output.build_recommendations(llm_targets, reason_texts)
        candidate_by_sku = {c.sku_id: c for c in llm_targets}
        recommendations = []
        for item in validated:
            candidate = candidate_by_sku.get(item.sku_id)
            recommendations.append(
                {
                    "recommendation_id": item.recommendation_id,
                    "usl_item_id": str(candidate.usl_item_id) if candidate else None,
                    "sku_id": item.sku_id,
                    "product_name": item.product_name,
                    "price": float(candidate.price) if candidate else 0,
                    "image_url": candidate.image_url if candidate else None,
                    "reason_type": item.reason_type,
                    "reason_text": item.reason_text,
                    "confidence": item.confidence,
                }
            )

        latency_ms = int((time.perf_counter() - started) * 1000)
        record_path_b_run(
            shortlist_size=len(shortlist),
            llm_candidate_size=len(llm_targets),
            output_count=len(recommendations),
            latency_ms=latency_ms,
        )

        return {
            "checkout_session_id": checkout_session_id,
            "recommendations": recommendations,
            "shortlist_size": len(shortlist),
            "latency_ms": latency_ms,
        }

    def _build_reason_texts(
        self,
        candidates: list[CheckoutCandidate],
        cart_categories: set[str],
    ) -> dict[str, str]:
        reason_texts: dict[str, str] = {}
        for candidate in candidates:
            if candidate.reason_type not in VALID_REASON_TYPES:
                continue
            signals = {
                "product_name": candidate.product_name,
                "raw_intent": candidate.raw_intent,
                "cart_categories": list(cart_categories),
                "usl_category": candidate.category,
            }
            reason_texts[candidate.sku_id] = self.llm.generate_reason_text(candidate.reason_type, signals)
        return reason_texts
