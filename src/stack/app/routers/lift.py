"""Daily lift-log routes."""

from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import LiftLog
from stack.app.schemas import LiftCreate, LiftRead, LiftUpdate

APP_TIMEZONE = ZoneInfo("America/Chicago")
DatabaseSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    tags=["lift"],
    dependencies=[Depends(require_basic_auth)],
)


@router.post("/lift", response_model=LiftRead, status_code=status.HTTP_201_CREATED)
def create_lift_log(payload: LiftCreate, db: DatabaseSession) -> LiftLog:
    log = LiftLog(
        completed=payload.completed,
        log_date=payload.log_date or datetime.now(APP_TIMEZONE).date(),
    )
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A lift entry already exists for this date",
        ) from None
    db.refresh(log)
    return log


@router.patch("/lift/{log_date}", response_model=LiftRead)
def update_lift_log(
    log_date: date, payload: LiftUpdate, db: DatabaseSession
) -> LiftLog:
    log = db.scalar(select(LiftLog).where(LiftLog.log_date == log_date))
    if log is None:
        raise HTTPException(status_code=404, detail="Lift entry not found")

    log.completed = payload.completed
    db.commit()
    db.refresh(log)
    return log


@router.get("/lift", response_model=list[LiftRead])
def list_lift_logs(
    db: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
) -> list[LiftLog]:
    end_date = end or datetime.now(APP_TIMEZONE).date()
    start_date = start or end_date - timedelta(days=29)
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    query = (
        select(LiftLog)
        .where(LiftLog.log_date >= start_date, LiftLog.log_date <= end_date)
        .order_by(LiftLog.log_date)
    )
    return list(db.scalars(query))
