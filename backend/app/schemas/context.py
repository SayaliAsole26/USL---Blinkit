from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WeatherContext(BaseModel):
    forecast: str
    severity: str
    days_ahead: int | None = None
    max_precipitation_mm: float | None = None


class UpcomingEvent(BaseModel):
    item_id: UUID
    event_date: date
    days_until: int
    label: str


class CheckoutContextResponse(BaseModel):
    season: str
    season_label: str
    weather: WeatherContext
    cart_categories: list[str] = Field(default_factory=list)
    upcoming_events: list[UpcomingEvent] = Field(default_factory=list)
    festival: str | None = None
