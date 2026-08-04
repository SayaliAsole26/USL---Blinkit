from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import health_router
from app.api.v1.router import api_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Universal Shopping List (USL) — Blinkit checkout recommendation engine",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

cors_middleware_kwargs: dict = {
    "allow_origins": settings.cors_origin_list,
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}
if settings.cors_allow_vercel_previews:
    cors_middleware_kwargs["allow_origin_regex"] = settings.cors_origin_regex

app.add_middleware(CORSMiddleware, **cors_middleware_kwargs)

app.include_router(health_router)
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "phase": "3",
        "framework": "Dataset → Filter → LLM → Output",
        "docs": None if settings.is_production else "/docs",
        "health": "/health",
        "ready": "/ready",
    }
