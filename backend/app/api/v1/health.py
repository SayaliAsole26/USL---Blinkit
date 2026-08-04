from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db.session import check_database_connection, get_db
from app.pipeline.dataset import FixedDatasetService
from app.services.redis_client import check_redis_connection

health_router = APIRouter(tags=["health"])


@health_router.get("/health")
def health():
    return {"status": "ok", "service": "usl-blinkit-api"}


@health_router.get("/ready")
def ready(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    db_ok = check_database_connection()
    redis_ok = check_redis_connection(settings)
    catalog_count = 0
    if db_ok:
        catalog_count = len(FixedDatasetService(db).load_catalog(limit=1_000_000))

    return {
        "status": "ready" if db_ok and redis_ok else "degraded",
        "checks": {
            "database": db_ok,
            "redis": redis_ok,
            "catalog_products_seeded": catalog_count > 0,
            "groq_configured": bool(settings.groq_api_key),
        },
        "catalog_product_count": catalog_count,
    }
