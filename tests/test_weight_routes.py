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
    database_url = f"sqlite:///{tmp_path / 'api.db'}"
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_get_db() -> Generator[Session, None, None]:
        with test_session() as session:
            yield session

    monkeypatch.setenv("BASIC_AUTH_USERNAME", "stack-user")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "stack-password")
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def auth_headers() -> dict[str, str]:
    credentials = b64encode(b"stack-user:stack-password").decode()
    return {"Authorization": f"Basic {credentials}"}


def test_weight_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/weight").status_code == 401


def test_create_weight_defaults_to_chicago_today(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    chicago = ZoneInfo("America/Chicago")
    date_before_request = datetime.now(chicago).date().isoformat()

    response = client.post(
        "/weight", headers=auth_headers, json={"weight_lbs": 180.5}
    )

    date_after_request = datetime.now(chicago).date().isoformat()
    assert response.status_code == 201
    assert response.json()["log_date"] in {date_before_request, date_after_request}
    assert response.json()["created_at"].endswith("Z")


def test_weight_create_conflict_update_and_ordered_range(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for log_date, weight in (("2026-09-22", 180.5), ("2026-09-20", 181.5)):
        response = client.post(
            "/weight",
            headers=auth_headers,
            json={"weight_lbs": weight, "log_date": log_date},
        )
        assert response.status_code == 201

    duplicate = client.post(
        "/weight",
        headers=auth_headers,
        json={"weight_lbs": 179, "log_date": "2026-09-22"},
    )
    assert duplicate.status_code == 409

    update = client.patch(
        "/weight/2026-09-22",
        headers=auth_headers,
        json={"weight_lbs": 179.75},
    )
    assert update.status_code == 200
    assert update.json()["weight_lbs"] == 179.75

    response = client.get(
        "/weight?start=2026-09-19&end=2026-09-22", headers=auth_headers
    )
    assert response.status_code == 200
    assert [item["log_date"] for item in response.json()] == [
        "2026-09-20",
        "2026-09-22",
    ]


def test_weight_range_and_missing_update_errors(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.patch(
        "/weight/2026-09-22", headers=auth_headers, json={"weight_lbs": 180}
    )
    assert missing.status_code == 404

    empty_range = client.get(
        "/weight?start=2026-09-22&end=2026-09-22", headers=auth_headers
    )
    assert empty_range.status_code == 200
    assert empty_range.json() == []

    bad_range = client.get(
        "/weight?start=2026-09-23&end=2026-09-22", headers=auth_headers
    )
    assert bad_range.status_code == 422
