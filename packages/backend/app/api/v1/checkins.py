"""Check-in records + weekly targets (PRD §4.1). Mostly AI-written via MCP, but
exposed over REST for the read-only UI and manual user targets."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.checkin import CheckInRecord, WeeklyTarget
from app.models.user import User
from app.schemas.checkin import (
    CheckInCreate,
    CheckInRead,
    WeeklyTargetCreate,
    WeeklyTargetRead,
)

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("", response_model=list[CheckInRead])
def list_checkins(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(CheckInRecord)
        .filter(CheckInRecord.user_id == user.id, CheckInRecord.deleted_at.is_(None))
        .order_by(CheckInRecord.date.desc())
        .all()
    )


@router.post("", response_model=CheckInRead, status_code=201)
def create_checkin(
    payload: CheckInCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rec = CheckInRecord(user_id=user.id, **payload.model_dump())
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


@router.get("/targets", response_model=list[WeeklyTargetRead])
def list_targets(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(WeeklyTarget)
        .filter(WeeklyTarget.user_id == user.id, WeeklyTarget.deleted_at.is_(None))
        .order_by(WeeklyTarget.week_start_date.desc())
        .all()
    )


@router.post("/targets", response_model=WeeklyTargetRead, status_code=201)
def create_target(
    payload: WeeklyTargetCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    target = WeeklyTarget(user_id=user.id, **payload.model_dump())
    db.add(target)
    db.commit()
    db.refresh(target)
    return target
