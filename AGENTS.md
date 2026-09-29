# AGENTS.md

## Project

Stack is a single-user personal health dashboard built with:

* FastAPI
* SQLAlchemy 2.0 declarative ORM
* SQLite
* Alembic
* Pydantic v2
* Jinja2 + Tailwind
* pytest
* uv for dependency/environment management

The product requirements and API behavior are defined in `spec.md`.

Treat `spec.md` as the source of truth for application behavior. Do not silently change requirements or introduce new features that are outside the spec.

## Development Philosophy

This project is also a learning project.

Do not automatically implement large features end-to-end unless explicitly asked.

When helping with a new feature:

1. Explain the relevant concepts and architecture first.
2. Break the work into small implementation steps.
3. Prefer giving guidance or a focused next step before writing code.
4. Let the developer implement reasonable portions when the goal is learning.
5. Review the developer's implementation and explain problems rather than immediately replacing it.
6. If explicitly asked to implement something, implementation is allowed.

Do not hide important framework behavior behind abstractions the developer does not yet understand.

Prefer straightforward, idiomatic Python and FastAPI over clever abstractions.

## Scope Control

Implement only what is required by `spec.md` or explicitly requested.

Do not add:

* multi-user authentication
* JWT authentication
* PostgreSQL support
* repository/service layers unless complexity actually requires them
* generic CRUD frameworks
* generic daily-metric abstractions
* advanced sleep/device integrations
* unnecessary frontend frameworks
* unnecessary dependencies

Prefer the simplest implementation that satisfies the current requirements.

If a requested change conflicts with `spec.md`, point out the conflict before changing behavior.

## Project Structure

Application code lives under:

```text
src/stack/app/
```

Expected organization:

```text
app/
├── main.py
├── db.py
├── auth.py
├── models/
├── schemas/
├── routers/
├── templates/
└── static/
```

Keep responsibilities separated:

* `models/`: SQLAlchemy ORM models
* `schemas/`: Pydantic request/response models
* `routers/`: FastAPI route handlers
* `db.py`: database engine, session factory, database dependency
* `auth.py`: HTTP Basic authentication
* `templates/`: Jinja templates
* `static/`: frontend assets

Do not put ORM models, Pydantic schemas, and route logic into the same file unless explicitly requested for a temporary experiment.

## Python / FastAPI Conventions

Use:

* modern Python type hints
* SQLAlchemy 2.0 APIs
* `Mapped[...]`
* `mapped_column(...)`
* Pydantic v2 syntax
* FastAPI dependency injection for database sessions and authentication

Avoid deprecated SQLAlchemy 1.x patterns.

Keep route handlers reasonably small.

Do not duplicate validation logic that belongs naturally in a Pydantic schema or database constraint.

## Database Rules

SQLite is the v1 database.

Enable SQLite foreign-key enforcement for every connection:

```text
PRAGMA foreign_keys=ON
```

Database constraints must enforce important invariants in addition to application validation.

Daily metric tables must maintain one entry per `log_date`.

Do not use `Base.metadata.create_all()` as the production schema-management mechanism.

Alembic owns production schema changes.

Every schema change must include an Alembic migration.

Do not manually edit the production database schema.

## Time and Date Rules

All timestamps are stored as UTC.

The application timezone is:

```text
America/Chicago
```

Do not represent Central Time using a fixed UTC offset because daylight-saving time changes the offset.

`log_date` represents the user's calendar day in `America/Chicago`.

When serializing UTC timestamps through the API, use ISO-8601 representations.

## SQLite / Fly.io Constraints

Production SQLite data must live on the mounted Fly.io persistent volume, not the ephemeral application filesystem.

Production should use a database path such as:

```text
/data/stack.db
```

The SQLite architecture assumes one application machine in v1.

Do not introduce horizontal scaling while the application uses this SQLite + Fly volume architecture.

## API Behavior

Keep API behavior consistent across the daily resources:

* weight
* protein
* lift
* sleep

Use appropriate HTTP semantics:

* successful GET: `200`
* successful POST: `201`
* successful PATCH: `200`
* successful DELETE: `204`
* missing resource: `404`
* duplicate daily entry: `409`
* invalid request data: `422`
* failed authentication: `401`

Do not silently convert an update into a create operation.

Range-query boundaries are inclusive.

Range-query results should have deterministic ordering.

## Authentication

HTTP Basic authentication is sufficient for v1.

Credentials come from environment variables:

```text
BASIC_AUTH_USERNAME
BASIC_AUTH_PASSWORD
```

Never hard-code credentials.

Never commit real credentials or `.env`.

Use constant-time secret comparison where appropriate.

All production authenticated traffic must use HTTPS.

A public `/health` route may exist but must not expose sensitive application or database information.

## Environment Variables

Development environment variables are documented in `.env.example`.

Expected variables include:

```text
DATABASE_URL
BASIC_AUTH_USERNAME
BASIC_AUTH_PASSWORD
```

Never overwrite or expose a real `.env` file.

When adding a required environment variable, update `.env.example`.

## Dependency Management

Use `uv`.

Prefer commands such as:

```bash
uv sync
uv run pytest
```

Add dependencies through the project dependency configuration rather than ad-hoc global installs.

Do not introduce a new dependency when the standard library or an existing dependency reasonably solves the problem.

## Testing

Tests live under:

```text
tests/
```

Tests must never use the real development or production SQLite database.

Use an isolated temporary or in-memory test database.

Important behavior should include tests for:

* successful CRUD operations where supported
* unique daily-log constraints
* `404` behavior
* invalid request validation
* authentication failures
* vitamin foreign-key/cascade behavior
* date-range boundaries
* timezone-sensitive behavior
* production/test database isolation

When fixing a bug, add or update a test that reproduces the bug when practical.

Run relevant tests after making changes.

Prefer running focused tests during development and the complete test suite before considering a feature complete.

## Migrations

Use Alembic for schema changes.

Typical workflow:

```bash
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

Always inspect autogenerated migrations before considering them complete.

Do not assume an autogenerated migration is correct.

## Code Changes

Prefer small, focused diffs.

Do not refactor unrelated code while implementing a feature.

Do not rename files, modules, API routes, or database columns without a clear reason.

Before modifying several parts of the application, identify which layers actually need to change:

```text
model
→ schema
→ migration
→ route
→ template/frontend
→ tests
```

Not every feature requires changing every layer.

## Error Handling

Do not catch broad exceptions merely to suppress errors.

Translate expected application/database failures into deliberate HTTP responses.

Unexpected programming errors should remain visible during development rather than being silently converted into generic success responses.

## Security

Never:

* commit secrets
* print passwords
* log Basic Auth credentials
* expose `.env` contents
* construct SQL using untrusted string interpolation

Use SQLAlchemy queries rather than manually assembling SQL.

## Before Implementing a Feature

Check:

1. What does `spec.md` require?
2. Which layer actually owns the behavior?
3. Does the change require a database migration?
4. What validation is required?
5. What HTTP behavior should occur?
6. What tests demonstrate that the feature works?

If requirements are genuinely ambiguous and the choice could affect the public API or database schema, identify the ambiguity rather than silently inventing a design.

## Definition of Done

A change is complete when:

* it satisfies the relevant `spec.md` requirement
* the implementation is understandable and reasonably simple
* database changes have migrations
* validation exists where appropriate
* relevant tests exist
* relevant tests pass
* no secrets or production data were introduced
* unrelated functionality was not changed

## Commiting rules

Never commit or push any code without explicit guidance from the user,
instead propose a commit message along with what files should be commited.
Break big changes into several commits to keep a clean git history. 