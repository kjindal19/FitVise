"""Check-in, non-scale victory, and weekly-target schemas."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel

from app.schemas.common import ORMModel


class CheckInCreate(BaseModel):
    date: dt.date
    weight_at_checkin: float | None = None
    waist_at_checkin: float | None = None
    sessions_planned: int | None = None
    sessions_completed: int | None = None
    ai_summary: str | None = None
    targets_next_week: dict | None = None
    programme_id: str | None = None


class CheckInRead(ORMModel):
    id: str
    date: dt.date
    weight_at_checkin: float | None = None
    waist_at_checkin: float | None = None
    sessions_planned: int | None = None
    sessions_completed: int | None = None
    ai_summary: str | None = None
    targets_next_week: dict | None = None
    programme_id: str | None = None
    created_at: dt.datetime


class NSVCreate(BaseModel):
    date: dt.date
    description: str


class NSVRead(ORMModel):
    id: str
    date: dt.date
    description: str
    logged_at: dt.datetime


class WeeklyTargetCreate(BaseModel):
    week_start_date: dt.date
    weight_target: float | None = None
    waist_target: float | None = None
    behavioural_goal: str | None = None
    training_goal: str | None = None
    set_by: str = "user"


class WeeklyTargetRead(ORMModel):
    id: str
    week_start_date: dt.date
    weight_target: float | None = None
    waist_target: float | None = None
    behavioural_goal: str | None = None
    training_goal: str | None = None
    set_by: str
    created_at: dt.datetime
