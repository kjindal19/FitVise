"""Recovery / energy logs (PRD §4.1)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db, utcnow
from app.models.logs import RecoveryLog
from app.models.user import User
from app.schemas.logs import RecoveryLogCreate, RecoveryLogRead

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.get("", response_model=list[RecoveryLogRead])
def list_recovery(
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(RecoveryLog).filter(
        RecoveryLog.user_id == user.id, RecoveryLog.deleted_at.is_(None)
    )
    if start_date:
        q = q.filter(RecoveryLog.date >= start_date)
    if end_date:
        q = q.filter(RecoveryLog.date <= end_date)
    return q.order_by(RecoveryLog.date.desc()).all()


@router.post("", response_model=RecoveryLogRead, status_code=201)
def create_recovery(
    payload: RecoveryLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    log = RecoveryLog(user_id=user.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{recovery_id}", status_code=204)
def delete_recovery(
    recovery_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    log = db.query(RecoveryLog).filter(
        RecoveryLog.id == recovery_id, RecoveryLog.user_id == user.id
    ).first()
    if not log:
        raise HTTPException(404, "Not found")
    log.deleted_at = utcnow()
    db.commit()
