"""First-run database bootstrap.

For the scaffold this uses ``Base.metadata.create_all`` (idempotent). A proper
Alembic setup lives under ``alembic/`` for schema evolution once the model
stabilises; this module is what the container entrypoint calls on boot.

In single_user mode it also provisions the sole user so the app is usable with
zero manual setup (the setup wizard can later rename / set preferences).
"""
from __future__ import annotations

import os

from app.config import AuthMode, settings
from app.db.base import Base, SessionLocal, engine
from app import models  # noqa: F401  (registers all tables on Base.metadata)


def create_all() -> None:
    Base.metadata.create_all(bind=engine)


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
    ensure_single_user()
    print("[fitvise] migrations complete.")


if __name__ == "__main__":
    main()
