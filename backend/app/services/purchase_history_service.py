"""Purchase history ingestion from orders and Blinkit history."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CatalogProduct, PurchaseHistory


class PurchaseHistoryService:
    def __init__(self, db: Session):
        self.db = db

    def record_order_purchases(
        self,
        user_id: uuid.UUID,
        sku_ids: list[str],
        order_id: str,
        *,
        source: str = "order",
        purchased_at: datetime | None = None,
    ) -> int:
        if not sku_ids:
            return 0

        when = purchased_at or datetime.now(timezone.utc)
        recorded = 0
        for sku_id in sku_ids:
            product = self.db.get(CatalogProduct, sku_id)
            if not product:
                continue
            self.db.add(
                PurchaseHistory(
                    user_id=user_id,
                    sku_id=sku_id,
                    product_name=product.product_name,
                    category=product.category,
                    quantity=1,
                    order_id=order_id,
                    source=source,
                    purchased_at=when,
                )
            )
            recorded += 1

        if recorded:
            self.db.flush()
        return recorded

    def get_user_history(self, user_id: uuid.UUID) -> list[PurchaseHistory]:
        return list(
            self.db.scalars(
                select(PurchaseHistory)
                .where(PurchaseHistory.user_id == user_id)
                .order_by(PurchaseHistory.purchased_at.desc())
            ).all()
        )

    def get_last_purchase(self, user_id: uuid.UUID, sku_id: str) -> PurchaseHistory | None:
        return self.db.scalars(
            select(PurchaseHistory)
            .where(PurchaseHistory.user_id == user_id, PurchaseHistory.sku_id == sku_id)
            .order_by(PurchaseHistory.purchased_at.desc())
            .limit(1)
        ).first()

    def get_sku_purchase_dates(self, user_id: uuid.UUID, sku_id: str) -> list[datetime]:
        rows = self.db.scalars(
            select(PurchaseHistory.purchased_at)
            .where(PurchaseHistory.user_id == user_id, PurchaseHistory.sku_id == sku_id)
            .order_by(PurchaseHistory.purchased_at.asc())
        ).all()
        return list(rows)
