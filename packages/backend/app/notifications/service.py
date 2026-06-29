"""Channel-agnostic notification service.

``notify`` is the single entry point: it persists an in-app notification (the
bell/inbox) and, if the user has Web Push enabled, fans the same payload out to
their browser subscriptions. Per-user preferences gate both channels.
"""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationPreference
from app.notifications import webpush

logger = logging.getLogger("fitvise.notifications")


def get_or_create_prefs(db: Session, user_id: str) -> NotificationPreference:
    prefs = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
    if prefs is None:
        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


# Map notification type -> the preference flag that gates it (None = always on).
_TYPE_GATE = {
    "missed_workout": "missed_workout_enabled",
    "workout_updated": "workout_updated_enabled",
    "checkin_ready": "checkin_enabled",
    "checkin_summary": "checkin_enabled",
    "weekly_targets": "checkin_enabled",
    "daily_reminder": "daily_reminder_enabled",
}


def notify(
    db: Session,
    *,
    user_id: str,
    type: str,
    title: str,
    body: str | None = None,
    data: dict | None = None,
) -> Notification | None:
    """Create + deliver a notification, respecting the user's preferences.

    Returns the persisted in-app Notification (or None if the category is
    disabled by the user).
    """
    prefs = get_or_create_prefs(db, user_id)

    gate = _TYPE_GATE.get(type)
    if gate is not None and not getattr(prefs, gate, True):
        return None

    note: Notification | None = None
    if prefs.inapp_enabled:
        note = Notification(user_id=user_id, type=type, title=title, body=body, data=data)
        db.add(note)
        db.commit()
        db.refresh(note)

    if prefs.webpush_enabled:
        payload = {
            "title": title,
            "body": body or "",
            "type": type,
            "data": data or {},
            "id": note.id if note else None,
        }
        try:
            sent = webpush.send_to_user(db, user_id, payload)
            logger.debug("web push fanout user=%s sent=%s", user_id, sent)
        except Exception as exc:  # noqa: BLE001 - never break the caller
            logger.warning("web push fanout failed user=%s: %s", user_id, exc)

    return note
