"""First-run database bootstrap.

For the scaffold this uses ``Base.metadata.create_all`` (idempotent). A proper
Alembic setup lives under ``alembic/`` for schema evolution once the model
stabilises; this module is what the container entrypoint calls on boot.

In single_user mode it also provisions the sole user so the app is usable with
zero manual setup (the setup wizard can later rename / set preferences).
"""
from __future__ import annotations

import os

from sqlalchemy import inspect, text

from app.config import AuthMode, settings
from app.db.base import Base, SessionLocal, engine
from app import models  # noqa: F401  (registers all tables on Base.metadata)

# Columns added after the initial schema shipped. ``create_all`` only creates
# missing *tables*, never new columns on existing ones, so we add these by hand
# (idempotent). SQLite and PostgreSQL both support ``ALTER TABLE ADD COLUMN``.
_ADDITIVE_COLUMNS: list[tuple[str, str, str]] = [
    ("users", "gender", "VARCHAR(20)"),
    ("user_profiles", "eating_patterns", "TEXT"),
    ("user_profiles", "supplements_notes", "TEXT"),
    ("user_profiles", "medical_notes", "TEXT"),
    ("programme_sessions", "label", "VARCHAR(120)"),
    ("programme_sessions", "warmup", "JSON"),
    ("programme_sessions", "cooldown", "JSON"),
    ("exercises", "reps_raw", "VARCHAR(60)"),
]


def create_all() -> None:
    Base.metadata.create_all(bind=engine)


def add_missing_columns() -> None:
    """Apply additive column migrations to a pre-existing database."""
    insp = inspect(engine)
    tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, column, sql_type in _ADDITIVE_COLUMNS:
            if table not in tables:
                continue  # create_all() just made it with the column already present
            if column in {c["name"] for c in insp.get_columns(table)}:
                continue
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
            print(f"[fitvise] added column {table}.{column}")


def ensure_single_user() -> None:
    """In single_user mode, make sure exactly one user exists."""
    if settings.auth_mode is not AuthMode.single_user:
        return
    from app.models.user import User
    from app.models.notification import NotificationPreference

    with SessionLocal() as db:
        user = db.query(User).first()
        if user is None:
            user = User(name=os.getenv("FITVISE_DEFAULT_USER_NAME", "You"), is_admin=True)
            db.add(user)
            db.flush()
            db.add(NotificationPreference(user_id=user.id))
            db.commit()
            print(f"[fitvise] created single-user account id={user.id}")


def main() -> None:
    print("[fitvise] create_all() …")
    create_all()
    add_missing_columns()
    ensure_single_user()
    print("[fitvise] migrations complete.")


if __name__ == "__main__":
    main()
