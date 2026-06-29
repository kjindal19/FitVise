"""Data export (PRD §8) — full-fidelity JSON and per-entity CSV (zip)."""
from __future__ import annotations

import csv
import io
import json
import zipfile

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.checkin import CheckInRecord, NonScaleVictory, WeeklyTarget
from app.models.logs import (
    BehaviourFlag,
    BodyMetrics,
    DietLog,
    InjuryLog,
    RecoveryLog,
    WorkoutLog,
    WorkoutSetLog,
)
from app.models.programme import Programme
from app.models.user import User, UserProfile

router = APIRouter(prefix="/export", tags=["export"])

# Entity -> model for the generic export sweep (all scoped by user_id).
_ENTITIES = {
    "profile": UserProfile,
    "programmes": Programme,
    "workout_logs": WorkoutLog,
    "diet_logs": DietLog,
    "body_metrics": BodyMetrics,
    "recovery_logs": RecoveryLog,
    "behaviour_flags": BehaviourFlag,
    "injury_logs": InjuryLog,
    "checkin_records": CheckInRecord,
    "non_scale_victories": NonScaleVictory,
    "weekly_targets": WeeklyTarget,
}


def _row_to_dict(obj) -> dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _collect(db: Session, user: User) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"user": [_row_to_dict(user)]}
    for name, model in _ENTITIES.items():
        rows = db.query(model).filter(model.user_id == user.id).all()
        out[name] = [_row_to_dict(r) for r in rows]
    # workout sets belong to the user's workout logs
    log_ids = [r["id"] for r in out["workout_logs"]]
    sets = (
        db.query(WorkoutSetLog).filter(WorkoutSetLog.workout_log_id.in_(log_ids)).all()
        if log_ids
        else []
    )
    out["workout_set_logs"] = [_row_to_dict(s) for s in sets]
    return out


@router.get("/json")
def export_json(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = _collect(db, user)
    payload = json.loads(json.dumps(data, default=str))  # serialise dates/uuids
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": "attachment; filename=fitvise-export.json"},
    )


@router.get("/csv")
def export_csv(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = _collect(db, user)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, rows in data.items():
            if not rows:
                continue
            sbuf = io.StringIO()
            writer = csv.DictWriter(sbuf, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            for r in rows:
                writer.writerow({k: ("" if v is None else v) for k, v in r.items()})
            zf.writestr(f"{name}.csv", sbuf.getvalue())
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=fitvise-export-csv.zip"},
    )
