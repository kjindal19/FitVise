"""Health / status endpoint (PRD §13.7 — version, DB, MCP, OAuth reachability)."""
from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from app import __version__
from app.config import settings
from app.db.base import SessionLocal

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "version": __version__,
        "auth_mode": settings.auth_mode.value,
        "db": {"type": settings.db_type.value, "connected": db_ok},
        "mcp": {"endpoint": "/mcp", "transport": "streamable_http"},
        "oauth": {
            "enabled": settings.is_multi_user,
            "issuer": settings.issuer if settings.is_multi_user else None,
        },
        "webpush": {"enabled": settings.webpush_enabled},
    }
