"""Catalog search — Meilisearch + pgvector + PostgreSQL FTS fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import CatalogProduct, CatalogProductEmbedding
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class CatalogSearchHit:
    sku_id: str
    product_name: str
    category: str
    price: float
    image_url: str | None
    score: float
    source: str


class CatalogMatcherService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.embeddings = EmbeddingService(settings)

    def search(self, query: str, limit: int = 40) -> list[CatalogSearchHit]:
        merged: dict[str, CatalogSearchHit] = {}

        for hit in self._search_postgres(query, limit):
            merged[hit.sku_id] = hit

        for hit in self._search_meilisearch(query, limit):
            existing = merged.get(hit.sku_id)
            if existing:
                existing.score = max(existing.score, hit.score)
                existing.source = f"{existing.source}+{hit.source}"
            else:
                merged[hit.sku_id] = hit

        if self.settings.embeddings_enabled:
            intent_vector = self.embeddings.embed_text(query)
            for hit in self._search_vectors(intent_vector, limit):
                existing = merged.get(hit.sku_id)
                if existing:
                    existing.score = max(existing.score, hit.score)
                    existing.source = f"{existing.source}+{hit.source}"
                else:
                    merged[hit.sku_id] = hit

        hits = sorted(merged.values(), key=lambda h: h.score, reverse=True)
        return hits[:limit]

    def _search_postgres(self, query: str, limit: int) -> list[CatalogSearchHit]:
        tokens = [t.strip() for t in query.lower().split() if t.strip()]
        if not tokens:
            return []

        filters = [CatalogProduct.product_name.ilike(f"%{token}%") for token in tokens]
        rows = self.db.query(CatalogProduct).filter(or_(*filters)).limit(limit).all()
        hits: list[CatalogSearchHit] = []
        for row in rows:
            score = self._keyword_score(query, row.product_name, row.category)
            hits.append(
                CatalogSearchHit(
                    sku_id=row.sku_id,
                    product_name=row.product_name,
                    category=row.category,
                    price=float(row.price),
                    image_url=row.image_url,
                    score=score,
                    source="postgres",
                )
            )
        return hits

    def _search_meilisearch(self, query: str, limit: int) -> list[CatalogSearchHit]:
        if not self.settings.meili_enabled or not self.settings.meili_url:
            return []
        try:
            import meilisearch
        except ImportError:
            return []

        try:
            client = meilisearch.Client(self.settings.meili_url, self.settings.meili_master_key, timeout=1000)
            index = client.index(self.settings.meili_index)
            result = index.search(query, {"limit": limit})
            hits: list[CatalogSearchHit] = []
            for doc in result.get("hits", []):
                score = 1.0 - (doc.get("_rankingScore") or 0.5) if "_rankingScore" in doc else 0.7
                hits.append(
                    CatalogSearchHit(
                        sku_id=doc["sku_id"],
                        product_name=doc["product_name"],
                        category=doc["category"],
                        price=float(doc["price"]),
                        image_url=doc.get("image_url"),
                        score=min(max(score, 0.1), 1.0),
                        source="meilisearch",
                    )
                )
            return hits
        except Exception as exc:
            logger.debug("Meilisearch unavailable: %s", exc)
            return []

    def _search_vectors(self, query_vector: list[float], limit: int) -> list[CatalogSearchHit]:
        if "postgresql" not in self.settings.database_url:
            return []

        try:
            from pgvector.sqlalchemy import Vector  # noqa: F401

            distance = CatalogProductEmbedding.embedding.cosine_distance(query_vector)
            rows = (
                self.db.query(CatalogProductEmbedding, CatalogProduct)
                .join(CatalogProduct, CatalogProduct.sku_id == CatalogProductEmbedding.sku_id)
                .order_by(distance)
                .limit(limit)
                .all()
            )
            hits: list[CatalogSearchHit] = []
            for embedding_row, product in rows:
                hits.append(
                    CatalogSearchHit(
                        sku_id=product.sku_id,
                        product_name=product.product_name,
                        category=product.category,
                        price=float(product.price),
                        image_url=product.image_url,
                        score=0.65,
                        source="pgvector",
                    )
                )
            return hits
        except Exception as exc:
            logger.debug("Vector search unavailable: %s", exc)
            return []

    @staticmethod
    def _keyword_score(query: str, product_name: str, category: str) -> float:
        q = query.lower()
        name = product_name.lower()
        cat = category.lower()
        score = 0.0
        if q in name:
            score += 0.8
        for token in q.split():
            if token in name:
                score += 0.15
            if token in cat:
                score += 0.05
        return min(score, 1.0)
