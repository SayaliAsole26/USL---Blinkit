"""Phase 7 — notify when unavailable USL matches become available."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AvailabilityWatch, CatalogMatch, UslItem
from app.integrations.mock_blinkit import MockInventoryAdapter


class AvailabilityWatchService:
    def __init__(self, db: Session):
        self.db = db
        self.inventory = MockInventoryAdapter(db)

    def subscribe(self, user_id: uuid.UUID, item_id: uuid.UUID, pincode: str) -> AvailabilityWatch:
        item = self.db.get(UslItem, item_id)
        if not item or item.user_id != user_id:
            raise ValueError("USL item not found")

        match = self.db.scalars(
            select(CatalogMatch).where(CatalogMatch.item_id == item_id).order_by(CatalogMatch.rank).limit(1)
        ).first()
        if not match:
            raise ValueError("No catalog match to watch")

        existing = self.db.scalars(
            select(AvailabilityWatch).where(
                AvailabilityWatch.user_id == user_id,
                AvailabilityWatch.item_id == item_id,
                AvailabilityWatch.active.is_(True),
            )
        ).first()
        if existing:
            return existing

        watch = AvailabilityWatch(
            watch_id=uuid.uuid4(),
            user_id=user_id,
            item_id=item_id,
            sku_id=match.sku_id,
            pincode=pincode,
            active=True,
        )
        self.db.add(watch)
        self.db.commit()
        self.db.refresh(watch)
        return watch

    def list_watches(self, user_id: uuid.UUID) -> list[AvailabilityWatch]:
        return list(
            self.db.scalars(
                select(AvailabilityWatch).where(
                    AvailabilityWatch.user_id == user_id,
                    AvailabilityWatch.active.is_(True),
                )
            ).all()
        )

    def check_and_notify(self, user_id: uuid.UUID) -> list[dict]:
        """Return watches that became available (demo: immediate check)."""
        notifications: list[dict] = []
        watches = self.list_watches(user_id)
        for watch in watches:
            status = self.inventory.check_availability(watch.sku_id, watch.pincode)
            if status == "available":
                watch.notified_at = datetime.now(timezone.utc)
                watch.active = False
                notifications.append(
                    {
                        "watch_id": str(watch.watch_id),
                        "item_id": str(watch.item_id),
                        "sku_id": watch.sku_id,
                        "message": f"Good news — an item on your list is now available at {watch.pincode}.",
                    }
                )
        if notifications:
            self.db.commit()
        return notifications
