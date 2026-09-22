"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="Stack")


@app.get("/health")
def health_check() -> dict[str, str]:
    """Public liveness endpoint without application or database details."""
    return {"status": "ok"}
