"""Seed catalog from static dataset fixtures into PostgreSQL and Meilisearch."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import CatalogProduct, ProductAvailability
from app.db.session import SessionLocal, engine
from app.db.models import Base
from app.services.embedding_service import EmbeddingService


def seed_postgres(db: Session, fixtures: list[dict]) -> tuple[int, int]:
    product_count = 0
    availability_count = 0

    for item in fixtures:
        existing = db.query(CatalogProduct).filter(CatalogProduct.sku_id == item["sku_id"]).first()
        if not existing:
            db.add(
                CatalogProduct(
                    sku_id=item["sku_id"],
                    product_name=item["product_name"],
                    category=item["category"],
                    price=item["price"],
                    image_url=item.get("image_url"),
                    attributes=item.get("attributes"),
                )
            )
            product_count += 1

        for pincode in item.get("pincodes", []):
            avail = (
                db.query(ProductAvailability)
                .filter(
                    ProductAvailability.sku_id == item["sku_id"],
                    ProductAvailability.pincode == pincode,
                )
                .first()
            )
            if not avail:
                db.add(
                    ProductAvailability(
                        sku_id=item["sku_id"],
                        pincode=pincode,
                        availability_status="available",
                        quantity=10,
                    )
                )
                availability_count += 1

    db.commit()
    return product_count, availability_count


def seed_meilisearch(fixtures: list[dict]) -> int:
    settings = get_settings()
    try:
        import meilisearch
    except ImportError:
        print("meilisearch package not installed; skipping Meilisearch index")
        return 0

    client = meilisearch.Client(settings.meili_url, settings.meili_master_key)
    index = client.index("catalog_products")
    try:
        client.create_index("catalog_products", {"primaryKey": "sku_id"})
    except Exception:
        pass

    documents = [
        {
            "sku_id": item["sku_id"],
            "product_name": item["product_name"],
            "category": item["category"],
            "price": item["price"],
        }
        for item in fixtures
    ]
    index.add_documents(documents)
    return len(documents)


def main() -> None:
    fixtures_path = ROOT / "data" / "catalog-fixtures.json"
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        products, availability = seed_postgres(db, fixtures)
        meili_count = seed_meilisearch(fixtures)
        settings = get_settings()
        embedding_count = 0
        if settings.embeddings_enabled and "postgresql" in settings.database_url:
            embedding_count = EmbeddingService(settings).embed_all_catalog(db)
        print(
            f"Seeded {products} new products, {availability} availability rows, "
            f"{meili_count} Meilisearch docs, {embedding_count} embeddings"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
