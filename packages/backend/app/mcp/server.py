"""FitVise MCP server (Streamable HTTP) — the AI coach's read/write interface.

Built on the official MCP Python SDK's FastMCP. Mounted by app.main at /mcp.
Every tool resolves the calling user from the request's bearer token (see
app.mcp.auth) and scopes all queries to that user. Tool descriptions are written
for the AI to read — they double as the coach's instruction manual (PRD §6.4).
"""
from __future__ import annotations

import datetime as dt

from mcp.server.fastmcp import Context, FastMCP

from app.config import settings
from app.db.base import SessionLocal
from app.mcp import data
from app.mcp.auth import FitViseTokenVerifier, MCPAuthError, resolve_user
from app.programme.service import ProgrammeValidationError, write_programme
from app.schemas.common import mcp_err, mcp_ok
from app.notifications import triggers


def _auth_kwargs() -> dict:
    """In multi_user / managed mode, wire OAuth bearer enforcement into the
    transport so unauthenticated clients get 401 + ``WWW-Authenticate`` (RFC 9728)
    and discover the OAuth flow. The challenge points at the Protected Resource
    Metadata served at the app root (see app.main); ``resource_server_url`` is the
    bare instance URL so the well-known path resolves to that existing endpoint
    rather than under the ``/mcp`` mount. Single-user mode adds no transport auth.
    """
    if not settings.is_multi_user:
        return {}
    from mcp.server.auth.settings import AuthSettings

    return {
        "token_verifier": FitViseTokenVerifier(),
        "auth": AuthSettings(
            issuer_url=settings.issuer,
            resource_server_url=settings.base_url.rstrip("/"),
            required_scopes=[],
        ),
    }


mcp_server = FastMCP(
    name="fitvise",
    instructions=(
        "You are the user's personal trainer and nutritionist, and FitVise is the journal "
        "where their plan and history live. Talk like an experienced coach who knows them — "
        "warm, direct, encouraging, never clinical or form-like. Always read the relevant "
        "context first (get_user_profile, get_current_programme, recent logs) before giving "
        "advice. Capture what you learn about them with update_user_profile so it persists. "
        "Use update_programme to author or revise their plan, write_checkin_summary and "
        "set_weekly_targets at check-ins. All data is scoped to the authenticated user."
    ),
    stateless_http=True,
    streamable_http_path="/",
    **_auth_kwargs(),
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
        start = _parse_date(start_date) or _default_start(2)
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
def update_user_profile(
    ctx: Context,
    name: str | None = None,
    age: int | None = None,
    gender: str | None = None,
    height: float | None = None,
    current_weight: float | None = None,
    weight_unit: str | None = None,
    measurement_unit: str | None = None,
    goal_type: str | None = None,
    target_weight: float | None = None,
    target_waist: float | None = None,
    diet_type: str | None = None,
    dietary_restrictions: str | None = None,
    eating_patterns: str | None = None,
    supplements_notes: str | None = None,
    medical_notes: str | None = None,
    training_modality: str | None = None,
    training_days_per_week: int | None = None,
    session_length_preference: int | None = None,
    equipment_available: list[str] | None = None,
    gym_access_type: str | None = None,
    injuries_notes: str | None = None,
    preferences_notes: str | None = None,
) -> dict:
    """Save what you learn about the user to their profile — call this as you gather
    details in conversation so nothing is lost (e.g. right after they tell you their
    age/weight/height, then again after the diet questions). Onboarding cannot be
    completed until the required fields are saved. Only pass the fields you're
    updating; omitted fields are left unchanged.

    Field guidance:
    - gender: 'male' | 'female' | 'other' (used to tailor training/nutrition).
    - height: in cm (or inches if measurement_unit='in'); current_weight/target_weight
      in kg (or lbs if weight_unit='lbs').
    - goal_type: e.g. 'fat_loss' | 'muscle_gain' | 'recomposition' | 'maintenance' |
      'strength' | 'general_fitness'.
    - diet_type: e.g. 'vegetarian' | 'non_vegetarian' | 'eggetarian' | 'vegan' |
      'pescatarian'.
    - dietary_restrictions: allergies, intolerances, foods they avoid.
    - eating_patterns: their relationship with food — foodie, dessert lover, big
      snacker, late-night eater, who they cook for, eats out often, etc.
    - supplements_notes: supplements they take or are interested in.
    - medical_notes: medical conditions / issues relevant to training or diet.
    - training_modality: 'gym' | 'home_bodyweight' | 'walk_run' | 'classes_zumba' |
      'hybrid'.
    - equipment_available: the machines / kit the user can actually train with, as a
      list of short labels (e.g. ['barbell','dumbbells','squat_rack','leg_press',
      'cable_machine','pull_up_bar','resistance_bands','kettlebells','treadmill']).
      Confirm this list back to the user during onboarding so they know which
      exercises may need swapping, and only program movements their equipment
      supports.
    - gym_access_type: e.g. 'full_gym' | 'home_gym' | 'basic_home' | 'bodyweight_only'.
    - injuries_notes: any pain, injuries, or movement limitations to program around.
    Returns the updated onboarding status so you can see what's still missing."""
    from app.core.onboarding import apply_profile_updates, compute_onboarding_status

    updates = {
        "name": name, "age": age, "gender": gender,
        "weight_unit": weight_unit, "measurement_unit": measurement_unit,
        "height": height, "current_weight": current_weight,
        "goal_type": goal_type, "target_weight": target_weight, "target_waist": target_waist,
        "diet_type": diet_type, "dietary_restrictions": dietary_restrictions,
        "eating_patterns": eating_patterns, "supplements_notes": supplements_notes,
        "medical_notes": medical_notes,
        "training_modality": training_modality, "training_days_per_week": training_days_per_week,
        "session_length_preference": session_length_preference,
        "equipment_available": equipment_available, "gym_access_type": gym_access_type,
        "injuries_notes": injuries_notes, "preferences_notes": preferences_notes,
    }

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        user = apply_profile_updates(db, user, updates)
        return mcp_ok(
            {
                "profile": data.profile_dict(user),
                "onboarding": compute_onboarding_status(user).model_dump(mode="json"),
            },
            user_id=user.id,
        )


@mcp_server.tool()
def update_programme(ctx: Context, programme: dict) -> dict:
    """Create or replace the user's active programme. The previous programme is
    archived, not deleted. Invalid writes return code VALIDATION_FAILED with a
    reason — fix and retry.

    ``programme`` shape:
      {
        "name": str, "total_weeks": int, "current_week": int (default 1),
        "goal_type": str,
        "sessions": [
          {
            "session_type": "push|pull|lower|upper|full|walk|run|class|rest|cardio|mobility",
            "label": "Upper A — Push",          # optional display title
            "day_of_week": 0,                    # optional, 0=Mon … 6=Sun
            "week_number": 1,                    # optional, defaults to 1
            "exercises": [
              { "name": str, "sets": int,
                "reps": "10-12",                 # number, range, or text e.g. "30 sec hold"
                "rest_seconds": int, "notes": str }
            ],
            "warmup":   [ {"name": str, "reps": "5 min", "notes": str} ],   # optional
            "cooldown": [ {"name": str, "reps": "30 sec", "notes": str} ]   # optional
          }
        ]
      }

    Only include ``warmup`` / ``cooldown`` when the user actually wants them — the app
    hides those blocks entirely when omitted. ``reps`` and ``notes`` are accepted as
    written; numeric ranges are parsed automatically."""
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
def complete_onboarding(
    ctx: Context,
    name: str | None = None,
    age: int | None = None,
    gender: str | None = None,
    height: float | None = None,
    current_weight: float | None = None,
    goal_type: str | None = None,
    diet_type: str | None = None,
    training_modality: str | None = None,
    training_days_per_week: int | None = None,
    target_weight: float | None = None,
    dietary_restrictions: str | None = None,
    eating_patterns: str | None = None,
    supplements_notes: str | None = None,
    medical_notes: str | None = None,
    injuries_notes: str | None = None,
) -> dict:
    """Mark onboarding complete (the lock-in handshake) and unlock app features.

    You may pass any still-missing profile fields directly here to save and finalise
    in one call — this is the safety net, so if you've collected the details in
    conversation but haven't persisted them yet, include them now. It persists them
    (same as update_user_profile), then completes. If required fields are still
    missing afterwards it returns VALIDATION_FAILED listing them — set those via
    update_user_profile (or re-call this with them) and retry. Call only after the
    first programme is written via update_programme."""
    from app.core.onboarding import apply_profile_updates, compute_onboarding_status
    from app.db.base import utcnow

    updates = {
        "name": name, "age": age, "gender": gender, "height": height,
        "current_weight": current_weight, "goal_type": goal_type, "diet_type": diet_type,
        "training_modality": training_modality, "training_days_per_week": training_days_per_week,
        "target_weight": target_weight, "dietary_restrictions": dietary_restrictions,
        "eating_patterns": eating_patterns, "supplements_notes": supplements_notes,
        "medical_notes": medical_notes, "injuries_notes": injuries_notes,
    }

    with SessionLocal() as db:
        try:
            user = resolve_user(db, _headers(ctx))
        except MCPAuthError as e:
            return mcp_err(str(e), "UNAUTHORIZED")
        if any(v is not None for v in updates.values()):
            user = apply_profile_updates(db, user, updates)
        status = compute_onboarding_status(user)
        if status.missing_fields:
            return mcp_err(
                "Cannot complete onboarding; still missing: "
                f"{', '.join(status.missing_fields)}. Save them via update_user_profile "
                "(or pass them to this tool) and retry.",
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
    """Run FitVise onboarding as a personal trainer: get to know the user
    conversationally, then author and lock their first programme."""
    return (
        "You're the user's new personal trainer and nutritionist, meeting them for the "
        "first time. This is a real intake conversation, not a form — be warm, curious, "
        "and experienced. React to what they say before moving on. Group related "
        "questions so it flows naturally (don't drip one trivial question at a time, and "
        "don't dump a giant questionnaire either).\n\n"
        "Open by introducing yourself and asking what brought them here and what they "
        "want to achieve — get the goal and the 'why' behind it.\n\n"
        "Then move through these stages, roughly one message per stage:\n"
        "  1. THE BASICS, together in one message: age, gender, height, and current "
        "weight (and a target weight if they have one). Frame it as getting the numbers "
        "to tailor everything to them.\n"
        "  2. NUTRITION — get to know how they actually eat. Diet preference "
        "(veg / non-veg / eggetarian / vegan, etc.), any allergies or foods they avoid, "
        "AND their patterns/relationship with food: are they a foodie, a dessert lover, a "
        "big snacker, eat out a lot, cook for family? Be conversational here.\n"
        "  3. HEALTH & SUPPLEMENTS: any medical conditions or issues, and whether they "
        "take or are interested in any supplements.\n"
        "  4. TRAINING: how they like to train (gym, home/bodyweight, walking/running, "
        "classes), how many days a week they can realistically commit, any injuries or "
        "limitations to work around, and whether they'd like warm-ups and cool-downs "
        "included in their sessions. Also ask what equipment / machines they actually "
        "have access to (full gym, a home setup, just dumbbells and bands, bodyweight "
        "only, etc.). Then READ BACK the specific equipment list you understood and have "
        "them confirm it — make clear this is what their exercises will be built around, "
        "so anything they don't have gets swapped out. Save it via equipment_available "
        "(and gym_access_type).\n\n"
        "After EACH stage, immediately call update_user_profile with what you just "
        "learned (age/gender/height/current_weight; diet_type/dietary_restrictions/"
        "eating_patterns; medical_notes/supplements_notes; training_modality/"
        "training_days_per_week/equipment_available/gym_access_type/injuries_notes). Do "
        "NOT batch all saves to the end — persist as you go. Call get_onboarding_status "
        "anytime to see what's left.\n\n"
        "Once you know enough, propose a first programme in plain language, get their "
        "buy-in, then call update_programme — include warmup/cooldown blocks only if they "
        "asked for them. Finally call complete_onboarding to lock it in (you can pass any "
        "fields you haven't saved yet directly to it as a safety net), then tell them how "
        "to start their first session in the app.\n\n"
        "Throughout: confident, specific, and personal. Make them feel coached, not "
        "processed."
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
