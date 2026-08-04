"""Checkout recommendations and user actions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.models import CatalogProduct, RecommendationEvent, UslItem
from app.integrations.mock_blinkit import get_cart_adapter
from app.pipeline.path_b import PathBProcessor
from app.schemas.recommendations import RecommendationAction


class RecommendationService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.cart = get_cart_adapter()

    def get_checkout_recommendations(
        self,
        user_id: uuid.UUID,
        checkout_session_id: str,
        cart_sku_ids: list[str] | None = None,
    ) -> dict:
        if not self.settings.usl_checkout_recommendations:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checkout recommendations disabled")

        result = PathBProcessor(self.db, self.settings).process(
            user_id,
            checkout_session_id,
            cart_sku_ids=cart_sku_ids,
        )

        for rec in result["recommendations"]:
            self._log_event(
                user_id=user_id,
                checkout_session_id=checkout_session_id,
                recommendation_id=rec["recommendation_id"],
                item_id=uuid.UUID(rec["usl_item_id"]) if rec.get("usl_item_id") else None,
                sku_id=rec["sku_id"],
                reason_type=rec["reason_type"],
                reason_text=rec["reason_text"],
                action="shown",
            )

        self.db.commit()
        return result

    def handle_action(
        self,
        user_id: uuid.UUID,
        recommendation_id: str,
        action: RecommendationAction,
        checkout_session_id: str,
    ) -> dict:
        shown = self.db.scalars(
            select(RecommendationEvent)
            .where(
                RecommendationEvent.user_id == user_id,
                RecommendationEvent.recommendation_id == recommendation_id,
                RecommendationEvent.action == "shown",
            )
            .order_by(RecommendationEvent.created_at.desc())
            .limit(1)
        ).first()

        if not shown:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found")

        self._log_event(
            user_id=user_id,
            checkout_session_id=checkout_session_id,
            recommendation_id=recommendation_id,
            item_id=shown.item_id,
            sku_id=shown.sku_id,
            reason_type=shown.reason_type,
            reason_text=shown.reason_text,
            action=action.value,
        )

        message = "Action recorded"
        if action == RecommendationAction.ADDED_TO_CART:
            self.cart.add_item(str(user_id), shown.sku_id)
            message = "Added to cart"
        elif action == RecommendationAction.SAVED_FOR_LATER and shown.item_id:
            item = self.db.get(UslItem, shown.item_id)
            if item:
                item.status = "saved_for_later"
            message = "Saved for later"
        elif action == RecommendationAction.DISMISSED and shown.item_id:
            item = self.db.get(UslItem, shown.item_id)
            if item:
                item.status = "dismissed"
            message = "Dismissed for 7 days"

        self.db.commit()
        return {
            "recommendation_id": recommendation_id,
            "action": action.value,
            "usl_item_id": shown.item_id,
            "sku_id": shown.sku_id,
            "message": message,
        }

    def handle_order_completed(self, user_id: uuid.UUID, sku_ids: list[str], order_id: str) -> tuple[int, int]:
        if not sku_ids:
            return 0, 0

        from app.db.models import CatalogMatch
        from app.services.purchase_history_service import PurchaseHistoryService

        purchase_history = PurchaseHistoryService(self.db)
        history_count = purchase_history.record_order_purchases(user_id, sku_ids, order_id)

        items = list(
            self.db.scalars(
                select(UslItem).where(
                    UslItem.user_id == user_id,
                    UslItem.status.in_(["pending", "saved_for_later"]),
                )
            ).all()
        )

        purchased_count = 0
        sku_set = set(sku_ids)
        for item in items:
            rows = self.db.scalars(select(CatalogMatch).where(CatalogMatch.item_id == item.item_id)).all()
            matched_skus = {r.sku_id for r in rows}
            if matched_skus.intersection(sku_set):
                item.status = "purchased"
                item.purchased_at = datetime.now(timezone.utc)
                purchased_count += 1

        self.db.commit()
        return purchased_count, history_count

    def _log_event(
        self,
        *,
        user_id: uuid.UUID,
        checkout_session_id: str,
        recommendation_id: str,
        item_id: uuid.UUID | None,
        sku_id: str,
        reason_type: str,
        reason_text: str,
        action: str,
    ) -> None:
        self.db.add(
            RecommendationEvent(
                user_id=user_id,
                checkout_session_id=checkout_session_id,
                recommendation_id=recommendation_id,
                item_id=item_id,
                sku_id=sku_id,
                reason_type=reason_type,
                reason_text=reason_text,
                action=action,
            )
        )
