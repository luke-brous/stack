"""Validation schemas for vitamins and vitamin dose logs."""

from datetime import UTC, datetime
from typing import Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)

from stack.app.schemas.common import UTCResponseModel


class VitaminBase(BaseModel):
    """Fields shared by vitamin create and response payloads."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    dose_amount: float
    dose_unit: str = Field(min_length=1, max_length=20)
    brand: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class VitaminCreate(VitaminBase):
    """Payload for creating a vitamin definition."""


class VitaminUpdate(BaseModel):
    """Payload for partially updating a vitamin definition."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    dose_amount: float | None = None
    dose_unit: str | None = Field(default=None, min_length=1, max_length=20)
    brand: str | None = Field(default=None, max_length=100)
    notes: str | None = None

    @model_validator(mode="after")
    def required_fields_cannot_be_null(self) -> Self:
        for field_name in ("name", "dose_amount", "dose_unit"):
            if field_name in self.model_fields_set and getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self


class VitaminRead(VitaminBase, UTCResponseModel):
    """Serialized vitamin definition."""

    id: int
    created_at: datetime
    updated_at: datetime


class VitaminLogCreate(BaseModel):
    """Payload for recording a vitamin dose."""

    vitamin_id: PositiveInt
    taken_at: AwareDatetime | None = None

    @field_validator("taken_at")
    @classmethod
    def convert_taken_at_to_utc(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value is not None else None


class VitaminLogRead(UTCResponseModel):
    """Serialized vitamin dose log."""

    id: int
    vitamin_id: int
    taken_at: datetime
    created_at: datetime
