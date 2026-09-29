"""Authenticated HTML dashboard."""

from datetime import UTC, datetime, time, timedelta
from pathlib import Path
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import LiftLog, ProteinLog, SleepLog, Vitamin, VitaminLog, WeightLog

APP_TIMEZONE = ZoneInfo("America/Chicago")
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)
router = APIRouter(dependencies=[Depends(require_basic_auth)])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: DatabaseSession) -> HTMLResponse:
    """Show today's status across all five health domains."""
    today = datetime.now(APP_TIMEZONE).date()
    start_utc = datetime.combine(today, time.min, APP_TIMEZONE).astimezone(UTC)
    end_utc = datetime.combine(
        today + timedelta(days=1), time.min, APP_TIMEZONE
    ).astimezone(UTC)

    vitamin_doses = db.scalar(
        select(func.count(VitaminLog.id)).where(
            VitaminLog.taken_at >= start_utc,
            VitaminLog.taken_at < end_utc,
        )
    )
    response = templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "today": today.isoformat(),
            "vitamins": db.scalars(select(Vitamin).order_by(Vitamin.name)).all(),
            "vitamin_doses": vitamin_doses or 0,
            "weight": db.scalar(select(WeightLog).where(WeightLog.log_date == today)),
            "protein": db.scalar(select(ProteinLog).where(ProteinLog.log_date == today)),
            "lift": db.scalar(select(LiftLog).where(LiftLog.log_date == today)),
            "sleep": db.scalar(select(SleepLog).where(SleepLog.log_date == today)),
        },
    )
    response.headers["Cache-Control"] = "no-store"
    return response
