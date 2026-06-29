"""Background scheduler for time-based notifications (APScheduler).

Started from the FastAPI lifespan. Two jobs:
- ``daily_reminders`` (every minute): for each user whose local HH:MM matches
  their reminder time, fire a "log your day" nudge.
- ``missed_workout_sweep`` (hourly): flag planned sessions for the current
  weekday with no workout log yet.

Kept deliberately simple for the scaffold; de-duplication beyond same-minute
matching is a follow-up (track last_reminded_on per user).
"""
from __future__ import annotations

import datetime as dt
import logging
import zoneinfo

from apscheduler.schedulers.background import BackgroundScheduler

from app.config import settings
from app.db.base import SessionLocal
from app.models.notification import NotificationPreference
from app.models.programme import Programme, ProgrammeSession
from app.models.user import User
from app.models.logs import WorkoutLog
from app.notifications import triggers

logger = logging.getLogger("fitvise.scheduler")
_scheduler: BackgroundScheduler | None = None


def _user_now(user: User) -> dt.datetime:
    tzname = user.timezone or settings.default_timezone
    try:
        tz = zoneinfo.ZoneInfo(tzname)
    except Exception:  # noqa: BLE001
        tz = zoneinfo.ZoneInfo("UTC")
    return dt.datetime.now(tz)


def daily_reminders() -> None:
    with SessionLocal() as db:
        rows = (
            db.query(User, NotificationPreference)
            .join(NotificationPreference, NotificationPreference.user_id == User.id)
            .filter(
                User.deleted_at.is_(None),
                NotificationPreference.daily_reminder_enabled.is_(True),
            )
            .all()
        )
        for user, prefs in rows:
            now = _user_now(user)
            if now.strftime("%H:%M") == prefs.daily_reminder_time:
                triggers.daily_reminder(
                    db, user.id, "Don't forget to log today's workout, meals, and metrics."
                )
                logger.info("daily reminder -> user=%s", user.id)


def missed_workout_sweep() -> None:
    with SessionLocal() as db:
        users = db.query(User).filter(User.deleted_at.is_(None)).all()
        for user in users:
            now = _user_now(user)
            # only nudge in the evening window
            if now.hour < 20:
                continue
            weekday = now.weekday()  # 0=Mon
            prog = (
                db.query(Programme)
                .filter(Programme.user_id == user.id, Programme.status == "active")
                .first()
            )
            if prog is None:
                continue
            planned = (
                db.query(ProgrammeSession)
                .filter(
                    ProgrammeSession.programme_id == prog.id,
                    ProgrammeSession.week_number == prog.current_week,
                    ProgrammeSession.day_of_week == weekday,
                    ProgrammeSession.session_type != "rest",
                )
                .first()
            )
            if planned is None:
                continue
            logged = (
                db.query(WorkoutLog)
                .filter(
                    WorkoutLog.user_id == user.id,
                    WorkoutLog.date == now.date(),
                    WorkoutLog.deleted_at.is_(None),
                )
                .first()
            )
            if logged is None:
                triggers.missed_workout(db, user.id, planned.session_type)
                logger.info("missed-workout nudge -> user=%s", user.id)


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(daily_reminders, "cron", minute="*", id="daily_reminders", max_instances=1)
    _scheduler.add_job(
        missed_workout_sweep, "cron", minute=5, id="missed_workout_sweep", max_instances=1
    )
    _scheduler.start()
    logger.info("notification scheduler started")


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
