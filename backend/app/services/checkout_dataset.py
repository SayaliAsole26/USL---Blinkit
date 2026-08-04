"""Checkout fixed dataset aggregation for Path B."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import desc, nulls_last, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.models import CatalogMatch, CatalogProduct, RecommendationEvent, UserLocation, UslItem
from app.integrations.mock_blinkit import get_cart_adapter, MockInventoryAdapter
from app.pipeline.checkout_rules import CheckoutRulesEngine


@dataclass
class CheckoutDatasetBundle:
    pincode: str
    usl_rows: list[dict]
    cart_sku_ids: set[str]
    cart_categories: set[str]
    dismissed_item_ids: set[uuid.UUID]


class CheckoutDatasetService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.inventory = MockInventoryAdapter(db)
        self.cart = get_cart_adapter()

    def load(self, user_id: uuid.UUID, cart_sku_ids: list[str] | None = None) -> CheckoutDatasetBundle:
        location = self.db.get(UserLocation, user_id)
        pincode = location.pincode if location else "560001"

        cart_items = self.cart.get_cart(str(user_id))
        cart_skus = {item.sku_id for item in cart_items}
        if cart_sku_ids:
            cart_skus.update(cart_sku_ids)

        cart_categories: set[str] = set()
        for sku_id in cart_skus:
            product = self.db.get(CatalogProduct, sku_id)
            if product:
                cart_categories.add(product.category)

        dismiss_events = self._load_dismiss_events(user_id)
        dismissed_item_ids = CheckoutRulesEngine.get_dismissed_item_ids(
            dismiss_events,
            self.settings.dismiss_cooldown_days,
        )

        usl_items = list(
            self.db.scalars(
                select(UslItem)
                .where(UslItem.user_id == user_id)
                .order_by(nulls_last(desc(UslItem.priority)), UslItem.created_at.desc())
            ).all()
        )

        usl_rows: list[dict] = []
        for item in usl_items:
            top_match = self._get_top_match(item.item_id, pincode)
            usl_rows.append(
                {
                    "item_id": item.item_id,
                    "raw_intent": item.raw_intent,
                    "normalized_name": item.normalized_name,
                    "category": item.category,
                    "status": item.status,
                    "match_status": item.match_status,
                    "priority": item.priority,
                    "top_match": top_match,
                }
            )

        return CheckoutDatasetBundle(
            pincode=pincode,
            usl_rows=usl_rows,
            cart_sku_ids=cart_skus,
            cart_categories=cart_categories,
            dismissed_item_ids=dismissed_item_ids,
        )

    def _get_top_match(self, item_id: uuid.UUID, pincode: str) -> dict | None:
        match = self.db.scalars(
            select(CatalogMatch).where(CatalogMatch.item_id == item_id).order_by(CatalogMatch.rank).limit(1)
        ).first()
        if not match:
            return None

        product = self.db.get(CatalogProduct, match.sku_id)
        if not product:
            return None

        availability = self.inventory.check_availability(match.sku_id, pincode)
        return {
            "sku_id": match.sku_id,
            "product_name": product.product_name,
            "category": product.category,
            "price": float(product.price),
            "image_url": product.image_url,
            "match_confidence": match.match_confidence,
            "availability_status": availability,
        }

    def _load_dismiss_events(self, user_id: uuid.UUID) -> list[dict]:
        rows = self.db.scalars(
            select(RecommendationEvent)
            .where(RecommendationEvent.user_id == user_id, RecommendationEvent.action == "dismissed")
            .order_by(RecommendationEvent.created_at.desc())
        ).all()
        return [
            {"item_id": row.item_id, "action": row.action, "created_at": row.created_at}
            for row in rows
            if row.item_id
        ]
