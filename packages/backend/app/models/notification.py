"""Notification entities (additional ask — in-app center + Web Push).

- ``Notification``      : a persisted in-app notification (the bell/inbox).
- ``PushSubscription``  : a browser Web Push endpoint registered by the PWA.
- ``NotificationPreference`` : per-user channel + reminder settings.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_column, pk_column, updated_at_column


# Notification categories (drive icon/routing on the client).
NOTIFICATION_TYPES = (
    "daily_reminder",      # scheduled "log your day / today's workout"
    "missed_workout",      # planned session passed with no workout log
    "workout_updated",     # AI changed the programme via MCP
    "checkin_ready",       # weekly check-in is due / a new summary was written
    "checkin_summary",     # AI wrote a check-in summary
    "weekly_targets",      # AI set next-week targets
    "streak_milestone",    # streak / NSV celebration
    "generic",
)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False, default="generic")
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Optional deep link / payload the client uses to navigate (e.g. {"screen":"workout"}).
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    read_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()
    # Set when a push is rejected with 404/410 — the subscription is dead.
    expired_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    # Channels
    inapp_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    webpush_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Daily reminder
    daily_reminder_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_reminder_time: Mapped[str] = mapped_column(String(5), default="18:00", nullable=False)  # HH:MM local

    # Event toggles
    missed_workout_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    workout_updated_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    checkin_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    updated_at: Mapped[dt.datetime] = updated_at_column()
