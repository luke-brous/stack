"""Database engine and FastAPI session dependency."""

import os
from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

DEFAULT_DATABASE_URL = "sqlite:///./stack.db"


def create_database_engine(database_url: str | URL) -> Engine:
    """Create an engine with SQLite foreign-key enforcement enabled."""
    engine = create_engine(database_url, connect_args={"check_same_thread": False})

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()  # type: ignore[union-attr]
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_database_engine(os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL))
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    """Yield one database session per request and close it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

