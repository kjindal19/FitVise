"""Onboarding completeness logic, shared by REST and the MCP server.

The required-field set is what the AI needs to author a first programme. Used by
``get_onboarding_status`` (MCP) and the REST profile endpoints.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.user import User, UserProfile
from app.schemas.user import OnboardingStatus

# Which model each writable field lives on, so a flat dict of updates can be
# routed to User vs UserProfile. Shared by the MCP write tools (server.py).
USER_FIELDS = {"name", "age", "gender", "weight_unit", "measurement_unit", "timezone"}
PROFILE_FIELDS = {
    "current_weight", "height", "goal_type", "target_weight", "target_waist",
    "diet_type", "dietary_restrictions", "eating_patterns", "supplements_notes",
    "medical_notes", "training_days_per_week", "training_modality",
    "preferred_activities", "equipment_available", "session_length_preference",
    "gym_access_type", "injuries_notes", "preferences_notes",
}


def apply_profile_updates(db: Session, user: User, updates: dict) -> User:
    """Persist a flat dict of profile updates (None values skipped), routing each
    field to the User row or its UserProfile (created if absent). Commits."""
    for field, value in updates.items():
        if value is not None and field in USER_FIELDS:
            setattr(user, field, value)

    profile = user.profile
    if profile is None:
        profile = UserProfile(user_id=user.id)
        db.add(profile)
    for field, value in updates.items():
        if value is not None and field in PROFILE_FIELDS:
            setattr(profile, field, value)

    db.commit()
    db.refresh(user)
    return user

# (attribute_path, human_label) — attribute resolved on user or user.profile.
# These are the inputs a coach needs to author a safe, personalised first
# programme + nutrition guidance, so onboarding can't complete without them.
REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("user.name", "name"),
    ("user.age", "age"),
    ("user.gender", "gender"),
    ("profile.height", "height"),
    ("profile.current_weight", "current_weight"),
    ("profile.goal_type", "goal_type"),
    ("profile.diet_type", "diet_type"),
    ("profile.training_modality", "training_modality"),
    ("profile.training_days_per_week", "training_days_per_week"),
]


def _resolve(user: User, path: str):
    obj, attr = path.split(".")
    target = user if obj == "user" else user.profile
    if target is None:
        return None
    return getattr(target, attr, None)


def compute_onboarding_status(user: User) -> OnboardingStatus:
    missing = [label for path, label in REQUIRED_FIELDS if _resolve(user, path) in (None, "")]
    return OnboardingStatus(
        onboarding_completed=user.onboarding_completed_at is not None,
        completed_at=user.onboarding_completed_at,
        missing_fields=missing,
    )
