"""User account + onboarding profile (PRD §4.1)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, created_at_column, pk_column, updated_at_column


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = pk_column()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)

    # Auth — password only used in multi_user / managed; null in single_user.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    weight_unit: Mapped[str] = mapped_column(String(8), default="kg", nullable=False)   # kg | lbs
    measurement_unit: Mapped[str] = mapped_column(String(8), default="cm", nullable=False)  # cm | in
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)

    onboarding_completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    profile: Mapped["UserProfile | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )

    current_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    goal_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    target_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_waist: Mapped[float | None] = mapped_column(Float, nullable=True)

    diet_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    dietary_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)

    training_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # gym | home_bodyweight | walk_run | classes_zumba | hybrid
    training_modality: Mapped[str | None] = mapped_column(String(40), nullable=True)
    preferred_activities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    equipment_available: Mapped[list | None] = mapped_column(JSON, nullable=True)
    session_length_preference: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gym_access_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    injuries_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferences_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    updated_at: Mapped[dt.datetime] = updated_at_column()

    user: Mapped["User"] = relationship(back_populates="profile")
