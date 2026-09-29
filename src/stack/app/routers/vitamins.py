"""Vitamin definition and dose-log routes."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from stack.app.auth import require_basic_auth
from stack.app.db import get_db
from stack.app.models import Vitamin, VitaminLog
from stack.app.schemas import (
    VitaminCreate,
    VitaminLogCreate,
    VitaminLogRead,
    VitaminRead,
    VitaminUpdate,
)

APP_TIMEZONE = ZoneInfo("America/Chicago")
DatabaseSession = Annotated[Session, Depends(get_db)]

router = APIRouter(
    tags=["vitamins"],
    dependencies=[Depends(require_basic_auth)],
)


def _get_vitamin_or_404(vitamin_id: int, db: Session) -> Vitamin:
    vitamin = db.get(Vitamin, vitamin_id)
    if vitamin is None:
        raise HTTPException(status_code=404, detail="Vitamin not found")
    return vitamin


@router.post("/vitamins", response_model=VitaminRead, status_code=status.HTTP_201_CREATED)
def create_vitamin(payload: VitaminCreate, db: DatabaseSession) -> Vitamin:
    vitamin = Vitamin(**payload.model_dump())
    db.add(vitamin)
    db.commit()
    db.refresh(vitamin)
    return vitamin


@router.get("/vitamins", response_model=list[VitaminRead])
def list_vitamins(db: DatabaseSession) -> list[Vitamin]:
    return list(db.scalars(select(Vitamin).order_by(Vitamin.id)))


@router.patch("/vitamins/{vitamin_id}", response_model=VitaminRead)
def update_vitamin(
    vitamin_id: int, payload: VitaminUpdate, db: DatabaseSession
) -> Vitamin:
    vitamin = _get_vitamin_or_404(vitamin_id, db)
    for field_name, value in payload.model_dump(exclude_unset=True).items():
        setattr(vitamin, field_name, value)
    db.commit()
    db.refresh(vitamin)
    return vitamin


@router.delete("/vitamins/{vitamin_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vitamin(vitamin_id: int, db: DatabaseSession) -> Response:
    vitamin = _get_vitamin_or_404(vitamin_id, db)
    db.delete(vitamin)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/vitamin-logs",
    response_model=VitaminLogRead,
    status_code=status.HTTP_201_CREATED,
)
def create_vitamin_log(payload: VitaminLogCreate, db: DatabaseSession) -> VitaminLog:
    _get_vitamin_or_404(payload.vitamin_id, db)
    log = VitaminLog(
        vitamin_id=payload.vitamin_id,
        taken_at=payload.taken_at or datetime.now(UTC),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/vitamin-logs", response_model=list[VitaminLogRead])
def list_vitamin_logs(
    db: DatabaseSession,
    start: date | None = None,
    end: date | None = None,
    vitamin_id: Annotated[int | None, Query(gt=0)] = None,
) -> list[VitaminLog]:
    end_date = end or datetime.now(APP_TIMEZONE).date()
    start_date = start or end_date - timedelta(days=29)
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="start must be on or before end")

    start_utc = datetime.combine(start_date, time.min, APP_TIMEZONE).astimezone(UTC)
    end_utc = datetime.combine(
        end_date + timedelta(days=1), time.min, APP_TIMEZONE
    ).astimezone(UTC)

    query = (
        select(VitaminLog)
        .where(VitaminLog.taken_at >= start_utc, VitaminLog.taken_at < end_utc)
        .order_by(VitaminLog.taken_at, VitaminLog.id)
    )
    if vitamin_id is not None:
        query = query.where(VitaminLog.vitamin_id == vitamin_id)

    return list(db.scalars(query))
