"""Event-based notification triggers.

These are thin, well-named wrappers called from REST routers and MCP tools so
the trigger points read clearly:
    triggers.workout_updated(db, user_id, programme_name)
    triggers.checkin_summary_written(db, user_id, week)
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.notifications.service import notify


def workout_updated(db: Session, user_id: str, programme_name: str | None = None) -> None:
    notify(
        db,
        user_id=user_id,
        type="workout_updated",
        title="Your coach updated your programme",
        body=(f"“{programme_name}” was revised." if programme_name else "Your training plan changed."),
        data={"screen": "programme"},
    )


def checkin_summary_written(db: Session, user_id: str, week: int | None = None) -> None:
    notify(
        db,
        user_id=user_id,
        type="checkin_summary",
        title="New check-in summary",
        body=(f"Your week {week} check-in is ready." if week else "Your coach wrote a new check-in."),
        data={"screen": "checkin"},
    )


def weekly_targets_set(db: Session, user_id: str) -> None:
    notify(
        db,
        user_id=user_id,
        type="weekly_targets",
        title="Next week's targets are set",
        body="Your coach set goals for the week ahead.",
        data={"screen": "journal", "tab": "check"},
    )


def checkin_due(db: Session, user_id: str) -> None:
    notify(
        db,
        user_id=user_id,
        type="checkin_ready",
        title="Weekly check-in time",
        body="Re-measure and run your check-in with your coach.",
        data={"screen": "metrics"},
    )


def missed_workout(db: Session, user_id: str, session_label: str) -> None:
    notify(
        db,
        user_id=user_id,
        type="missed_workout",
        title="Missed a session?",
        body=f"You had {session_label} planned today. Log it or reschedule.",
        data={"screen": "programme"},
    )


def daily_reminder(db: Session, user_id: str, message: str) -> None:
    notify(
        db,
        user_id=user_id,
        type="daily_reminder",
        title="FitVise",
        body=message,
        data={"screen": "home"},
    )
