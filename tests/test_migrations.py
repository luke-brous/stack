from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from stack.app.db import create_database_engine


def test_initial_migration_creates_vitamin_tables_and_database_cascade(
    tmp_path: Path, monkeypatch,
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    database_url = f"sqlite:///{tmp_path / 'migration.db'}"
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(config, "head")

    engine = create_database_engine(database_url)
    inspector = inspect(engine)
    assert {"vitamins", "vitamin_logs", "weight_logs"}.issubset(
        inspector.get_table_names()
    )
    weight_unique_columns = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("weight_logs")
    }
    assert ("log_date",) in weight_unique_columns

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO vitamins (name, dose_amount, dose_unit)
                VALUES ('Vitamin D', 1000, 'IU')
                """
            )
        )
        connection.execute(
            text(
                """
                INSERT INTO vitamin_logs (vitamin_id, taken_at)
                VALUES (1, CURRENT_TIMESTAMP)
                """
            )
        )
        connection.execute(text("DELETE FROM vitamins WHERE id = 1"))
        remaining_logs = connection.scalar(text("SELECT COUNT(*) FROM vitamin_logs"))

    assert remaining_logs == 0
