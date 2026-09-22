"""HTTP Basic authentication dependency for protected routes."""

import os
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()


def require_basic_auth(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    """Validate credentials from environment variables and return the username."""
    expected_username = os.getenv("BASIC_AUTH_USERNAME")
    expected_password = os.getenv("BASIC_AUTH_PASSWORD")
    username_matches = secrets.compare_digest(
        credentials.username, expected_username or ""
    )
    password_matches = secrets.compare_digest(
        credentials.password, expected_password or ""
    )
    is_valid = (
        expected_username is not None
        and expected_password is not None
        and username_matches
        and password_matches
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username
