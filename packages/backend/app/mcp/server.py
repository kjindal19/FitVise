"""FitVise MCP server (Streamable HTTP) — the AI coach's read/write interface.

Built on the official MCP Python SDK's FastMCP. Mounted by app.main at /mcp.
Every tool resolves the calling user from the request's bearer token (see
app.mcp.auth) and scopes all queries to that user. Tool descriptions are written
for the AI to read — they double as the coach's instruction manual (PRD §6.4).
"""
from __future__ import annotations

import datetime as dt

from mcp.server.fastmcp import Context, FastMCP

from app.db.base import SessionLocal
from app.mcp import data
from app.mcp.auth import MCPAuthError, resolve_user
from app.programme.service import ProgrammeValidationError, write_programme
from app.schemas.common import mcp_err, mcp_ok
from app.notifications import triggers

mcp_server = FastMCP(
    name="fitvise",
    instructions=(
        "FitVise is the user's fitness journal. Use the read tools to load the user's "
        "profile, programme, and logs before coaching; use the write tools to update the "
        "programme, record check-in summaries, and set weekly targets. All data is scoped "
        "to the authenticated user."
    ),
    stateless_http=True,
    streamable_http_path="/",
)


def _headers(ctx: Context) -> dict[str, str]:
    """Best-effort extraction of HTTP headers from the FastMCP request context."""
    try:
        request = ctx.request_context.request
        if request is not None:
            return {k.lower(): v for k, v in request.headers.items()}
    except Exception:  # noqa: BLE001
        pass
    return {}


def _parse_date(value: str | None) -> dt.date | None:
    return dt.date.fromisoformat(value) if value else None


def _default_start(weeks: int) -> dt.date:
    return dt.date.today() - dt.timedelta(weeks=weeks)


# =====================================================================
# Read tools
# =====================================================================
@mcp_server.tool()
def get_user_profile(ctx: Context) -> dict:
    """Return the full user profile: name, age, weight, height, goal, diet type,
    training modality, injuries, and days available. Call this at the start of any
    coaching conversation to ground your advice in the user's actual situation."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(data.profile_dict(user), user_id=user.id)


@mcp_server.tool()
def get_onboarding_status(ctx: Context) -> dict:
    """Return whether onboarding is complete and which required profile fields are
    still missing. Call this first when running the onboarding workflow."""
    from app.core.onboarding import compute_onboarding_status

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(compute_onboarding_status(user).model_dump(mode="json"), user_id=user.id)


@mcp_server.tool()
def get_current_programme(ctx: Context, summary: bool = False) -> dict:
    """Return the active programme: week number, phase, weeks remaining, and this
    week's sessions with exercises. Set summary=true for a compact view without the
    session detail."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        prog = data.current_programme_dict(db, user.id, summary=summary)
        if prog is None:
            return mcp_err("No active programme. Use update_programme to create one.", "NOT_FOUND")
        return mcp_ok(prog, user_id=user.id)


@mcp_server.tool()
def get_session_plan(
    ctx: Context, day_of_week: int | None = None, session_type: str | None = None
) -> dict:
    """Return a specific session from this week's plan — all exercises with sets,
    reps, rest, and form notes. Identify it by day_of_week (0=Mon…6=Sun) and/or
    session_type (push/pull/lower/upper/full/walk/run/class). Returns the first
    match."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        plan = data.session_plan_dict(
            db, user.id, day_of_week=day_of_week, session_type=session_type
        )
        if plan is None:
            return mcp_err("No matching session in the current week's plan.", "NOT_FOUND")
        return mcp_ok(plan, user_id=user.id)


@mcp_server.tool()
def get_workout_logs(ctx: Context, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Return logged workout sessions as exercise × weight × reps per set. Defaults
    to the last 4 weeks unless a date range (YYYY-MM-DD) is given — avoid pulling
    all-time history to keep context lean."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        start = _parse_date(start_date) or _default_start(4)
        rows = data.workout_logs_dicts(db, user.id, start, _parse_date(end_date))
        return mcp_ok(rows, user_id=user.id, context_note="Last 4 weeks unless a range was specified.")


@mcp_server.tool()
def get_diet_logs(ctx: Context, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Return meal logs (descriptions + flags) for the date range. Defaults to the
    last 4 weeks. No calories or macros — FitVise logs what was eaten, not numbers."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        start = _parse_date(start_date) or _default_start(4)
        rows = data.diet_logs_dicts(db, user.id, start, _parse_date(end_date))
        return mcp_ok(rows, user_id=user.id, context_note="Last 4 weeks unless a range was specified.")


@mcp_server.tool()
def get_body_metrics(ctx: Context, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Return body weight and measurement history. Defaults to the last 12 weeks.
    The waist measurement is the most reliable fat-loss indicator — prioritise it
    over scale weight when assessing trajectory."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        start = _parse_date(start_date) or _default_start(12)
        rows = data.body_metrics_dicts(db, user.id, start, _parse_date(end_date))
        return mcp_ok(rows, user_id=user.id, context_note="Last 12 weeks unless a range was specified.")


@mcp_server.tool()
def get_recovery_logs(ctx: Context, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Return energy, sleep, and soreness history. Use it to spot under-recovery
    before adjusting training load. Defaults to the last 4 weeks."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        start = _parse_date(start_date) or _default_start(4)
        rows = data.recovery_logs_dicts(db, user.id, start, _parse_date(end_date))
        return mcp_ok(rows, user_id=user.id)


@mcp_server.tool()
def get_behaviour_flags(ctx: Context, start_date: str | None = None, end_date: str | None = None) -> dict:
    """Return slip / behaviour pattern logs (late-night eating, cravings, good
    choices, etc). Surface patterns gently — never present these back as counts."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        start = _parse_date(start_date) or _default_start(4)
        rows = data.behaviour_flags_dicts(db, user.id, start, _parse_date(end_date))
        return mcp_ok(rows, user_id=user.id)


@mcp_server.tool()
def get_injury_log(ctx: Context) -> dict:
    """Return injury and discomfort records. Check this before programming or
    progressing any lift that loads a flagged area."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(data.injury_logs_dicts(db, user.id), user_id=user.id)


@mcp_server.tool()
def get_checkin_history(ctx: Context) -> dict:
    """Return previous check-in summaries with weight, waist, sessions, and the
    targets you set. Read this at the start of a weekly check-in for continuity."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(data.checkin_history_dicts(db, user.id), user_id=user.id)


@mcp_server.tool()
def get_lift_progression(ctx: Context, exercise_name: str) -> dict:
    """Return the weight × reps time-series for a single named exercise. Use it to
    decide whether to progress, hold, or deload that lift."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(
            data.lift_progression_dicts(db, user.id, exercise_name),
            user_id=user.id,
            context_note=f"Progression for '{exercise_name}'.",
        )


@mcp_server.tool()
def get_non_scale_victories(ctx: Context) -> dict:
    """Return user-logged non-scale victories (energy, fit of clothes, stamina).
    Reference these to reinforce progress that the scale doesn't show."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        return mcp_ok(data.nsv_dicts(db, user.id), user_id=user.id)


# =====================================================================
# Write tools
# =====================================================================
@mcp_server.tool()
def update_programme(ctx: Context, programme: dict) -> dict:
    """Create or replace the user's active programme. ``programme`` must match the
    FitVise programme schema (name, total_weeks, current_week, sessions[] with
    exercises[]). The payload is validated structurally; invalid writes return
    code VALIDATION_FAILED with a reason so you can correct and retry. The previous
    programme is archived, not deleted."""
    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        try:
            prog = write_programme(db, user_id=user.id, payload=programme)
        except ProgrammeValidationError as e:
            return mcp_err(str(e), "VALIDATION_FAILED")
        triggers.workout_updated(db, user.id, prog.name)
        return mcp_ok(
            {"programme_id": prog.id, "name": prog.name, "current_week": prog.current_week},
            user_id=user.id,
        )


@mcp_server.tool()
def complete_onboarding(ctx: Context) -> dict:
    """Mark onboarding complete (the lock-in handshake): sets onboarding_completed_at
    and unlocks app features. Call this only after the profile is captured and the
    first programme is written via update_programme."""
    from app.core.onboarding import compute_onboarding_status
    from app.db.base import utcnow

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        status = compute_onboarding_status(user)
        if status.missing_fields:
            return mcp_err(
                f"Cannot complete onboarding; missing: {', '.join(status.missing_fields)}",
                "VALIDATION_FAILED",
            )
        if user.onboarding_completed_at is None:
            user.onboarding_completed_at = utcnow()
            db.commit()
            db.refresh(user)
        return mcp_ok(compute_onboarding_status(user).model_dump(mode="json"), user_id=user.id)


@mcp_server.tool()
def write_checkin_summary(
    ctx: Context,
    date: str,
    ai_summary: str,
    weight_at_checkin: float | None = None,
    waist_at_checkin: float | None = None,
    sessions_planned: int | None = None,
    sessions_completed: int | None = None,
) -> dict:
    """Persist your weekly check-in summary so the user sees it in the app. Provide
    the check-in date (YYYY-MM-DD), your written summary, and the week's numbers."""
    from app.models.checkin import CheckInRecord
    from app.models.programme import Programme

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        active = (
            db.query(Programme)
            .filter(Programme.user_id == user.id, Programme.status == "active")
            .first()
        )
        rec = CheckInRecord(
            user_id=user.id,
            date=dt.date.fromisoformat(date),
            weight_at_checkin=weight_at_checkin,
            waist_at_checkin=waist_at_checkin,
            sessions_planned=sessions_planned,
            sessions_completed=sessions_completed,
            ai_summary=ai_summary,
            programme_id=active.id if active else None,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        triggers.checkin_summary_written(db, user.id)
        return mcp_ok({"checkin_id": rec.id}, user_id=user.id)


@mcp_server.tool()
def set_weekly_targets(
    ctx: Context,
    week_start_date: str,
    weight_target: float | None = None,
    waist_target: float | None = None,
    behavioural_goal: str | None = None,
    training_goal: str | None = None,
) -> dict:
    """Set next-week goals (weight/waist target, a behavioural goal, and a training
    goal). week_start_date is YYYY-MM-DD. The user sees these on their journal."""
    from app.models.checkin import WeeklyTarget

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        target = WeeklyTarget(
            user_id=user.id,
            week_start_date=dt.date.fromisoformat(week_start_date),
            weight_target=weight_target,
            waist_target=waist_target,
            behavioural_goal=behavioural_goal,
            training_goal=training_goal,
            set_by="ai",
        )
        db.add(target)
        db.commit()
        db.refresh(target)
        triggers.weekly_targets_set(db, user.id)
        return mcp_ok({"target_id": target.id}, user_id=user.id)


@mcp_server.tool()
def add_exercise_substitution(
    ctx: Context, original_exercise: str, substitute_exercise: str, reason: str | None = None
) -> dict:
    """Record an exercise substitution with a reason (e.g. swapping a movement that
    aggravates a flagged joint). The user sees the substitution on their programme."""
    from app.models.programme import Programme
    from app.models.substitution import ExerciseSubstitution

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        active = (
            db.query(Programme)
            .filter(Programme.user_id == user.id, Programme.status == "active")
            .first()
        )
        sub = ExerciseSubstitution(
            user_id=user.id,
            programme_id=active.id if active else None,
            original_exercise=original_exercise,
            substitute_exercise=substitute_exercise,
            reason=reason,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return mcp_ok({"substitution_id": sub.id}, user_id=user.id)


# =====================================================================
# Prompts (server-defined workflow templates → slash commands)
# =====================================================================
@mcp_server.prompt()
def onboard() -> str:
    """Run FitVise onboarding: capture the profile (incl. training modality),
    propose and lock a first programme."""
    return (
        "You are the user's FitVise coach running onboarding.\n"
        "1. Call get_onboarding_status to see what's missing.\n"
        "2. Ask one question at a time to fill the missing profile fields "
        "(goal, training modality, days/week, current weight, injuries).\n"
        "3. Propose a first programme and, once agreed, call update_programme with it.\n"
        "4. Finish by calling complete_onboarding.\n"
        "Be warm, concise, and never overwhelm with dense forms."
    )


@mcp_server.prompt()
def weekly_checkin() -> str:
    """Conduct the weekly check-in and record the summary + next-week targets."""
    return (
        "Run the user's FitVise weekly check-in.\n"
        "1. Call get_checkin_history, get_workout_logs, and get_body_metrics for context.\n"
        "2. Assess progress — prioritise the waist trend over scale weight.\n"
        "3. Write a short, encouraging summary and call write_checkin_summary.\n"
        "4. Call set_weekly_targets with next week's weight/behaviour/training goals."
    )


@mcp_server.prompt()
def change_workout() -> str:
    """Modify the current programme on the user's request."""
    return (
        "Help the user change their training programme.\n"
        "1. Call get_current_programme to load the active plan.\n"
        "2. Discuss the requested change.\n"
        "3. Call update_programme with the full revised programme (it will be "
        "validated; fix and retry if it returns VALIDATION_FAILED)."
    )


@mcp_server.prompt()
def log_review() -> str:
    """Review recent logs and surface patterns gently."""
    return (
        "Review the user's recent FitVise logs.\n"
        "1. Call get_workout_logs, get_diet_logs, and get_behaviour_flags.\n"
        "2. Identify 2–3 gentle, actionable patterns — wins first, then one nudge.\n"
        "Never present behaviour flags back as raw counts."
    )
