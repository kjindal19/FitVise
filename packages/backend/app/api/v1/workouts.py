"""Workout logs + sets (PRD §4.1). Supports offline sync via client-supplied
dates/timestamps; conflict strategy is last-write-wins (PRD §3.1)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.logs import WorkoutLog, WorkoutSetLog
from app.models.user import User
from app.schemas.logs import WorkoutLogCreate, WorkoutLogRead

router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("", response_model=list[WorkoutLogRead])
def list_workouts(
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(WorkoutLog).filter(
        WorkoutLog.user_id == user.id, WorkoutLog.deleted_at.is_(None)
    )
    if start_date:
        q = q.filter(WorkoutLog.date >= start_date)
    if end_date:
        q = q.filter(WorkoutLog.date <= end_date)
    return q.order_by(WorkoutLog.date.desc()).all()


@router.post("", response_model=WorkoutLogRead, status_code=201)
def create_workout(
    payload: WorkoutLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = WorkoutLog(
        user_id=user.id,
        session_id=payload.session_id,
        date=payload.date,
        started_at=payload.started_at,
        completed_at=payload.completed_at,
        notes=payload.notes,
    )
    db.add(log)
    db.flush()
    for s in payload.sets:
        db.add(WorkoutSetLog(workout_log_id=log.id, **s.model_dump()))
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{workout_id}", status_code=204)
def delete_workout(
    workout_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = db.query(WorkoutLog).filter(
        WorkoutLog.id == workout_id, WorkoutLog.user_id == user.id
    ).first()
    if not log:
        raise HTTPException(404, "Not found")
    log.deleted_at = dt.datetime.now(dt.timezone.utc)  # soft delete (PRD §8)
    db.commit()
