"""Web Push delivery via VAPID (pywebpush).

Dead subscriptions (404/410) are marked expired so the scheduler stops trying.
All failures are swallowed and logged — a push failure must never break the
request that triggered it.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.db.base import utcnow
from app.models.notification import PushSubscription

logger = logging.getLogger("fitvise.webpush")

try:  # pywebpush is optional at import time so the app still boots without keys
    from pywebpush import WebPushException, webpush
except Exception:  # pragma: no cover
    webpush = None
    WebPushException = Exception


def _vapid_claims() -> dict:
    return {"sub": settings.vapid_subject}


def send_to_subscription(db: Session, sub: PushSubscription, payload: dict) -> bool:
    if not settings.webpush_enabled or webpush is None:
        return False
    try:
        webpush(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims=_vapid_claims(),
            ttl=86400,
        )
        return True
    except WebPushException as exc:  # pragma: no cover - network dependent
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in (404, 410):
            sub.expired_at = utcnow()
            db.add(sub)
            db.commit()
            logger.info("Push subscription %s expired (%s)", sub.id, status)
        else:
            logger.warning("Web push failed for %s: %s", sub.id, exc)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("Web push error for %s: %s", sub.id, exc)
        return False


def send_to_user(db: Session, user_id: str, payload: dict) -> int:
    """Fan a payload out to all of a user's live push subscriptions."""
    subs = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id, PushSubscription.expired_at.is_(None))
        .all()
    )
    return sum(1 for s in subs if send_to_subscription(db, s, payload))
