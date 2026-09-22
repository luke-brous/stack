# Stack

Stack is a single-user personal health dashboard built with FastAPI,
SQLAlchemy, SQLite, and Jinja2.

## Run Locally

From the repository root, install the locked dependencies:

```bash
uv sync
```

Apply all database migrations:

```bash
uv run alembic upgrade head
```

Start the FastAPI development server with automatic reload:

```bash
uv run uvicorn stack.app.main:app --reload
```

Open these URLs in a browser:

- Health check: <http://127.0.0.1:8000/health>
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The health endpoint should return:

```json
{"status":"ok"}
```

The visual dashboard has not been implemented yet, so there is currently no
browser interface at `/`. Stop the development server with `Ctrl+C`.
