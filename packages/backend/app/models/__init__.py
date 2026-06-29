"""Importing this package registers every ORM model on ``Base.metadata``.

The DB bootstrap (app.db.migrate) imports this module so create_all / Alembic
autogenerate see the full schema.
"""
from app.models.checkin import CheckInRecord, NonScaleVictory, WeeklyTarget
from app.models.logs import (
    BehaviourFlag,
    BodyMetrics,
    DietLog,
    InjuryLog,
    RecoveryLog,
    WorkoutLog,
    WorkoutSetLog,
)
from app.models.notification import (
    Notification,
    NotificationPreference,
    PushSubscription,
)
from app.models.oauth import OAuthClient, OAuthGrant, OAuthToken
from app.models.programme import Exercise, Programme, ProgrammeSession
from app.models.substitution import ExerciseSubstitution
from app.models.user import User, UserProfile

__all__ = [
    "User",
    "UserProfile",
    "Programme",
    "ProgrammeSession",
    "Exercise",
    "ExerciseSubstitution",
    "WorkoutLog",
    "WorkoutSetLog",
    "DietLog",
    "BodyMetrics",
    "RecoveryLog",
    "BehaviourFlag",
    "InjuryLog",
    "CheckInRecord",
    "NonScaleVictory",
    "WeeklyTarget",
    "Notification",
    "PushSubscription",
    "NotificationPreference",
    "OAuthClient",
    "OAuthGrant",
    "OAuthToken",
]
