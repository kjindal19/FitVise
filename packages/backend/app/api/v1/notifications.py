"""Notification center + Web Push subscription management (additional ask)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.config import settings
from app.db.base import get_db, utcnow
from app.models.notification import Notification, NotificationPreference, PushSubscription
from app.models.user import User
from app.notifications.service import get_or_create_prefs, notify
from app.schemas.notification import (
    NotificationPreferenceRead,
    NotificationPreferenceUpdate,
    NotificationRead,
    PushSubscriptionCreate,
    VapidPublicKey,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ---- In-app center -------------------------------------------------
@router.get("", response_model=list[NotificationRead])
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Notification).filter(Notification.user_id == user.id)
    if unread_only:
        q = q.filter(Notification.read_at.is_(None))
    return q.order_by(Notification.created_at.desc()).limit(min(limit, 200)).all()


@router.get("/unread-count")
def unread_count(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.read_at.is_(None))
        .count()
    )
    return {"unread": count}


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_read(
    notification_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    note = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user.id
    ).first()
    if not note:
        raise HTTPException(404, "Not found")
    if note.read_at is None:
        note.read_at = utcnow()
        db.commit()
        db.refresh(note)
    return note


@router.post("/read-all")
def mark_all_read(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user.id, Notification.read_at.is_(None))
        .update({Notification.read_at: utcnow()})
    )
    db.commit()
    return {"updated": updated}


# ---- Preferences ---------------------------------------------------
@router.get("/preferences", response_model=NotificationPreferenceRead)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_or_create_prefs(db, user.id)


@router.put("/preferences", response_model=NotificationPreferenceRead)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    prefs: NotificationPreference = get_or_create_prefs(db, user.id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, field, value)
    db.commit()
    db.refresh(prefs)
    return prefs


# ---- Web Push ------------------------------------------------------
@router.get("/vapid-public-key", response_model=VapidPublicKey)
def vapid_public_key() -> VapidPublicKey:
    return VapidPublicKey(public_key=settings.vapid_public_key, enabled=settings.webpush_enabled)


@router.post("/push/subscribe", status_code=201)
def subscribe_push(
    payload: PushSubscriptionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == payload.endpoint
    ).first()
    if existing:
        existing.user_id = user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
        existing.user_agent = payload.user_agent
        existing.expired_at = None
    else:
        db.add(
            PushSubscription(
                user_id=user.id,
                endpoint=payload.endpoint,
                p256dh=payload.keys.p256dh,
                auth=payload.keys.auth,
                user_agent=payload.user_agent,
            )
        )
    db.commit()
    return {"ok": True}


@router.post("/push/unsubscribe")
def unsubscribe_push(
    endpoint: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> dict:
    db.query(PushSubscription).filter(
        PushSubscription.endpoint == endpoint, PushSubscription.user_id == user.id
    ).delete()
    db.commit()
    return {"ok": True}


@router.post("/test")
def send_test(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    """Send a test notification to verify in-app + push delivery."""
    note = notify(
        db,
        user_id=user.id,
        type="generic",
        title="FitVise test notification",
        body="If you can see this, notifications are working. 🎉",
        data={"screen": "home"},
    )
    return {"ok": True, "notification_id": note.id if note else None}
