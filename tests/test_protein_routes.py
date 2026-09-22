from base64 import b64encode
from collections.abc import Generator
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from stack.app.db import create_database_engine, get_db
from stack.app.main import app
from stack.app.models import Base
from stack.app.routers import protein as protein_router


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


def test_protein_routes_require_authentication(client: TestClient) -> None:
    assert client.get("/protein").status_code == 401


def test_protein_create_defaults_to_chicago_today(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    chicago = ZoneInfo("America/Chicago")
    before = datetime.now(chicago).date().isoformat()

    response = client.post("/protein", headers=auth_headers, json={"hit_goal": False})

    after = datetime.now(chicago).date().isoformat()
    assert response.status_code == 201
    assert response.json()["hit_goal"] is False
    assert response.json()["log_date"] in {before, after}
    assert response.json()["created_at"].endswith("Z")


def test_protein_duplicate_update_and_inclusive_ordered_range(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    for log_date, hit_goal in (("2026-09-22", False), ("2026-09-20", True)):
        response = client.post(
            "/protein",
            headers=auth_headers,
            json={"hit_goal": hit_goal, "log_date": log_date},
        )
        assert response.status_code == 201

    duplicate = client.post(
        "/protein",
        headers=auth_headers,
        json={"hit_goal": True, "log_date": "2026-09-22"},
    )
    assert duplicate.status_code == 409

    update = client.patch(
        "/protein/2026-09-22", headers=auth_headers, json={"hit_goal": True}
    )
    assert update.status_code == 200
    assert update.json()["hit_goal"] is True

    response = client.get(
        "/protein?start=2026-09-20&end=2026-09-22", headers=auth_headers
    )
    assert response.status_code == 200
    assert [item["log_date"] for item in response.json()] == [
        "2026-09-20",
        "2026-09-22",
    ]
    assert all(item["hit_goal"] is True for item in response.json())


def test_protein_default_range_covers_trailing_30_days(
    client: TestClient,
    auth_headers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz: ZoneInfo | None = None) -> datetime:
            fixed = datetime(2026, 9, 22, 12, tzinfo=ZoneInfo("America/Chicago"))
            return fixed if tz is None else fixed.astimezone(tz)

    monkeypatch.setattr(protein_router, "datetime", FixedDateTime)
    today = date(2026, 9, 22)
    included_date = today - timedelta(days=29)
    excluded_date = today - timedelta(days=30)
    for log_date in (included_date, excluded_date):
        response = client.post(
            "/protein",
            headers=auth_headers,
            json={"hit_goal": False, "log_date": log_date.isoformat()},
        )
        assert response.status_code == 201

    response = client.get("/protein", headers=auth_headers)
    assert response.status_code == 200
    assert [item["log_date"] for item in response.json()] == [
        included_date.isoformat()
    ]


def test_protein_validation_range_and_missing_update(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    missing = client.patch(
        "/protein/2026-09-22", headers=auth_headers, json={"hit_goal": True}
    )
    assert missing.status_code == 404

    invalid_value = client.post(
        "/protein",
        headers=auth_headers,
        json={"hit_goal": "yes", "log_date": "2026-09-22"},
    )
    assert invalid_value.status_code == 422

    invalid_patch = client.patch(
        "/protein/2026-09-22", headers=auth_headers, json={"hit_goal": None}
    )
    assert invalid_patch.status_code == 422

    invalid_range = client.get(
        "/protein?start=2026-09-23&end=2026-09-22", headers=auth_headers
    )
    assert invalid_range.status_code == 422

    empty_range = client.get(
        "/protein?start=2026-09-22&end=2026-09-22", headers=auth_headers
    )
    assert empty_range.status_code == 200
    assert empty_range.json() == []
