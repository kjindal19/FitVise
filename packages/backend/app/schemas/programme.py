"""Programme schemas — also the canonical write contract validated on MCP
``update_programme`` (PRD §3.4 / §7). ``ProgrammeWrite`` is intentionally the
shape the AI authors; validation lives in app/programme/validation.py.
"""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ExerciseIn(BaseModel):
    name: str
    order_index: int = 0
    sets: int | None = Field(default=None, ge=1, le=20)
    reps_min: int | None = Field(default=None, ge=1, le=100)
    reps_max: int | None = Field(default=None, ge=1, le=100)
    rest_seconds: int | None = Field(default=None, ge=0, le=1800)
    form_notes: str | None = None
    substitutes: list[str] | None = None


class SessionIn(BaseModel):
    week_number: int = Field(ge=1, le=104)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    session_type: str
    estimated_duration_minutes: int | None = Field(default=None, ge=0, le=600)
    notes: str | None = None
    exercises: list[ExerciseIn] = Field(default_factory=list)


class ProgrammeWrite(BaseModel):
    """Payload the AI sends to update_programme / the manual editor."""

    name: str
    total_weeks: int = Field(ge=1, le=104)
    current_week: int = Field(default=1, ge=1, le=104)
    goal_type: str | None = None
    phases: list[dict] | None = None  # [{week_range, focus, intensity_label}]
    sessions: list[SessionIn] = Field(default_factory=list)


class ExerciseRead(ORMModel):
    id: str
    name: str
    order_index: int
    sets: int | None = None
    reps_min: int | None = None
    reps_max: int | None = None
    rest_seconds: int | None = None
    form_notes: str | None = None
    substitutes: list | None = None


class SessionRead(ORMModel):
    id: str
    week_number: int
    day_of_week: int | None = None
    session_type: str
    estimated_duration_minutes: int | None = None
    notes: str | None = None
    exercises: list[ExerciseRead] = Field(default_factory=list)


class ProgrammeRead(ORMModel):
    id: str
    name: str
    total_weeks: int
    current_week: int
    phase_count: int
    goal_type: str | None = None
    status: str
    created_by: str
    created_at: dt.datetime
    updated_at: dt.datetime
    sessions: list[SessionRead] = Field(default_factory=list)
