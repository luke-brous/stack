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


def test_lift_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/lift").status_code == 401


def test_lift_create_defaults_to_chicago_today(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    chicago = ZoneInfo("America/Chicago")
    before = datetime.now(chicago).date().isoformat()

    response = client.post("/lift", headers=auth_headers, json={"completed": False})

    after = datetime.now(chicago).date().isoformat()
    assert response.status_code == 201
    assert response.json()["completed"] is False
    assert response.json()["log_date"] in {before, after}
    assert response.json()["created_at"].endswith("Z")


def test_lift_duplicate_update_and_inclusive_ordered_range(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for log_date, completed in (("2026-09-22", False), ("2026-09-20", True)):
        response = client.post(
            "/lift",
            headers=auth_headers,
            json={"completed": completed, "log_date": log_date},
        )
        assert response.status_code == 201

    duplicate = client.post(
        "/lift",
        headers=auth_headers,
        json={"completed": True, "log_date": "2026-09-22"},
    )
    assert duplicate.status_code == 409

    update = client.patch(
        "/lift/2026-09-22", headers=auth_headers, json={"completed": True}
    )
    assert update.status_code == 200
    assert update.json()["completed"] is True

    response = client.get(
        "/lift?start=2026-09-20&end=2026-09-22", headers=auth_headers
    )
    assert response.status_code == 200
    assert [item["log_date"] for item in response.json()] == [
        "2026-09-20",
        "2026-09-22",
    ]
    assert all(item["completed"] is True for item in response.json())


def test_lift_validation_range_and_missing_update(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.patch(
        "/lift/2026-09-22", headers=auth_headers, json={"completed": True}
    )
    assert missing.status_code == 404

    invalid_value = client.post(
        "/lift",
        headers=auth_headers,
        json={"completed": "yes", "log_date": "2026-09-22"},
    )
    assert invalid_value.status_code == 422

    invalid_range = client.get(
        "/lift?start=2026-09-23&end=2026-09-22", headers=auth_headers
    )
    assert invalid_range.status_code == 422

    empty_range = client.get(
        "/lift?start=2026-09-22&end=2026-09-22", headers=auth_headers
    )
    assert empty_range.status_code == 200
    assert empty_range.json() == []
