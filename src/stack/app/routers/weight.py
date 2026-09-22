"""Daily weight-log routes."""

from datetime import date, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import WeightLog
from stack.app.schemas import WeightCreate, WeightRead, WeightUpdate

APP_TIMEZONE = ZoneInfo("America/Chicago")
DatabaseSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    tags=["weight"],
    dependencies=[Depends(require_basic_auth)],
)


@router.post("/weight", response_model=WeightRead, status_code=status.HTTP_201_CREATED)
def create_weight_log(payload: WeightCreate, db: DatabaseSession) -> WeightLog:
    log = WeightLog(
        weight_lbs=payload.weight_lbs,
        log_date=payload.log_date or datetime.now(APP_TIMEZONE).date(),
    )
    db.add(log)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A weight entry already exists for this date",
        ) from None
    db.refresh(log)
    return log


@router.patch("/weight/{log_date}", response_model=WeightRead)
def update_weight_log(
    log_date: date, payload: WeightUpdate, db: DatabaseSession
) -> WeightLog:
    log = db.scalar(select(WeightLog).where(WeightLog.log_date == log_date))
    if log is None:
        raise HTTPException(status_code=404, detail="Weight entry not found")

    log.weight_lbs = payload.weight_lbs
    db.commit()
    db.refresh(log)
    return log


@router.get("/weight", response_model=list[WeightRead])
def list_weight_logs(
    db: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
) -> list[WeightLog]:
    end_date = end or datetime.now(APP_TIMEZONE).date()
    start_date = start or end_date - timedelta(days=29)
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    query = (
        select(WeightLog)
        .where(WeightLog.log_date >= start_date, WeightLog.log_date <= end_date)
        .order_by(WeightLog.log_date)
    )
    return list(db.scalars(query))
