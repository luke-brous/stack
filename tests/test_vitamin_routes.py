from base64 import b64encode
from collections.abc import Generator
from pathlib import Path

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


def test_vitamin_routes_require_authentication(client: TestClient) -> None:
    response = client.get("/vitamins")

    assert response.status_code == 401


def test_vitamin_crud(client: TestClient, auth_headers: dict[str, str]) -> None:
    create_response = client.post(
        "/vitamins",
        headers=auth_headers,
        json={
            "name": "Vitamin D",
            "dose_amount": 1000,
            "dose_unit": "IU",
            "brand": "Example Brand",
        },
    )
    assert create_response.status_code == 201
    vitamin_id = create_response.json()["id"]
    assert create_response.json()["created_at"].endswith("Z")

    list_response = client.get("/vitamins", headers=auth_headers)
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [vitamin_id]

    update_response = client.patch(
        f"/vitamins/{vitamin_id}",
        headers=auth_headers,
        json={"dose_amount": 2000, "brand": None},
    )
    assert update_response.status_code == 200
    assert update_response.json()["dose_amount"] == 2000
    assert update_response.json()["brand"] is None

    delete_response = client.delete(f"/vitamins/{vitamin_id}", headers=auth_headers)
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    missing_response = client.patch(
        f"/vitamins/{vitamin_id}", headers=auth_headers, json={"notes": "missing"}
    )
    assert missing_response.status_code == 404

    missing_delete = client.delete(f"/vitamins/{vitamin_id}", headers=auth_headers)
    assert missing_delete.status_code == 404


def test_vitamin_logs_allow_repeat_doses_and_date_filters(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vitamin = client.post(
        "/vitamins",
        headers=auth_headers,
        json={"name": "Magnesium", "dose_amount": 200, "dose_unit": "mg"},
    ).json()
    payload = {"vitamin_id": vitamin["id"], "taken_at": "2026-09-22T12:00:00Z"}

    first_response = client.post("/vitamin-logs", headers=auth_headers, json=payload)
    second_response = client.post("/vitamin-logs", headers=auth_headers, json=payload)
    assert first_response.status_code == second_response.status_code == 201
    assert first_response.json()["taken_at"].endswith("Z")

    matching = client.get(
        f"/vitamin-logs?start=2026-09-22&end=2026-09-22&vitamin_id={vitamin['id']}",
        headers=auth_headers,
    )
    assert matching.status_code == 200
    assert len(matching.json()) == 2

    outside_range = client.get(
        "/vitamin-logs?start=2026-09-23&end=2026-09-23",
        headers=auth_headers,
    )
    assert outside_range.status_code == 200
    assert outside_range.json() == []


def test_vitamin_log_range_uses_chicago_calendar_boundaries(
    client: TestClient, auth_headers: dict[str, str]
) -> None:
    vitamin = client.post(
        "/vitamins",
        headers=auth_headers,
        json={"name": "Zinc", "dose_amount": 15, "dose_unit": "mg"},
    ).json()
    timestamps = [
        "2026-09-22T04:59:59Z",
        "2026-09-22T05:00:00Z",
        "2026-09-23T04:59:59Z",
        "2026-09-23T05:00:00Z",
    ]
    for timestamp in reversed(timestamps):
        response = client.post(
            "/vitamin-logs",
            headers=auth_headers,
            json={"vitamin_id": vitamin["id"], "taken_at": timestamp},
        )
        assert response.status_code == 201

    response = client.get(
        "/vitamin-logs?start=2026-09-22&end=2026-09-22",
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert [log["taken_at"] for log in response.json()] == timestamps[1:3]


def test_vitamin_log_errors(client: TestClient, auth_headers: dict[str, str]) -> None:
    missing_vitamin = client.post(
        "/vitamin-logs",
        headers=auth_headers,
        json={"vitamin_id": 999, "taken_at": "2026-09-22T12:00:00Z"},
    )
    assert missing_vitamin.status_code == 404

    bad_range = client.get(
        "/vitamin-logs?start=2026-09-23&end=2026-09-22",
        headers=auth_headers,
    )
    assert bad_range.status_code == 422

    invalid_patch = client.patch(
        "/vitamins/999", headers=auth_headers, json={"name": None}
    )
    assert invalid_patch.status_code == 422
