"""Journal endpoints: behaviour flags, injury log, non-scale victories."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db, utcnow
from app.models.checkin import NonScaleVictory
from app.models.logs import BehaviourFlag, InjuryLog
from app.models.user import User
from app.schemas.checkin import NSVCreate, NSVRead
from app.schemas.logs import (
    BehaviourFlagCreate,
    BehaviourFlagRead,
    InjuryLogCreate,
    InjuryLogRead,
)

router = APIRouter(prefix="/journal", tags=["journal"])


# ---- Behaviour flags ----------------------------------------------
@router.get("/flags", response_model=list[BehaviourFlagRead])
def list_flags(
    start_date: dt.date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(BehaviourFlag).filter(
        BehaviourFlag.user_id == user.id, BehaviourFlag.deleted_at.is_(None)
    )
    if start_date:
        q = q.filter(BehaviourFlag.date >= start_date)
    return q.order_by(BehaviourFlag.date.desc()).all()


@router.post("/flags", response_model=BehaviourFlagRead, status_code=201)
def create_flag(
    payload: BehaviourFlagCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    flag = BehaviourFlag(user_id=user.id, **payload.model_dump())
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


# ---- Injury -------------------------------------------------------
@router.get("/injuries", response_model=list[InjuryLogRead])
def list_injuries(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(InjuryLog)
        .filter(InjuryLog.user_id == user.id, InjuryLog.deleted_at.is_(None))
        .order_by(InjuryLog.date.desc())
        .all()
    )


@router.post("/injuries", response_model=InjuryLogRead, status_code=201)
def create_injury(
    payload: InjuryLogCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    injury = InjuryLog(user_id=user.id, **payload.model_dump())
    db.add(injury)
    db.commit()
    db.refresh(injury)
    return injury


# ---- Non-scale victories ------------------------------------------
@router.get("/victories", response_model=list[NSVRead])
def list_victories(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(NonScaleVictory)
        .filter(NonScaleVictory.user_id == user.id, NonScaleVictory.deleted_at.is_(None))
        .order_by(NonScaleVictory.date.desc())
        .all()
    )


@router.post("/victories", response_model=NSVRead, status_code=201)
def create_victory(
    payload: NSVCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    nsv = NonScaleVictory(user_id=user.id, **payload.model_dump())
    db.add(nsv)
    db.commit()
    db.refresh(nsv)
    return nsv
