"""Check-ins, non-scale victories, and weekly targets (PRD §4.1)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_column, pk_column


class CheckInRecord(Base):
    __tablename__ = "checkin_records"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    weight_at_checkin: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_at_checkin: Mapped[float | None] = mapped_column(Float, nullable=True)
    sessions_planned: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sessions_completed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    targets_next_week: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # References the programme version active for this check-in (PRD §7).
    programme_id: Mapped[str | None] = mapped_column(ForeignKey("programmes.id"), nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NonScaleVictory(Base):
    __tablename__ = "non_scale_victories"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    logged_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WeeklyTarget(Base):
    __tablename__ = "weekly_targets"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_start_date: Mapped[dt.date] = mapped_column(Date, nullable=False, index=True)
    weight_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    behavioural_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    training_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    # ai | user
    set_by: Mapped[str] = mapped_column(String(8), nullable=False, default="ai")
    created_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
