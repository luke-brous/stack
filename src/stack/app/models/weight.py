"""Daily weight-log persistence model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from stack.app.models.base import Base


class WeightLog(Base):
    """A single weight measurement for a Chicago calendar day."""

    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    weight_lbs: Mapped[float] = mapped_column(Float)
    log_date: Mapped[date] = mapped_column(Date, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
