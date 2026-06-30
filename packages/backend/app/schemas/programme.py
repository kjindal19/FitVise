"""Programme schemas — also the canonical write contract validated on MCP
``update_programme`` (PRD §3.4 / §7). ``ProgrammeWrite`` is intentionally the
shape the AI authors; validation lives in app/programme/validation.py.
"""
from __future__ import annotations

import datetime as dt
import re

from pydantic import AliasChoices, BaseModel, Field, model_validator

from app.schemas.common import ORMModel

_REPS_RANGE = re.compile(r"^\s*(\d+)\s*[-–—to]+\s*(\d+)\s*$")
_REPS_SINGLE = re.compile(r"^\s*(\d+)\s*$")


class ExerciseIn(BaseModel):
    """One prescribed movement.

    Authored to tolerate the shape an AI naturally writes: ``reps`` may be a
    plain number, a ``"10-12"`` range, or free text like ``"30-45 sec hold"``;
    ``notes`` is accepted as an alias for ``form_notes``. Numeric ranges are
    parsed into reps_min/reps_max; anything else is kept verbatim in reps_raw.
    """

    name: str
    order_index: int = 0
    sets: int | None = Field(default=None, ge=1, le=20)
    reps_min: int | None = Field(default=None, ge=1, le=1000)
    reps_max: int | None = Field(default=None, ge=1, le=1000)
    reps_raw: str | None = Field(default=None, max_length=60)
    rest_seconds: int | None = Field(default=None, ge=0, le=1800)
    form_notes: str | None = Field(
        default=None, validation_alias=AliasChoices("form_notes", "notes")
    )
    substitutes: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_reps(cls, data):
        """Accept a single ``reps`` field (int or str) and split it into
        reps_min/reps_max when numeric, else preserve it in reps_raw."""
        if not isinstance(data, dict):
            return data
        reps = data.get("reps")
        if reps is None or data.get("reps_min") is not None or data.get("reps_max") is not None:
            return data
        text = str(reps).strip()
        if (m := _REPS_RANGE.match(text)):
            data["reps_min"], data["reps_max"] = int(m.group(1)), int(m.group(2))
        elif (m := _REPS_SINGLE.match(text)):
            data["reps_min"] = data["reps_max"] = int(m.group(1))
        else:
            data.setdefault("reps_raw", text[:60])
        return data


class SessionIn(BaseModel):
    # Defaults to week 1 so the coach can author a single-week template without
    # repeating week_number on every session.
    week_number: int = Field(default=1, ge=1, le=104)
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    session_type: str
    label: str | None = Field(default=None, max_length=120)
    estimated_duration_minutes: int | None = Field(default=None, ge=0, le=600)
    notes: str | None = None
    exercises: list[ExerciseIn] = Field(default_factory=list)
    # Optional, coach-included only. Same flexible shape as main exercises.
    warmup: list[ExerciseIn] | None = None
    cooldown: list[ExerciseIn] | None = None


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
    reps_raw: str | None = None
    rest_seconds: int | None = None
    form_notes: str | None = None
    substitutes: list | None = None


class SessionRead(ORMModel):
    id: str
    week_number: int
    day_of_week: int | None = None
    session_type: str
    label: str | None = None
    estimated_duration_minutes: int | None = None
    notes: str | None = None
    exercises: list[ExerciseRead] = Field(default_factory=list)
    warmup: list | None = None
    cooldown: list | None = None


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
