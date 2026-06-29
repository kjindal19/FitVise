"""Programme validation, persistence, and versioning (PRD §3.4 / §7).

``validate_programme`` enforces *structure* (not coaching quality) and returns a
human-readable reason on failure so the AI can self-correct. ``write_programme``
archives the previous active programme and persists the new validated version,
projecting the normalised Session/Exercise rows alongside the AI JSON.
"""
from __future__ import annotations

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.base import utcnow
from app.models.programme import Exercise, Programme, ProgrammeSession
from app.schemas.programme import ProgrammeWrite

VALID_SESSION_TYPES = {
    "push", "pull", "lower", "upper", "full", "walk", "run", "class", "rest", "cardio", "mobility",
}


class ProgrammeValidationError(Exception):
    """Raised with a human-readable message → MCP code VALIDATION_FAILED."""


def validate_programme(payload: dict) -> ProgrammeWrite:
    """Parse + structurally validate an AI-authored programme payload."""
    try:
        prog = ProgrammeWrite.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        loc = ".".join(str(p) for p in first["loc"])
        raise ProgrammeValidationError(f"Invalid programme at '{loc}': {first['msg']}") from exc

    if not prog.sessions:
        raise ProgrammeValidationError("Programme must contain at least one session.")

    for i, sess in enumerate(prog.sessions):
        if sess.session_type not in VALID_SESSION_TYPES:
            raise ProgrammeValidationError(
                f"sessions[{i}].session_type '{sess.session_type}' is not one of "
                f"{sorted(VALID_SESSION_TYPES)}."
            )
        if sess.week_number > prog.total_weeks:
            raise ProgrammeValidationError(
                f"sessions[{i}].week_number {sess.week_number} exceeds total_weeks "
                f"{prog.total_weeks}."
            )
        for j, ex in enumerate(sess.exercises):
            if ex.reps_min and ex.reps_max and ex.reps_min > ex.reps_max:
                raise ProgrammeValidationError(
                    f"sessions[{i}].exercises[{j}] reps_min > reps_max."
                )

    if prog.current_week > prog.total_weeks:
        raise ProgrammeValidationError("current_week exceeds total_weeks.")

    return prog


def write_programme(db: Session, *, user_id: str, payload: dict) -> Programme:
    """Validate, archive the prior active programme, and persist a new version."""
    prog = validate_programme(payload)

    prior = (
        db.query(Programme)
        .filter(Programme.user_id == user_id, Programme.status == "active")
        .order_by(Programme.created_at.desc())
        .first()
    )
    if prior is not None:
        prior.status = "archived"
        prior.updated_at = utcnow()

    phase_count = len(prog.phases or []) or 1
    new = Programme(
        user_id=user_id,
        name=prog.name,
        total_weeks=prog.total_weeks,
        current_week=prog.current_week,
        phase_count=phase_count,
        goal_type=prog.goal_type,
        status="active",
        created_by="ai",
        content=prog.model_dump(),
        supersedes_id=prior.id if prior else None,
    )
    db.add(new)
    db.flush()

    for sess in prog.sessions:
        s = ProgrammeSession(
            programme_id=new.id,
            week_number=sess.week_number,
            day_of_week=sess.day_of_week,
            session_type=sess.session_type,
            estimated_duration_minutes=sess.estimated_duration_minutes,
            notes=sess.notes,
        )
        db.add(s)
        db.flush()
        for ex in sess.exercises:
            db.add(
                Exercise(
                    session_id=s.id,
                    name=ex.name,
                    order_index=ex.order_index,
                    sets=ex.sets,
                    reps_min=ex.reps_min,
                    reps_max=ex.reps_max,
                    rest_seconds=ex.rest_seconds,
                    form_notes=ex.form_notes,
                    substitutes=ex.substitutes,
                )
            )

    db.commit()
    db.refresh(new)
    return new
