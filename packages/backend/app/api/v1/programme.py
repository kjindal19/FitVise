"""Programme endpoints. Reads serve the UI; writes go through the validating
service (PRD §7) and notify the user that their plan changed."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.base import get_db
from app.models.programme import Programme
from app.models.user import User
from app.notifications import triggers
from app.programme.service import ProgrammeValidationError, write_programme
from app.schemas.programme import ProgrammeRead, ProgrammeWrite

router = APIRouter(prefix="/programme", tags=["programme"])


def _active(db: Session, user_id: str) -> Programme | None:
    return (
        db.query(Programme)
        .filter(Programme.user_id == user_id, Programme.status == "active")
        .order_by(Programme.created_at.desc())
        .first()
    )


@router.get("/current", response_model=ProgrammeRead)
def current_programme(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prog = _active(db, user.id)
    if prog is None:
        raise HTTPException(404, "No active programme")
    return prog


@router.get("/history", response_model=list[ProgrammeRead])
def programme_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Programme)
        .filter(Programme.user_id == user.id)
        .order_by(Programme.created_at.desc())
        .all()
    )


@router.put("", response_model=ProgrammeRead)
def upsert_programme(
    payload: ProgrammeWrite,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manual / import write path (the AI uses the MCP ``update_programme`` tool,
    which calls the same service)."""
    try:
        prog = write_programme(db, user_id=user.id, payload=payload.model_dump())
    except ProgrammeValidationError as exc:
        raise HTTPException(422, str(exc))
    triggers.workout_updated(db, user.id, prog.name)
    return prog
