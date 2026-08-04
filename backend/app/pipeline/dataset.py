"""Fixed Dataset stage — catalog, USL memory, history."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.db.models import CatalogProduct, UslItem
from app.integrations.mock_blinkit import MockCatalogAdapter


@dataclass
class DatasetBundle:
    catalog_products: list[dict]
    usl_items: list[dict]


class FixedDatasetService:
    def __init__(self, db: Session):
        self.db = db
        self.catalog = MockCatalogAdapter(db)

    def load_catalog(self, limit: int = 100) -> list[dict]:
        rows = self.db.query(CatalogProduct).limit(limit).all()
        return [
            {
                "sku_id": r.sku_id,
                "product_name": r.product_name,
                "category": r.category,
                "price": float(r.price),
            }
            for r in rows
        ]

    def load_usl_for_user(self, user_id: str) -> list[dict]:
        rows = self.db.query(UslItem).filter(UslItem.user_id == user_id).all()
        return [{"item_id": str(r.item_id), "raw_intent": r.raw_intent, "status": r.status} for r in rows]

    def search_catalog(self, query: str, limit: int = 20) -> list[dict]:
        products = self.catalog.search(query, limit=limit)
        return [p.__dict__ for p in products]
