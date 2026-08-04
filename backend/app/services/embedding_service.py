"""Embedding generation and pgvector storage."""

from __future__ import annotations

import hashlib
import logging
import math
from functools import lru_cache

from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import CatalogProduct, CatalogProductEmbedding

logger = logging.getLogger(__name__)
EMBEDDING_DIM = 384


class EmbeddingService:
    _model = None
    _model_name: str | None = None

    def __init__(self, settings: Settings):
        self.settings = settings

    def embed_text(self, text: str) -> list[float]:
        if self.settings.embeddings_enabled:
            model = self._get_model()
            if model is not None:
                vector = model.encode(text, normalize_embeddings=True)
                return vector.tolist()
        return self._pseudo_embed(text)

    def embed_catalog_product(self, db: Session, product: CatalogProduct) -> None:
        text = f"{product.product_name} {product.category}"
        vector = self.embed_text(text)
        row = db.get(CatalogProductEmbedding, product.sku_id)
        if row:
            row.embedding = vector
        else:
            db.add(CatalogProductEmbedding(sku_id=product.sku_id, embedding=vector))
        db.commit()

    def embed_all_catalog(self, db: Session) -> int:
        products = db.query(CatalogProduct).all()
        count = 0
        for product in products:
            self.embed_catalog_product(db, product)
            count += 1
        return count

    def _get_model(self):
        if EmbeddingService._model is not None and EmbeddingService._model_name == self.settings.embedding_model:
            return EmbeddingService._model
        try:
            from sentence_transformers import SentenceTransformer

            EmbeddingService._model = SentenceTransformer(self.settings.embedding_model)
            EmbeddingService._model_name = self.settings.embedding_model
            return EmbeddingService._model
        except Exception as exc:  # pragma: no cover - optional heavy dependency
            logger.warning("Embedding model unavailable, using pseudo embeddings: %s", exc)
            return None

    @staticmethod
    def _pseudo_embed(text: str) -> list[float]:
        """Deterministic lightweight fallback when sentence-transformers is unavailable."""
        seed = hashlib.sha256(text.lower().encode()).digest()
        values: list[float] = []
        for i in range(EMBEDDING_DIM):
            byte = seed[i % len(seed)]
            values.append((byte / 255.0) * 2 - 1)
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    @staticmethod
    def cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
        norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
        return dot / (norm_a * norm_b)
