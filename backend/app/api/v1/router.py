from fastapi import APIRouter

from app.api.v1 import admin, flags, integrations, location, recommendations, usl

api_router = APIRouter(prefix="/v1")
api_router.include_router(flags.router)
api_router.include_router(integrations.router)
api_router.include_router(location.router)
api_router.include_router(usl.router)
api_router.include_router(recommendations.router)
api_router.include_router(admin.router)
