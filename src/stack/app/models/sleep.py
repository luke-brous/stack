"""Daily sleep-log persistence model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from stack.app.models.base import Base


class SleepLog(Base):
    """Hours slept on a Chicago calendar day."""

    __tablename__ = "sleep_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    hours_slept: Mapped[float] = mapped_column(Float)
    log_date: Mapped[date] = mapped_column(Date, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
