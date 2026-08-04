from fastapi import APIRouter, Depends

from app.config import Settings, get_settings

router = APIRouter(prefix="/flags", tags=["flags"])


@router.get("")
def get_feature_flags(settings: Settings = Depends(get_settings)):
    return {
        "usl_enabled": settings.usl_enabled,
        "usl_checkout_recommendations": settings.usl_checkout_recommendations,
        "experiments_enabled": settings.experiments_enabled,
        "rollout_percentage": settings.rollout_percentage,
    }
