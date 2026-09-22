"""Validation schemas for daily weight logs."""

from datetime import date, datetime

from pydantic import BaseModel

from stack.app.schemas.common import UTCResponseModel


class WeightCreate(BaseModel):
    """Payload for recording one day's weight."""

    weight_lbs: float
    log_date: date | None = None


class WeightUpdate(BaseModel):
    """Payload for changing an existing weight measurement."""

    weight_lbs: float


class WeightRead(UTCResponseModel):
    """Serialized daily weight log."""

    id: int
    weight_lbs: float
    log_date: date
    created_at: datetime
    updated_at: datetime
