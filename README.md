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
- Dashboard: <http://127.0.0.1:8000/> (HTTP Basic credentials from your environment)
- Interactive API documentation: <http://127.0.0.1:8000/docs>

The health endpoint should return:

```json
{"status":"ok"}
```

Stop the development server with `Ctrl+C`.

## Frontend Styles

The dashboard uses a checked-in Tailwind stylesheet. To regenerate it after
editing templates or `src/stack/app/static/dashboard.js`, download the
[standalone Tailwind CLI](https://tailwindcss.com/docs/installation/tailwind-cli).
For Linux x64, the version used for the checked-in stylesheet is:

```bash
curl -L --fail https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/tailwindcss-linux-x64 -o /tmp/stack-tailwindcss
chmod +x /tmp/stack-tailwindcss
/tmp/stack-tailwindcss -i src/stack/app/static/input.css -o src/stack/app/static/styles.css --minify
```

No Node installation or runtime CDN is required.

## Deploy to Fly.io

The Docker image runs a single FastAPI process with a SQLite database on the
`/data` Fly volume. Install and authenticate `fly`, then choose an app name and
region:

```bash
fly launch --no-deploy
fly volumes create data --size 1
fly secrets set DATABASE_URL=sqlite:////data/stack.db BASIC_AUTH_USERNAME=YOUR_USERNAME BASIC_AUTH_PASSWORD=YOUR_PASSWORD
fly scale count 1
fly deploy
```

Replace the example credentials with private values; do not put them in
`fly.toml` or commit `.env`. Keep the app at one machine while using this SQLite
volume. The startup script runs `alembic upgrade head` against the mounted
database before serving requests. Although `spec.md` suggests a Fly
`release_command`, Fly release-command VMs cannot mount persistent volumes,
so that command would migrate the wrong filesystem. The service forces HTTPS;
only `/health` is public.
