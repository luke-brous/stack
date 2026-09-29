"""Daily sleep-log routes."""

from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import SleepLog
from stack.app.schemas import SleepCreate, SleepRead, SleepUpdate

APP_TIMEZONE = ZoneInfo("America/Chicago")
DatabaseSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    tags=["sleep"],
    dependencies=[Depends(require_basic_auth)],
)


@router.post("/sleep", response_model=SleepRead, status_code=status.HTTP_201_CREATED)
def create_sleep_log(payload: SleepCreate, db: DatabaseSession) -> SleepLog:
    log = SleepLog(
        hours_slept=payload.hours_slept,
        log_date=payload.log_date or datetime.now(APP_TIMEZONE).date(),
    )
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A sleep entry already exists for this date",
        ) from None
    db.refresh(log)
    return log


@router.patch("/sleep/{log_date}", response_model=SleepRead)
def update_sleep_log(
    log_date: date, payload: SleepUpdate, db: DatabaseSession
) -> SleepLog:
    log = db.scalar(select(SleepLog).where(SleepLog.log_date == log_date))
    if log is None:
        raise HTTPException(status_code=404, detail="Sleep entry not found")

    log.hours_slept = payload.hours_slept
    db.commit()
    db.refresh(log)
    return log


@router.get("/sleep", response_model=list[SleepRead])
def list_sleep_logs(
    db: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
) -> list[SleepLog]:
    end_date = end or datetime.now(APP_TIMEZONE).date()
    start_date = start or end_date - timedelta(days=29)
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    query = (
        select(SleepLog)
        .where(SleepLog.log_date >= start_date, SleepLog.log_date <= end_date)
        .order_by(SleepLog.log_date)
    )
    return list(db.scalars(query))
