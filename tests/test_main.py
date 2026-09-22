from fastapi.testclient import TestClient

from stack.app.main import app


def test_health_check_is_public_and_minimal() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
