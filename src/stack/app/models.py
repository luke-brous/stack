"""Shared SQLAlchemy declarative base.

Domain models are added here or moved into domain modules as each feature is
implemented. Schema creation is managed by Alembic migrations.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all application ORM models."""
