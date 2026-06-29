"""Notification, push-subscription, and preference schemas."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel

from app.schemas.common import ORMModel


class NotificationRead(ORMModel):
    id: str
    type: str
    title: str
    body: str | None = None
    data: dict | None = None
    read_at: dt.datetime | None = None
    created_at: dt.datetime


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: PushKeys
    user_agent: str | None = None


class NotificationPreferenceRead(ORMModel):
    inapp_enabled: bool
    webpush_enabled: bool
    daily_reminder_enabled: bool
    daily_reminder_time: str
    missed_workout_enabled: bool
    workout_updated_enabled: bool
    checkin_enabled: bool


class NotificationPreferenceUpdate(BaseModel):
    inapp_enabled: bool | None = None
    webpush_enabled: bool | None = None
    daily_reminder_enabled: bool | None = None
    daily_reminder_time: str | None = None
    missed_workout_enabled: bool | None = None
    workout_updated_enabled: bool | None = None
    checkin_enabled: bool | None = None


class VapidPublicKey(BaseModel):
    public_key: str | None = None
    enabled: bool
