#!/bin/sh
set -eu

: "${DATABASE_URL:?Set DATABASE_URL to the mounted SQLite database URL}"
: "${BASIC_AUTH_USERNAME:?Set BASIC_AUTH_USERNAME}"
: "${BASIC_AUTH_PASSWORD:?Set BASIC_AUTH_PASSWORD}"

alembic upgrade head
exec uvicorn stack.app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
