from datetime import datetime

from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    city: str = Field(..., min_length=1, max_length=128)
    state: str = Field(..., min_length=1, max_length=128)
    pincode: str = Field(..., pattern=r"^\d{6}$")


class LocationResponse(BaseModel):
    city: str
    state: str
    pincode: str
    updated_at: datetime

    model_config = {"from_attributes": True}
