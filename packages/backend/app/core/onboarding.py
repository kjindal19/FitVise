"""Onboarding completeness logic, shared by REST and the MCP server.

The required-field set is what the AI needs to author a first programme. Used by
``get_onboarding_status`` (MCP) and the REST profile endpoints.
"""
from __future__ import annotations

from app.models.user import User
from app.schemas.user import OnboardingStatus

# (attribute_path, human_label) — attribute resolved on user or user.profile
REQUIRED_FIELDS: list[tuple[str, str]] = [
    ("user.name", "name"),
    ("profile.goal_type", "goal_type"),
    ("profile.training_modality", "training_modality"),
    ("profile.training_days_per_week", "training_days_per_week"),
    ("profile.current_weight", "current_weight"),
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
