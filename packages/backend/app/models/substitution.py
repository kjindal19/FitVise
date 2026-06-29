"""Exercise substitutions flagged by the AI (MCP tool add_exercise_substitution)."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, created_at_column, pk_column


class ExerciseSubstitution(Base):
    __tablename__ = "exercise_substitutions"

    id: Mapped[str] = pk_column()
    user_id: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    programme_id: Mapped[str | None] = mapped_column(ForeignKey("programmes.id"), nullable=True)
    original_exercise: Mapped[str] = mapped_column(String(160), nullable=False)
    substitute_exercise: Mapped[str] = mapped_column(String(160), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = created_at_column()
    deleted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
