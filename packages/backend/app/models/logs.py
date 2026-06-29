"""Logging entities: workout, diet, body metrics, recovery, behaviour, injury.

Every row carries ``user_id`` so the MCP layer and REST API can scope strictly
to the authenticated user (PRD §3.3 multi-tenant isolation). Soft delete via
``deleted_at`` (PRD §8 — no data deleted without explicit user action).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, created_at_column, pk_column


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        ForeignKey("programme_sessions.id"), nullable=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sets: Mapped[list["WorkoutSetLog"]] = relationship(
        back_populates="workout_log", cascade="all, delete-orphan", order_by="WorkoutSetLog.logged_at"
    )


class WorkoutSetLog(Base):
    __tablename__ = "workout_set_logs"

    id: Mapped[str] = pk_column()
    workout_log_id: Mapped[str] = mapped_column(
        ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_name: Mapped[str] = mapped_column(String(160), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    reps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_personal_best: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    logged_at: Mapped[dt.datetime] = created_at_column()

    workout_log: Mapped["WorkoutLog"] = relationship(back_populates="sets")


class DietLog(Base):
    __tablename__ = "diet_logs"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    # morning | afternoon | evening | night
    meal_slot: Mapped[str] = mapped_column(String(16), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # high | none | mixed
    protein_quality: Mapped[str | None] = mapped_column(String(8), nullable=True)
    flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    logged_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BodyMetrics(Base):
    __tablename__ = "body_metrics"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    logged_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hip_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    left_arm_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    right_thigh_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class RecoveryLog(Base):
    __tablename__ = "recovery_logs"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    energy_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    # none | mild | significant
    soreness_level: Mapped[str | None] = mapped_column(String(16), nullable=True)
    soreness_location: Mapped[str | None] = mapped_column(String(80), nullable=True)
    stress_level: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–3
    logged_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class BehaviourFlag(Base):
    __tablename__ = "behaviour_flags"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    # late_night_eating | sugar_craving | skipped_session | stress_eating |
    # emotional_eating | overate_at_meal | good_choice_moment
    flag_type: Mapped[str] = mapped_column(String(32), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InjuryLog(Base):
    __tablename__ = "injury_logs"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    body_area: Mapped[str] = mapped_column(String(80), nullable=False)
    # pain | discomfort | stiffness | swelling
    injury_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1–5
    # during_workout | after_workout | unrelated
    context: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    logged_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
