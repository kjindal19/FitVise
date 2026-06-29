"""Shared FastAPI dependencies — primarily resolving the current user.

Resolution differs by deployment mode (PRD §5):
- single_user : there is exactly one user; no token required. We return it.
- multi_user / managed : require a Bearer app-JWT and resolve sub -> user.
"""
from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.security import decode_access_token
from app.config import settings
from app.db.base import get_db
from app.models.user import User


def _single_user(db: Session) -> User:
    user = db.query(User).filter(User.deleted_at.is_(None)).first()
    if user is None:
        # Should not happen — migrate.ensure_single_user provisions one.
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, "No user provisioned")
    return user


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    if not settings.is_multi_user:
        return _single_user(db)

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_access_token(token)
    except Exception:  # noqa: BLE001 - any decode failure is a 401
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = db.get(User, payload.get("sub"))
    if user is None or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Admin only")
    return user
