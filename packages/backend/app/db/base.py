"""SQLAlchemy engine, session factory, and declarative base.

SQLite (single-user) runs with WAL + check_same_thread off; PostgreSQL
(multi-user / managed) uses a pooled engine. Models import ``Base`` from here.
"""
from __future__ import annotations

import datetime as dt
import uuid
from collections.abc import Generator

from sqlalchemy import DateTime, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, mapped_column, sessionmaker

from app.config import DbType, settings


def _make_engine():
    url = settings.sqlalchemy_url
    if settings.db_type is DbType.sqlite:
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            future=True,
        )

        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _):  # pragma: no cover - thin glue
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute("PRAGMA foreign_keys=ON;")
            cur.close()

        return engine
    return create_engine(url, pool_pre_ping=True, future=True)


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base with shared id + timestamp conventions."""


def gen_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


# Reusable column factories (kept as functions so each model gets its own column).
def pk_column():
    return mapped_column(String(36), primary_key=True, default=gen_uuid)


def created_at_column():
    return mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


def updated_at_column():
    return mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
