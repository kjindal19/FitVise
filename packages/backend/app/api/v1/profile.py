"""User + onboarding profile endpoints (PRD §3.1 fallback form, §3.5)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.onboarding import compute_onboarding_status
from app.db.base import get_db, utcnow
from app.models.user import User, UserProfile
from app.schemas.user import (
    OnboardingStatus,
    ProfileRead,
    ProfileUpdate,
    UserRead,
    UserUpdate,
)

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_or_create_profile(db: Session, user: User) -> UserProfile:
    if user.profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(user)
    return user.profile


@router.get("", response_model=ProfileRead)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserProfile:
    return _get_or_create_profile(db, user)


@router.put("", response_model=ProfileRead)
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    profile = _get_or_create_profile(db, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/user", response_model=UserRead)
def update_user(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/onboarding-status", response_model=OnboardingStatus)
def onboarding_status(user: User = Depends(get_current_user)) -> OnboardingStatus:
    return compute_onboarding_status(user)


@router.post("/complete-onboarding", response_model=OnboardingStatus)
def complete_onboarding(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> OnboardingStatus:
    if user.onboarding_completed_at is None:
        user.onboarding_completed_at = utcnow()
        db.commit()
        db.refresh(user)
    return compute_onboarding_status(user)
