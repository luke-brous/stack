"""Daily protein-goal routes."""

from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import ProteinLog
from stack.app.schemas import ProteinCreate, ProteinRead, ProteinUpdate

APP_TIMEZONE = ZoneInfo("America/Chicago")
DatabaseSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    tags=["protein"],
    dependencies=[Depends(require_basic_auth)],
)


@router.post("/protein", response_model=ProteinRead, status_code=status.HTTP_201_CREATED)
def create_protein_log(payload: ProteinCreate, db: DatabaseSession) -> ProteinLog:
    log = ProteinLog(
        hit_goal=payload.hit_goal,
        log_date=payload.log_date or datetime.now(APP_TIMEZONE).date(),
    )
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A protein entry already exists for this date",
        ) from None
    db.refresh(log)
    return log


@router.patch("/protein/{log_date}", response_model=ProteinRead)
def update_protein_log(
    log_date: date, payload: ProteinUpdate, db: DatabaseSession
) -> ProteinLog:
    log = db.scalar(select(ProteinLog).where(ProteinLog.log_date == log_date))
    if log is None:
        raise HTTPException(status_code=404, detail="Protein entry not found")

    log.hit_goal = payload.hit_goal
    db.commit()
    db.refresh(log)
    return log


@router.get("/protein", response_model=list[ProteinRead])
def list_protein_logs(
    db: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
) -> list[ProteinLog]:
    end_date = end or datetime.now(APP_TIMEZONE).date()
    start_date = start or end_date - timedelta(days=29)
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    query = (
        select(ProteinLog)
        .where(ProteinLog.log_date >= start_date, ProteinLog.log_date <= end_date)
        .order_by(ProteinLog.log_date)
    )
    return list(db.scalars(query))
