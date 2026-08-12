from datetime import datetime
from typing import List
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship


vitamins = Table(
    "vitamins",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("dose_mg", String(100)),
    Column("brand", String(100)),
    Column("created_at", String(100)),
    Column("updated_at", String(100)),
    Column("notes", String()),
)

vitamin_logs = Table(
    "vitamin_logs",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("vitamin_id", Integer, foreign_key="vitamins.id"),
    Column("taken_at", Timestamp),
)

class Base(DeclarativeBase):
    pass


class Vitamin(Base):
    __tablename__ = "vitamins"

    id = mapped_column(Integer, primary_key=True)
    name: Mapped[str]
    dose_mg: Mapped[Optional[str]] = mapped_column(String(64))
    brand: Mapped[Optional[str]] = mapped_column(String(64))
    notes: Mapped[Optional[str]] = mapped_column(String())
    create_date: Mapped[datetime] = mapped_column(insert_default=func.now())
    updated_date: Mapped[datetime] = mapped_column(onupdate=func.now())

class Address(Base):
    __tablename__ = "address"

    id = mapped_column(Integer, primary_key=True)
    user_id = mapped_column(ForeignKey("user.id"))
    email_address: Mapped[str]

    user: Mapped["User"] = relationship(back_populates="addresses")

