"""Validation schemas for daily protein-goal logs."""

from datetime import date, datetime

from pydantic import BaseModel, StrictBool

from stack.app.schemas.common import UTCResponseModel


class ProteinCreate(BaseModel):
    """Payload for recording one day's protein-goal result."""

    hit_goal: StrictBool
    log_date: date | None = None


class ProteinUpdate(BaseModel):
    """Payload for changing an existing protein-goal result."""

    hit_goal: StrictBool


class ProteinRead(UTCResponseModel):
    """Serialized daily protein-goal log."""

    id: int
    hit_goal: bool
    log_date: date
    created_at: datetime
    updated_at: datetime
