"""Open-Meteo weather forecast with Redis cache by pincode + date."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Any

import httpx

from app.config import Settings, get_settings
from app.services.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Common Indian pincodes used in fixtures / dev
PINCODE_COORDS: dict[str, tuple[float, float]] = {
    "560001": (12.9716, 77.5946),
    "560034": (12.9279, 77.6271),
    "110001": (28.6139, 77.2090),
    "400001": (18.9388, 72.8354),
}

RAIN_WEATHER_CODES = {
    51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99
}


class WeatherProvider:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def get_forecast(self, pincode: str, when: date | None = None) -> dict[str, Any]:
        day = when or datetime.now(timezone.utc).date()
        cache_key = f"context:weather:{pincode}:{day.isoformat()}"

        cached = self._read_cache(cache_key)
        if cached:
            return cached

        forecast = self._fetch_forecast(pincode)
        self._write_cache(cache_key, forecast)
        return forecast

    def is_adverse_weather(self, forecast: dict[str, Any]) -> bool:
        return forecast.get("forecast") in {"rain", "heavy_rain"}

    def is_weather_relevant_item(
        self,
        *,
        raw_intent: str = "",
        normalized_name: str = "",
        category: str = "",
        product_name: str = "",
    ) -> bool:
        haystack = " ".join(
            part.lower()
            for part in (raw_intent, normalized_name, category, product_name)
            if part
        )
        keywords = ("umbrella", "raincoat", "rain coat", "rain", "monsoon", "waterproof")
        return any(keyword in haystack for keyword in keywords)

    def _fetch_forecast(self, pincode: str) -> dict[str, Any]:
        lat, lon = PINCODE_COORDS.get(pincode, PINCODE_COORDS["560001"])
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "precipitation_sum,weathercode",
            "forecast_days": 7,
            "timezone": "Asia/Kolkata",
        }

        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            logger.warning("Weather fetch failed for pincode %s: %s", pincode, exc)
            return self._neutral_forecast()

        daily = payload.get("daily", {})
        precipitation = daily.get("precipitation_sum") or []
        weather_codes = daily.get("weathercode") or []

        rain_day_index = None
        max_precip = 0.0
        for idx, (precip, code) in enumerate(zip(precipitation, weather_codes)):
            precip_val = float(precip or 0)
            if precip_val > max_precip:
                max_precip = precip_val
            if rain_day_index is None and (precip_val >= 2.0 or int(code) in RAIN_WEATHER_CODES):
                rain_day_index = idx

        if rain_day_index is not None:
            severity = "heavy" if max_precip >= 10 else "moderate" if max_precip >= 2 else "light"
            forecast_type = "heavy_rain" if max_precip >= 10 else "rain"
            return {
                "forecast": forecast_type,
                "severity": severity,
                "days_ahead": rain_day_index + 1,
                "max_precipitation_mm": round(max_precip, 1),
            }

        return self._neutral_forecast()

    @staticmethod
    def _neutral_forecast() -> dict[str, Any]:
        return {
            "forecast": "clear",
            "severity": "none",
            "days_ahead": None,
            "max_precipitation_mm": 0.0,
        }

    def _read_cache(self, key: str) -> dict[str, Any] | None:
        try:
            client = get_redis_client(self.settings)
            raw = client.get(key)
            if raw:
                return json.loads(raw)
        except Exception:
            pass
        return None

    def _write_cache(self, key: str, payload: dict[str, Any]) -> None:
        try:
            client = get_redis_client(self.settings)
            client.setex(key, self.settings.weather_cache_ttl_seconds, json.dumps(payload))
        except Exception:
            pass
