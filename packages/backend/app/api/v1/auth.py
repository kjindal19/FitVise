"""Web/app authentication (PRD §5).

- single_user: /auth/me returns the sole user; no login required.
- multi_user/managed: register + password login issue an app JWT used as a
  Bearer token by the SPA. (The MCP path uses OAuth, not this token.)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.auth.security import create_access_token, hash_password, verify_password
from app.config import settings
from app.db.base import get_db
from app.models.notification import NotificationPreference
from app.models.user import User
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.is_multi_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Registration is disabled in single_user mode")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    first_user = db.query(User).first() is None
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        is_admin=first_user,  # first registered account becomes the instance admin
    )
    db.add(user)
    db.flush()
    db.add(NotificationPreference(user_id=user.id))
    db.commit()

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=settings.access_token_ttl)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if not settings.is_multi_user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Login is disabled in single_user mode")
    user = db.query(User).filter(User.email == payload.email, User.deleted_at.is_(None)).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, expires_in=settings.access_token_ttl)


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user
