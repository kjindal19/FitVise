"""Body metrics (PRD §4.1)."""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db, utcnow
from app.models.logs import BodyMetrics
from app.models.user import User
from app.schemas.logs import BodyMetricsCreate, BodyMetricsRead

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=list[BodyMetricsRead])
def list_metrics(
    start_date: dt.date | None = Query(default=None),
    end_date: dt.date | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(BodyMetrics).filter(
        BodyMetrics.user_id == user.id, BodyMetrics.deleted_at.is_(None)
    )
    if start_date:
        q = q.filter(BodyMetrics.logged_at >= dt.datetime.combine(start_date, dt.time.min))
    if end_date:
        q = q.filter(BodyMetrics.logged_at <= dt.datetime.combine(end_date, dt.time.max))
    return q.order_by(BodyMetrics.logged_at.desc()).all()


@router.post("", response_model=BodyMetricsRead, status_code=201)
def create_metrics(
    payload: BodyMetricsCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    data = payload.model_dump()
    data["logged_at"] = data.get("logged_at") or utcnow()
    log = BodyMetrics(user_id=user.id, **data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{metric_id}", status_code=204)
def delete_metrics(
    metric_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    log = db.query(BodyMetrics).filter(
        BodyMetrics.id == metric_id, BodyMetrics.user_id == user.id
    ).first()
    if not log:
        raise HTTPException(404, "Not found")
    log.deleted_at = utcnow()
    db.commit()
