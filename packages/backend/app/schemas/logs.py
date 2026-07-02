"""Schemas for logging entities (workout, diet, metrics, recovery, journal)."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


# ---- Workout -------------------------------------------------------
class WorkoutSetIn(BaseModel):
    exercise_name: str
    set_number: int
    weight: float | None = None
    reps: int | None = None
    is_personal_best: bool = False


class WorkoutSetRead(ORMModel):
    id: str
    exercise_name: str
    set_number: int
    weight: float | None = None
    reps: int | None = None
    is_personal_best: bool
    logged_at: dt.datetime


class WorkoutLogCreate(BaseModel):
    session_id: str | None = None
    date: dt.date
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    notes: str | None = None
    sets: list[WorkoutSetIn] = Field(default_factory=list)


class WorkoutLogRead(ORMModel):
    id: str
    session_id: str | None = None
    date: dt.date
    started_at: dt.datetime | None = None
    completed_at: dt.datetime | None = None
    notes: str | None = None
    created_at: dt.datetime
    sets: list[WorkoutSetRead] = Field(default_factory=list)


# ---- Diet ----------------------------------------------------------
class DietLogCreate(BaseModel):
    date: dt.date
    # When the meal was eaten. Optional; defaults to "now" server-side. The slot
    # (morning/afternoon/evening/night) is derived from this on the client.
    logged_at: dt.datetime | None = None
    meal_slot: str
    description: str | None = None
    protein_quality: str | None = None
    flags: list[str] | None = None


class DietLogRead(ORMModel):
    id: str
    date: dt.date
    meal_slot: str
    description: str | None = None
    protein_quality: str | None = None
    flags: list | None = None
    logged_at: dt.datetime


# ---- Body metrics --------------------------------------------------
class BodyMetricsCreate(BaseModel):
    logged_at: dt.datetime | None = None
    weight: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    chest_cm: float | None = None
    left_arm_cm: float | None = None
    right_thigh_cm: float | None = None
    body_fat_pct: float | None = None
    notes: str | None = None


class BodyMetricsRead(ORMModel):
    id: str
    logged_at: dt.datetime
    weight: float | None = None
    waist_cm: float | None = None
    hip_cm: float | None = None
    chest_cm: float | None = None
    left_arm_cm: float | None = None
    right_thigh_cm: float | None = None
    body_fat_pct: float | None = None
    notes: str | None = None


# ---- Recovery ------------------------------------------------------
class RecoveryLogCreate(BaseModel):
    date: dt.date
    energy_level: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = None
    soreness_level: str | None = None
    soreness_location: str | None = None
    stress_level: int | None = Field(default=None, ge=1, le=3)


class RecoveryLogRead(ORMModel):
    id: str
    date: dt.date
    energy_level: int | None = None
    sleep_hours: float | None = None
    soreness_level: str | None = None
    soreness_location: str | None = None
    stress_level: int | None = None
    logged_at: dt.datetime


# ---- Behaviour flag ------------------------------------------------
class BehaviourFlagCreate(BaseModel):
    date: dt.date
    flag_type: str
    note: str | None = None


class BehaviourFlagRead(ORMModel):
    id: str
    date: dt.date
    flag_type: str
    note: str | None = None
    logged_at: dt.datetime


# ---- Injury --------------------------------------------------------
class InjuryLogCreate(BaseModel):
    date: dt.date
    body_area: str
    injury_type: str | None = None
    severity: int | None = Field(default=None, ge=1, le=5)
    context: str | None = None
    note: str | None = None


class InjuryLogRead(ORMModel):
    id: str
    date: dt.date
    body_area: str
    injury_type: str | None = None
    severity: int | None = None
    context: str | None = None
    note: str | None = None
    logged_at: dt.datetime
