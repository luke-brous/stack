"""FastAPI application entry point."""

from fastapi import FastAPI

from stack.app.routers.lift import router as lift_router
from stack.app.routers.protein import router as protein_router
from stack.app.routers.vitamins import router as vitamins_router
from stack.app.routers.weight import router as weight_router

app = FastAPI(title="Stack")
app.include_router(lift_router)
app.include_router(protein_router)
app.include_router(vitamins_router)
app.include_router(weight_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Public liveness endpoint without application or database details."""
    return {"status": "ok"}
