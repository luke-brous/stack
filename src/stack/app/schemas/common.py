"""Validation behavior shared by API response schemas."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UTCResponseModel(BaseModel):
    """Base response model that exposes stored timestamps explicitly as UTC."""

    model_config = ConfigDict(from_attributes=True)

    @field_validator("created_at", "updated_at", "taken_at", mode="before", check_fields=False)
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
