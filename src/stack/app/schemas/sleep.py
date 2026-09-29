"""Validation schemas for daily sleep logs."""

from datetime import date, datetime

from pydantic import BaseModel

from stack.app.schemas.common import UTCResponseModel


class SleepCreate(BaseModel):
    """Payload for recording one day's sleep."""

    hours_slept: float
    log_date: date | None = None


class SleepUpdate(BaseModel):
    """Payload for changing an existing sleep entry."""

    hours_slept: float


class SleepRead(UTCResponseModel):
    """Serialized daily sleep log."""

    id: int
    hours_slept: float
    log_date: date
    created_at: datetime
    updated_at: datetime
