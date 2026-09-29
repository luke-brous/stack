from base64 import b64encode
from collections.abc import Generator
from datetime import UTC, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from stack.app.db import create_database_engine, get_db
from stack.app.main import app
from stack.app.models import (
    Base,
    LiftLog,
    ProteinLog,
    SleepLog,
    Vitamin,
    VitaminLog,
    WeightLog,
)


@pytest.fixture
def dashboard_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Generator[tuple[TestClient, sessionmaker[Session]]]:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'dashboard.db'}")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Generator[Session, None, None]:
        with sessions() as session:
            yield session

    monkeypatch.setenv("BASIC_AUTH_USERNAME", "stack-user")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "stack-password")
    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, sessions
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_dashboard_requires_authentication_and_shows_today(
    dashboard_client: tuple[TestClient, sessionmaker[Session]],
) -> None:
    client, sessions = dashboard_client
    assert client.get("/").status_code == 401

    today = datetime.now(ZoneInfo("America/Chicago")).date()
    taken_at = datetime.combine(today, time(12), ZoneInfo("America/Chicago"))
    with sessions() as session:
        vitamin = Vitamin(name="Vitamin D", dose_amount=1000, dose_unit="IU")
        session.add_all(
            [
                vitamin,
                WeightLog(weight_lbs=180.5, log_date=today),
                ProteinLog(hit_goal=False, log_date=today),
                LiftLog(completed=True, log_date=today),
                SleepLog(hours_slept=7.5, log_date=today),
            ]
        )
        session.flush()
        session.add(VitaminLog(vitamin_id=vitamin.id, taken_at=taken_at.astimezone(UTC)))
        session.commit()

    credentials = b64encode(b"stack-user:stack-password").decode()
    response = client.get("/", headers={"Authorization": f"Basic {credentials}"})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    for expected in (
        today.isoformat(),
        "Vitamin D",
        "1 dose logged",
        "180.5 lb today",
        "Goal not met",
        "Completed today",
        "7.5 hours today",
    ):
        assert expected in response.text
    for path in ("/static/styles.css", "/static/dashboard.js", "/docs", "/openapi.json"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers={"Authorization": f"Basic {credentials}"}).status_code == 200
    assert client.get("/static/input.css", headers={"Authorization": f"Basic {credentials}"}).status_code == 404
