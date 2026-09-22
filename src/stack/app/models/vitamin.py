"""Vitamin definition and dose-log persistence models."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from stack.app.models.base import Base


class Vitamin(Base):
    """A reusable vitamin definition."""

    __tablename__ = "vitamins"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    dose_amount: Mapped[float] = mapped_column(Float)
    dose_unit: Mapped[str] = mapped_column(String(20))
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    logs: Mapped[list["VitaminLog"]] = relationship(
        back_populates="vitamin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class VitaminLog(Base):
    """A record of one vitamin dose being taken."""

    __tablename__ = "vitamin_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    vitamin_id: Mapped[int] = mapped_column(
        ForeignKey("vitamins.id", ondelete="CASCADE")
    )
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    vitamin: Mapped[Vitamin] = relationship(back_populates="logs")
