from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Railway/Heroku expose postgres://; SQLAlchemy 2 requires postgresql://."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "USL Blinkit API"
    app_version: str = "0.6.0"
    environment: str = "development"

    database_url: str = "postgresql://usl:usl@localhost:5432/usl"
    redis_url: str = "redis://localhost:6379"
    meili_url: str = "http://localhost:7700"
    meili_master_key: str = "masterKey"
    meili_index: str = "catalog_products"

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "mixtral-8x7b-32768"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embeddings_enabled: bool = True

    match_confidence_threshold: float = 0.45
    max_catalog_shortlist: int = 80
    max_catalog_matches: int = 3

    intent_worker_sync: bool = False
    admin_debug_enabled: bool = True
    meili_enabled: bool = True

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allow_vercel_previews: bool = True
    cors_origin_regex: str = r"https://.*\.vercel\.app"
    jwt_secret: str = "dev-secret-change-in-production"

    usl_enabled: bool = True
    usl_checkout_recommendations: bool = True

    dismiss_cooldown_days: int = 7
    max_checkout_recommendations: int = 5
    max_checkout_shortlist: int = 80
    checkout_cache_ttl_seconds: int = 300
    context_cache_ttl_seconds: int = 300
    weather_cache_ttl_seconds: int = 86400
    event_window_days: int = 14

    replenishment_due_threshold: float = 1.0
    frequency_cap_days: int = 7
    ranker_weights_json: str = ""

    run_migrations_on_startup: bool = False
    seed_catalog_on_startup: bool = False

    @field_validator("database_url")
    @classmethod
    def _normalize_database_url(cls, value: str) -> str:
        if not value or not str(value).strip():
            # Allow API boot for /health when Railway DATABASE_URL is missing (misconfigured).
            return "postgresql://127.0.0.1:5432/usl"
        return normalize_database_url(value)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
