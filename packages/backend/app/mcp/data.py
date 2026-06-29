"""Compact, AI-friendly serialisers for MCP reads (PRD §6.3 context efficiency).

These return plain dicts trimmed to what the coach needs — e.g. workout logs as
exercise × weight × reps, diet logs as descriptions, not full per-row metadata.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy.orm import Session

from app.models.checkin import CheckInRecord, NonScaleVictory
from app.models.logs import (
    BehaviourFlag,
    BodyMetrics,
    DietLog,
    InjuryLog,
    RecoveryLog,
    WorkoutLog,
)
from app.models.programme import Programme, ProgrammeSession
from app.models.user import User


def profile_dict(user: User) -> dict:
    p = user.profile
    return {
        "name": user.name,
        "age": user.age,
        "weight_unit": user.weight_unit,
        "measurement_unit": user.measurement_unit,
        "current_weight": getattr(p, "current_weight", None),
        "height": getattr(p, "height", None),
        "goal_type": getattr(p, "goal_type", None),
        "target_weight": getattr(p, "target_weight", None),
        "diet_type": getattr(p, "diet_type", None),
        "training_modality": getattr(p, "training_modality", None),
        "training_days_per_week": getattr(p, "training_days_per_week", None),
        "injuries_notes": getattr(p, "injuries_notes", None),
        "preferences_notes": getattr(p, "preferences_notes", None),
    }


def current_programme_dict(db: Session, user_id: str, *, summary: bool = False) -> dict | None:
    prog = (
        db.query(Programme)
        .filter(Programme.user_id == user_id, Programme.status == "active")
        .order_by(Programme.created_at.desc())
        .first()
    )
    if prog is None:
        return None
    out = {
        "name": prog.name,
        "current_week": prog.current_week,
        "total_weeks": prog.total_weeks,
        "weeks_remaining": max(prog.total_weeks - prog.current_week, 0),
        "goal_type": prog.goal_type,
        "phase_count": prog.phase_count,
    }
    if not summary:
        sessions = (
            db.query(ProgrammeSession)
            .filter(
                ProgrammeSession.programme_id == prog.id,
                ProgrammeSession.week_number == prog.current_week,
            )
            .all()
        )
        out["this_week_sessions"] = [
            {
                "day_of_week": s.day_of_week,
                "type": s.session_type,
                "exercises": [
                    {
                        "name": e.name,
                        "sets": e.sets,
                        "reps": f"{e.reps_min}-{e.reps_max}" if e.reps_min else None,
                    }
                    for e in s.exercises
                ],
            }
            for s in sessions
        ]
    return out


def session_plan_dict(
    db: Session, user_id: str, *, day_of_week: int | None = None, session_type: str | None = None
) -> dict | None:
    prog = (
        db.query(Programme)
        .filter(Programme.user_id == user_id, Programme.status == "active")
        .order_by(Programme.created_at.desc())
        .first()
    )
    if prog is None:
        return None
    q = db.query(ProgrammeSession).filter(
        ProgrammeSession.programme_id == prog.id,
        ProgrammeSession.week_number == prog.current_week,
    )
    if day_of_week is not None:
        q = q.filter(ProgrammeSession.day_of_week == day_of_week)
    if session_type is not None:
        q = q.filter(ProgrammeSession.session_type == session_type)
    s = q.first()
    if s is None:
        return None
    return {
        "day_of_week": s.day_of_week,
        "type": s.session_type,
        "estimated_duration_minutes": s.estimated_duration_minutes,
        "notes": s.notes,
        "exercises": [
            {
                "name": e.name,
                "sets": e.sets,
                "reps": f"{e.reps_min}-{e.reps_max}" if e.reps_min else None,
                "rest_seconds": e.rest_seconds,
                "form_notes": e.form_notes,
                "substitutes": e.substitutes,
            }
            for e in s.exercises
        ],
    }


def _range(q, model_date, start, end):
    if start:
        q = q.filter(model_date >= start)
    if end:
        q = q.filter(model_date <= end)
    return q


def workout_logs_dicts(db: Session, user_id: str, start=None, end=None) -> list[dict]:
    q = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id, WorkoutLog.deleted_at.is_(None))
    q = _range(q, WorkoutLog.date, start, end)
    logs = q.order_by(WorkoutLog.date.desc()).all()
    return [
        {
            "date": log.date.isoformat(),
            "type": log.session_id and "planned" or "ad_hoc",
            "exercises": [
                {"name": s.exercise_name, "weight": s.weight, "reps": s.reps, "set": s.set_number}
                for s in log.sets
            ],
            "notes": log.notes,
        }
        for log in logs
    ]


def diet_logs_dicts(db: Session, user_id: str, start=None, end=None) -> list[dict]:
    q = db.query(DietLog).filter(DietLog.user_id == user_id, DietLog.deleted_at.is_(None))
    q = _range(q, DietLog.date, start, end)
    rows = q.order_by(DietLog.date.desc()).all()
    return [
        {"date": r.date.isoformat(), "slot": r.meal_slot, "meal": r.description, "flags": r.flags}
        for r in rows
    ]


def body_metrics_dicts(db: Session, user_id: str, start=None, end=None) -> list[dict]:
    q = db.query(BodyMetrics).filter(BodyMetrics.user_id == user_id, BodyMetrics.deleted_at.is_(None))
    if start:
        q = q.filter(BodyMetrics.logged_at >= dt.datetime.combine(start, dt.time.min))
    if end:
        q = q.filter(BodyMetrics.logged_at <= dt.datetime.combine(end, dt.time.max))
    rows = q.order_by(BodyMetrics.logged_at.desc()).all()
    return [
        {
            "at": r.logged_at.isoformat(),
            "weight": r.weight,
            "waist_cm": r.waist_cm,
            "body_fat_pct": r.body_fat_pct,
        }
        for r in rows
    ]


def recovery_logs_dicts(db: Session, user_id: str, start=None, end=None) -> list[dict]:
    q = db.query(RecoveryLog).filter(RecoveryLog.user_id == user_id, RecoveryLog.deleted_at.is_(None))
    q = _range(q, RecoveryLog.date, start, end)
    rows = q.order_by(RecoveryLog.date.desc()).all()
    return [
        {
            "date": r.date.isoformat(),
            "energy": r.energy_level,
            "sleep_hours": r.sleep_hours,
            "soreness": r.soreness_level,
        }
        for r in rows
    ]


def behaviour_flags_dicts(db: Session, user_id: str, start=None, end=None) -> list[dict]:
    q = db.query(BehaviourFlag).filter(
        BehaviourFlag.user_id == user_id, BehaviourFlag.deleted_at.is_(None)
    )
    q = _range(q, BehaviourFlag.date, start, end)
    rows = q.order_by(BehaviourFlag.date.desc()).all()
    return [{"date": r.date.isoformat(), "flag": r.flag_type, "note": r.note} for r in rows]


def injury_logs_dicts(db: Session, user_id: str) -> list[dict]:
    rows = (
        db.query(InjuryLog)
        .filter(InjuryLog.user_id == user_id, InjuryLog.deleted_at.is_(None))
        .order_by(InjuryLog.date.desc())
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "area": r.body_area,
            "type": r.injury_type,
            "severity": r.severity,
            "context": r.context,
        }
        for r in rows
    ]


def checkin_history_dicts(db: Session, user_id: str) -> list[dict]:
    rows = (
        db.query(CheckInRecord)
        .filter(CheckInRecord.user_id == user_id, CheckInRecord.deleted_at.is_(None))
        .order_by(CheckInRecord.date.desc())
        .all()
    )
    return [
        {
            "date": r.date.isoformat(),
            "weight": r.weight_at_checkin,
            "waist": r.waist_at_checkin,
            "sessions": f"{r.sessions_completed}/{r.sessions_planned}",
            "summary": r.ai_summary,
            "targets": r.targets_next_week,
        }
        for r in rows
    ]


def lift_progression_dicts(db: Session, user_id: str, exercise_name: str) -> list[dict]:
    from app.models.logs import WorkoutSetLog

    rows = (
        db.query(WorkoutSetLog, WorkoutLog)
        .join(WorkoutLog, WorkoutSetLog.workout_log_id == WorkoutLog.id)
        .filter(
            WorkoutLog.user_id == user_id,
            WorkoutLog.deleted_at.is_(None),
            WorkoutSetLog.exercise_name.ilike(exercise_name),
        )
        .order_by(WorkoutLog.date.asc())
        .all()
    )
    return [
        {"date": log.date.isoformat(), "weight": s.weight, "reps": s.reps, "pb": s.is_personal_best}
        for s, log in rows
    ]


def nsv_dicts(db: Session, user_id: str) -> list[dict]:
    rows = (
        db.query(NonScaleVictory)
        .filter(NonScaleVictory.user_id == user_id, NonScaleVictory.deleted_at.is_(None))
        .order_by(NonScaleVictory.date.desc())
        .all()
    )
    return [{"date": r.date.isoformat(), "description": r.description} for r in rows]
