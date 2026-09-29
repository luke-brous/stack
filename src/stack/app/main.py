"""FastAPI application entry point."""

from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse

from stack.app.auth import require_basic_auth
from stack.app.routers.dashboard import router as dashboard_router
from stack.app.routers.lift import router as lift_router
from stack.app.routers.protein import router as protein_router
from stack.app.routers.sleep import router as sleep_router
from stack.app.routers.vitamins import router as vitamins_router
from stack.app.routers.weight import router as weight_router

app = FastAPI(title="Stack", docs_url=None, redoc_url=None, openapi_url=None)
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.include_router(dashboard_router)
app.include_router(lift_router)
app.include_router(protein_router)
app.include_router(sleep_router)
app.include_router(vitamins_router)
app.include_router(weight_router)


@app.get("/docs", dependencies=[Depends(require_basic_auth)], include_in_schema=False)
def api_docs() -> HTMLResponse:
    """Serve the interactive API docs behind Basic Auth."""
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Stack API docs")


@app.get("/openapi.json", dependencies=[Depends(require_basic_auth)], include_in_schema=False)
def openapi_schema() -> dict[str, Any]:
    """Serve the OpenAPI schema behind Basic Auth."""
    return app.openapi()


@app.get(
    "/static/{filename}",
    name="static",
    dependencies=[Depends(require_basic_auth)],
    include_in_schema=False,
)
def static_asset(filename: str) -> FileResponse:
    """Serve only the built dashboard assets behind Basic Auth."""
    if filename not in {"styles.css", "dashboard.js"}:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(STATIC_DIR / filename)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Public liveness endpoint without application or database details."""
    return {"status": "ok"}
