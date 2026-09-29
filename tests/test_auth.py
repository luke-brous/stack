import pytest
from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from stack.app.auth import require_basic_auth


def test_require_basic_auth_accepts_matching_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASIC_AUTH_USERNAME", "stack-user")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "stack-password")

    username = require_basic_auth(
        HTTPBasicCredentials(username="stack-user", password="stack-password")
    )

    assert username == "stack-user"


def test_require_basic_auth_rejects_invalid_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BASIC_AUTH_USERNAME", "stack-user")
    monkeypatch.setenv("BASIC_AUTH_PASSWORD", "stack-password")

    with pytest.raises(HTTPException) as error:
        require_basic_auth(HTTPBasicCredentials(username="stack-user", password="wrong"))

    assert error.value.status_code == 401
    assert error.value.headers == {"WWW-Authenticate": "Basic"}
