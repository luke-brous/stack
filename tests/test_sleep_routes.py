from base64 import b64encode
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from stack.app.db import create_database_engine, get_db
from stack.app.main import app
from stack.app.models import Base


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient]:
    engine = create_database_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Generator[Session, None, None]:
        with test_session() as session:
            yield session

    monkeypatch.setenv("BASIC_AUTH_USERNAME", "stack-user")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "stack-password")
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    credentials = b64encode(b"stack-user:stack-password").decode()
    return {"Authorization": f"Basic {credentials}"}


def test_sleep_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/sleep").status_code == 401


def test_sleep_create_defaults_to_chicago_today(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    chicago = ZoneInfo("America/Chicago")
    before = datetime.now(chicago).date().isoformat()

    response = client.post("/sleep", headers=auth_headers, json={"hours_slept": 7.5})

    after = datetime.now(chicago).date().isoformat()
    assert response.status_code == 201
    assert response.json()["hours_slept"] == 7.5
    assert response.json()["log_date"] in {before, after}
    assert response.json()["created_at"].endswith("Z")


def test_sleep_conflict_update_and_inclusive_ordered_range(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for log_date, hours in (("2026-09-22", 7.5), ("2026-09-20", 8.0)):
        response = client.post(
            "/sleep",
            headers=auth_headers,
            json={"hours_slept": hours, "log_date": log_date},
        )
        assert response.status_code == 201

    duplicate = client.post(
        "/sleep",
        headers=auth_headers,
        json={"hours_slept": 9, "log_date": "2026-09-22"},
    )
    assert duplicate.status_code == 409

    update = client.patch(
        "/sleep/2026-09-22", headers=auth_headers, json={"hours_slept": 6.75}
    )
    assert update.status_code == 200
    assert update.json()["hours_slept"] == 6.75

    response = client.get(
        "/sleep?start=2026-09-20&end=2026-09-22", headers=auth_headers
    )
    assert response.status_code == 200
    assert [item["log_date"] for item in response.json()] == [
        "2026-09-20",
        "2026-09-22",
    ]


def test_sleep_missing_update_and_invalid_inputs(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.patch(
        "/sleep/2026-09-22", headers=auth_headers, json={"hours_slept": 8}
    )
    assert missing.status_code == 404

    invalid_value = client.post(
        "/sleep",
        headers=auth_headers,
        json={"hours_slept": None, "log_date": "2026-09-22"},
    )
    assert invalid_value.status_code == 422

    invalid_range = client.get(
        "/sleep?start=2026-09-23&end=2026-09-22", headers=auth_headers
    )
    assert invalid_range.status_code == 422

    empty_range = client.get(
        "/sleep?start=2026-09-22&end=2026-09-22", headers=auth_headers
    )
    assert empty_range.status_code == 200
    assert empty_range.json() == []
