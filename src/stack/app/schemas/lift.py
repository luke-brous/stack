"""Validation schemas for daily lift logs."""

from datetime import date, datetime

from pydantic import BaseModel, StrictBool

from stack.app.schemas.common import UTCResponseModel


class LiftCreate(BaseModel):
    """Payload for recording one day's lift status."""

    completed: StrictBool
    log_date: date | None = None


class LiftUpdate(BaseModel):
    """Payload for changing an existing lift status."""

    completed: StrictBool


class LiftRead(UTCResponseModel):
    """Serialized daily lift log."""

    id: int
    completed: bool
    log_date: date
    created_at: datetime
    updated_at: datetime
