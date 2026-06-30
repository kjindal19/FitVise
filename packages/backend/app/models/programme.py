"""Programme engine entities (PRD §3.4 / §4.1 / §7).

The AI-authored programme is stored as validated JSON on ``Programme.content``
with a few columns projected out for querying (current_week, status, …).
Normalised Session/Exercise rows are also kept so the app can render and the
REST API can serve structured data without re-parsing JSON every read.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, created_at_column, pk_column, updated_at_column


class Programme(Base):
    __tablename__ = "programmes"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=12)
    current_week: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    phase_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    goal_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # active | archived | draft
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active", index=True)
    # ai | import | manual
    created_by: Mapped[str] = mapped_column(String(16), nullable=False, default="ai")

    # Full AI-authored JSON payload (validated against the programme schema on write).
    content: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    # Version chain: points at the programme this one replaced (PRD §7 versioning).
    supersedes_id: Mapped[str | None] = mapped_column(
        ForeignKey("programmes.id"), nullable=True
    )

    created_at: Mapped[dt.datetime] = created_at_column()
    updated_at: Mapped[dt.datetime] = updated_at_column()

    sessions: Mapped[list["ProgrammeSession"]] = relationship(
        back_populates="programme", cascade="all, delete-orphan", order_by="ProgrammeSession.week_number"
    )


class ProgrammeSession(Base):
    __tablename__ = "programme_sessions"

    id: Mapped[str] = pk_column()
    programme_id: Mapped[str] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 0=Mon … 6=Sun
    # push | pull | lower | upper | full | walk | run | class | rest
    session_type: Mapped[str] = mapped_column(String(24), nullable=False)
    # Human-friendly session title authored by the coach, e.g. "Upper A — Push".
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional warm-up / cool-down blocks: list[{name, reps, duration, notes}]. Only
    # populated when the coach includes them; the UI hides empty blocks entirely.
    warmup: Mapped[list | None] = mapped_column(JSON, nullable=True)
    cooldown: Mapped[list | None] = mapped_column(JSON, nullable=True)

    programme: Mapped["Programme"] = relationship(back_populates="sessions")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="Exercise.order_index"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = pk_column()
    session_id: Mapped[str] = mapped_column(
        ForeignKey("programme_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reps_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Verbatim rep prescription when it isn't a plain numeric range, e.g.
    # "30-45 sec hold", "AMRAP", "8 each side". Rendered as-is in the UI.
    reps_raw: Mapped[str | None] = mapped_column(String(60), nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    form_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    substitutes: Mapped[list | None] = mapped_column(JSON, nullable=True)

    session: Mapped["ProgrammeSession"] = relationship(back_populates="exercises")
