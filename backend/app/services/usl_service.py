import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CatalogMatch, CatalogProduct, UslItem, UslItemMetadata
from app.schemas.usl import CatalogMatchResponse, UslItemCreate, UslItemDetailResponse, UslItemResponse, UslItemStatus, UslItemUpdate
from app.services.intent_queue import enqueue_intent_processing


class UslService:
    def __init__(self, db: Session):
        self.db = db

    def list_items(self, user_id: uuid.UUID, status_filter: str | None = None) -> list[UslItemResponse]:
        query = (
            select(UslItem)
            .where(UslItem.user_id == user_id)
            .order_by(UslItem.created_at.desc())
        )

        if status_filter and status_filter != "all":
            if status_filter not in {s.value for s in UslItemStatus}:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid status filter: {status_filter}",
                )
            query = query.where(UslItem.status == status_filter)

        items = list(self.db.scalars(query).all())
        return [self._to_response(item) for item in items]

    def create_item(self, user_id: uuid.UUID, payload: UslItemCreate) -> UslItemResponse:
        item = UslItem(
            user_id=user_id,
            raw_intent=payload.raw_intent.strip(),
            status=UslItemStatus.PENDING.value,
            match_status="queued",
            priority=payload.priority,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)

        enqueue_intent_processing(item.item_id, user_id, trigger="created")
        return self._to_response(item)

    def get_item_detail(self, user_id: uuid.UUID, item_id: uuid.UUID) -> UslItemDetailResponse:
        item = self._get_owned_item(user_id, item_id)
        response = self._to_response(item)
        metadata = self.db.get(UslItemMetadata, item.item_id)
        return UslItemDetailResponse(**response.model_dump(), metadata=metadata)

    def update_item(self, user_id: uuid.UUID, item_id: uuid.UUID, payload: UslItemUpdate) -> UslItemResponse:
        item = self._get_owned_item(user_id, item_id)
        intent_changed = False

        if payload.raw_intent is not None:
            item.raw_intent = payload.raw_intent.strip()
            intent_changed = True
        if payload.status is not None:
            item.status = payload.status.value
            if payload.status == UslItemStatus.PURCHASED:
                item.purchased_at = datetime.now(timezone.utc)
        if payload.priority is not None:
            item.priority = payload.priority

        if intent_changed:
            item.match_status = "queued"

        self.db.commit()

        if intent_changed:
            enqueue_intent_processing(item.item_id, user_id, trigger="intent_updated")

        return self._to_response(item)

    def delete_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> None:
        item = self._get_owned_item(user_id, item_id)
        self.db.delete(item)
        self.db.commit()

    def _get_owned_item(self, user_id: uuid.UUID, item_id: uuid.UUID) -> UslItem:
        item = self.db.get(UslItem, item_id)
        if not item or item.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="USL item not found")
        return item

    def _to_response(self, item: UslItem) -> UslItemResponse:
        matches = self.db.scalars(
            select(CatalogMatch).where(CatalogMatch.item_id == item.item_id).order_by(CatalogMatch.rank)
        ).all()
        match_responses = []
        for match in matches:
            product = self.db.get(CatalogProduct, match.sku_id)
            match_responses.append(
                CatalogMatchResponse(
                    match_id=match.match_id,
                    sku_id=match.sku_id,
                    product_name=product.product_name if product else None,
                    category=product.category if product else None,
                    price=float(product.price) if product else None,
                    image_url=product.image_url if product else None,
                    match_confidence=match.match_confidence,
                    availability_status=match.availability_status,
                    pincode=match.pincode,
                    rank=match.rank,
                    matched_at=match.matched_at,
                )
            )

        return UslItemResponse(
            item_id=item.item_id,
            raw_intent=item.raw_intent,
            normalized_name=item.normalized_name,
            category=item.category,
            status=item.status,
            match_status=item.match_status,
            priority=item.priority,
            created_at=item.created_at,
            updated_at=item.updated_at,
            purchased_at=item.purchased_at,
            catalog_matches=match_responses,
        )
