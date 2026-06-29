"""Diet logs (PRD §4.1)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.logs import DietLog
from app.models.user import User
from app.schemas.logs import DietLogCreate, DietLogRead

router = APIRouter(prefix="/diet", tags=["diet"])


@router.get("", response_model=list[DietLogRead])
def list_diet(
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(DietLog).filter(DietLog.user_id == user.id, DietLog.deleted_at.is_(None))
    if start_date:
        q = q.filter(DietLog.date >= start_date)
    if end_date:
        q = q.filter(DietLog.date <= end_date)
    return q.order_by(DietLog.date.desc(), DietLog.logged_at.desc()).all()


@router.post("", response_model=DietLogRead, status_code=201)
def create_diet(
    payload: DietLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = DietLog(user_id=user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{diet_id}", status_code=204)
def delete_diet(diet_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.query(DietLog).filter(DietLog.id == diet_id, DietLog.user_id == user.id).first()
    if not log:
        raise HTTPException(404, "Not found")
    log.deleted_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
