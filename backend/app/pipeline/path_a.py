"""Path A — USL ingestion pipeline (Dataset → Filter → LLM → Output)."""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import CatalogMatch, UslItem, UslItemMetadata, UserLocation
from app.integrations.mock_blinkit import MockInventoryAdapter
from app.pipeline.filter import FilteringService
from app.pipeline.llm import GroqLLMService
from app.services.catalog_matcher import CatalogMatcherService
from app.services.pipeline_metrics import record_path_a_run

logger = logging.getLogger(__name__)

INTENT_QUERY_HINTS: dict[str, list[str]] = {
    "face wash": ["face wash", "cetaphil"],
    "moisturizer": ["moisturizer", "nivea"],
    "airpods": ["airpods", "earbuds", "airdopes"],
    "earbuds": ["earbuds", "airdopes", "bluetooth"],
    "dog food": ["dog food", "pedigree"],
}


class PathAProcessor:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.matcher = CatalogMatcherService(db, settings)
        self.filtering = FilteringService(max_shortlist=settings.max_catalog_shortlist)
        self.llm = GroqLLMService(settings)
        self.inventory = MockInventoryAdapter(db)

    def process(self, item_id: uuid.UUID, user_id: uuid.UUID, trigger: str = "created") -> dict:
        started = time.perf_counter()
        item = self.db.get(UslItem, item_id)
        if not item or item.user_id != user_id:
            return {"ok": False, "reason": "item_not_found"}

        location = self.db.get(UserLocation, user_id)
        pincode = location.pincode if location else "560001"

        item.match_status = "processing"
        self.db.commit()

        try:
            intent_data = self.llm.parse_intent(item.raw_intent)
            search_query = self._build_search_query(item.raw_intent, intent_data)
            catalog_hits = self.matcher.search(search_query, limit=self.settings.max_catalog_shortlist)

            catalog_rows = [
                {
                    "sku_id": hit.sku_id,
                    "product_name": hit.product_name,
                    "category": hit.category,
                    "price": hit.price,
                    "image_url": hit.image_url,
                    "score": hit.score,
                    "source": hit.source,
                }
                for hit in catalog_hits
            ]

            shortlist = self.filtering.filter_catalog_matches(
                catalog_rows,
                pincode=pincode,
                availability_checker=self.inventory.check_availability,
            )
            shortlist_payload = [
                {
                    "sku_id": c.sku_id,
                    "product_name": c.product_name,
                    "category": c.category,
                    "score": c.score,
                }
                for c in shortlist
            ]

            llm_candidates = shortlist_payload[: self.settings.max_catalog_shortlist]
            selected = self.llm.select_matches_from_shortlist(
                item.raw_intent,
                intent_data,
                llm_candidates,
                max_matches=self.settings.max_catalog_matches,
            )

            threshold = self.settings.match_confidence_threshold
            selected = [m for m in selected if m.get("match_confidence", 0) >= threshold]

            self._persist_results(item, intent_data, pincode, shortlist_payload, selected, started, trigger)
            latency_ms = int((time.perf_counter() - started) * 1000)
            record_path_a_run(
                shortlist_size=len(shortlist_payload),
                llm_candidate_size=len(llm_candidates),
                latency_ms=latency_ms,
                match_count=len(selected),
            )
            return {
                "ok": True,
                "item_id": str(item_id),
                "match_status": item.match_status,
                "matches": len(selected),
                "shortlist_size": len(shortlist_payload),
                "llm_candidate_size": len(llm_candidates),
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            logger.exception("Path A processing failed for %s", item_id)
            self._persist_error(item, str(exc), started)
            raise

    def _build_search_query(self, raw_intent: str, intent_data: dict) -> str:
        normalized = (intent_data.get("normalized_name") or raw_intent).strip()
        lowered = normalized.lower()
        raw_lower = raw_intent.lower()
        for key, hints in INTENT_QUERY_HINTS.items():
            if key in lowered or key in raw_lower:
                return " ".join(hints)
        return normalized

    def _persist_results(
        self,
        item: UslItem,
        intent_data: dict,
        pincode: str,
        shortlist: list[dict],
        selected: list[dict],
        started: float,
        trigger: str,
    ) -> None:
        self.db.query(CatalogMatch).filter(CatalogMatch.item_id == item.item_id).delete()

        item.normalized_name = intent_data.get("normalized_name") or item.raw_intent
        item.category = intent_data.get("category")
        item.match_status = "matched" if selected else "unmatched"
        if item.status == "pending" and not selected:
            item.status = "pending"

        metadata = self.db.get(UslItemMetadata, item.item_id)
        if not metadata:
            metadata = UslItemMetadata(item_id=item.item_id)
            self.db.add(metadata)

        metadata.attributes = intent_data.get("attributes") or {}
        metadata.intent_confidence = float(intent_data.get("confidence") or 0.0)
        metadata.tags = [trigger, intent_data.get("category") or "unknown"]
        metadata.shortlist_size = len(shortlist)
        metadata.processing_latency_ms = int((time.perf_counter() - started) * 1000)
        metadata.last_processed_at = datetime.now(timezone.utc)
        metadata.last_error = None

        for rank, match in enumerate(selected, start=1):
            availability = self.inventory.check_availability(match["sku_id"], pincode)
            self.db.add(
                CatalogMatch(
                    item_id=item.item_id,
                    sku_id=match["sku_id"],
                    match_confidence=float(match.get("match_confidence", match.get("score", 0.5))),
                    availability_status=availability,
                    pincode=pincode,
                    rank=rank,
                )
            )

        self.db.commit()
        self.db.refresh(item)

    def _persist_error(self, item: UslItem, error: str, started: float) -> None:
        item.match_status = "unmatched"
        metadata = self.db.get(UslItemMetadata, item.item_id)
        if not metadata:
            metadata = UslItemMetadata(item_id=item.item_id)
            self.db.add(metadata)
        metadata.last_error = error[:1000]
        metadata.processing_latency_ms = int((time.perf_counter() - started) * 1000)
        metadata.last_processed_at = datetime.now(timezone.utc)
        self.db.commit()
