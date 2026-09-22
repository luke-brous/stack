"""Daily lift-log persistence model."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from stack.app.models.base import Base


class LiftLog(Base):
    """Whether a lift was completed on a Chicago calendar day."""

    __tablename__ = "lift_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    completed: Mapped[bool] = mapped_column(Boolean)
    log_date: Mapped[date] = mapped_column(Date, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
