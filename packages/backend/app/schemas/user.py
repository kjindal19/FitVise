"""Auth + user/profile schemas."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


# ---- Auth ----------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ---- User / profile ------------------------------------------------
class UserRead(ORMModel):
    id: str
    name: str
    age: int | None = None
    gender: str | None = None
    email: str | None = None
    is_admin: bool
    weight_unit: str
    measurement_unit: str
    timezone: str | None = None
    onboarding_completed_at: dt.datetime | None = None
    created_at: dt.datetime


class UserUpdate(BaseModel):
    name: str | None = None
    age: int | None = None
    gender: str | None = None
    email: EmailStr | None = None
    weight_unit: str | None = None
    measurement_unit: str | None = None
    timezone: str | None = None


class ProfileRead(ORMModel):
    current_weight: float | None = None
    height: float | None = None
    goal_type: str | None = None
    target_weight: float | None = None
    target_waist: float | None = None
    diet_type: str | None = None
    dietary_restrictions: str | None = None
    eating_patterns: str | None = None
    supplements_notes: str | None = None
    medical_notes: str | None = None
    training_days_per_week: int | None = None
    training_modality: str | None = None
    preferred_activities: list | None = None
    equipment_available: list | None = None
    session_length_preference: int | None = None
    gym_access_type: str | None = None
    injuries_notes: str | None = None
    preferences_notes: str | None = None
    updated_at: dt.datetime | None = None


class ProfileUpdate(BaseModel):
    current_weight: float | None = None
    height: float | None = None
    goal_type: str | None = None
    target_weight: float | None = None
    target_waist: float | None = None
    diet_type: str | None = None
    dietary_restrictions: str | None = None
    eating_patterns: str | None = None
    supplements_notes: str | None = None
    medical_notes: str | None = None
    training_days_per_week: int | None = None
    training_modality: str | None = None
    preferred_activities: list | None = None
    equipment_available: list | None = None
    session_length_preference: int | None = None
    gym_access_type: str | None = None
    injuries_notes: str | None = None
    preferences_notes: str | None = None


class OnboardingStatus(BaseModel):
    onboarding_completed: bool
    completed_at: dt.datetime | None = None
    missing_fields: list[str]
