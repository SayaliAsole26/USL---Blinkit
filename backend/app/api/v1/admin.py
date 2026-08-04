import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.db.models import CatalogMatch, UslItem, UslItemMetadata
from app.db.session import get_db
from app.services.pipeline_metrics import get_path_a_metrics, get_path_b_metrics
from app.services.ranker_config import RankerConfigService
from app.services.redis_client import get_redis_client

router = APIRouter(prefix="/admin", tags=["admin"])

DLQ_KEY = "usl:intent:dlq"


def _require_admin(settings: Settings = Depends(get_settings)) -> None:
    if not settings.admin_debug_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")


@router.get("/matches")
def list_match_debug(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: None = Depends(_require_admin),
):
    rows = (
        db.scalars(
            select(UslItem)
            .options(selectinload(UslItem.catalog_matches), selectinload(UslItem.metadata_row))
            .order_by(UslItem.updated_at.desc())
            .limit(limit)
        )
        .all()
    )
    return {
        "items": [
            {
                "item_id": str(item.item_id),
                "raw_intent": item.raw_intent,
                "normalized_name": item.normalized_name,
                "match_status": item.match_status,
                "shortlist_size": item.metadata_row.shortlist_size if item.metadata_row else None,
                "processing_latency_ms": item.metadata_row.processing_latency_ms if item.metadata_row else None,
                "matches": [
                    {
                        "sku_id": match.sku_id,
                        "confidence": match.match_confidence,
                        "availability_status": match.availability_status,
                        "rank": match.rank,
                    }
                    for match in sorted(item.catalog_matches, key=lambda m: m.rank)
                ],
            }
            for item in rows
        ]
    }


@router.get("/pipeline/metrics")
def pipeline_metrics(_: None = Depends(_require_admin)):
    return {"path_a": get_path_a_metrics(), "path_b": get_path_b_metrics()}


@router.get("/ranker/weights")
def ranker_weights(
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_admin),
):
    weights = RankerConfigService(settings).get_weights()
    return {
        "memory_reminder": weights.memory_reminder,
        "replenishment_reminder": weights.replenishment_reminder,
        "weather_context": weights.weather_context,
        "seasonal_context": weights.seasonal_context,
        "event_based": weights.event_based,
        "cross_category_discovery": weights.cross_category_discovery,
        "shopping_completion": weights.shopping_completion,
        "acceptance_boost": weights.acceptance_boost,
        "dismissal_penalty": weights.dismissal_penalty,
    }


@router.get("/pipeline/dlq")
def pipeline_dlq(
    limit: int = 20,
    settings: Settings = Depends(get_settings),
    _: None = Depends(_require_admin),
):
    try:
        client = get_redis_client(settings)
        entries = client.lrange(DLQ_KEY, 0, limit - 1)
        return {"entries": [json.loads(entry) for entry in entries]}
    except Exception as exc:
        return {"entries": [], "error": str(exc)}
