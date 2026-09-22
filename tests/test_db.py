from sqlalchemy import text

from stack.app.db import create_database_engine


def test_sqlite_foreign_keys_are_enabled_for_new_connections() -> None:
    engine = create_database_engine("sqlite://")

    with engine.connect() as connection:
        enabled = connection.execute(text("PRAGMA foreign_keys")).scalar_one()

    assert enabled == 1
