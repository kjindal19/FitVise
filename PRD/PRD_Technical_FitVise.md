# FitVise — Technical Requirements Document
**Version:** 0.2 — For Engineering Team Review
**Prepared by:** Product (via AI Coach Specification)
**Status:** Draft — Updated after first architecture sync

> **Naming note:** This product was previously drafted as *CoachMCP* and has been renamed to **FitVise**.
> All product names and the `FITVISE_` env-var prefix reflect the new name.

---

## 1. Project Overview

FitVise is an **open-source** web application that acts as the **persistent data and logging layer** for an AI-powered fitness coaching experience. The AI layer is the user's own MCP client — Claude (via claude.ai / Claude Desktop) or any other MCP-compatible LLM. The client connects to a FitVise MCP server to read and write user data — workout programmes, logs, metrics, and progress history.

**Key constraint:** There is no LLM API integration in the app itself. The app does not call any LLM. All intelligence flows through the user's own AI session via MCP.

**Deployment model — three first-class modes (all v1, user's choice):**
1. **Self-host, single-user** — zero-config default. SQLite, simple token / static-key auth. Ideal for one person running it locally (Docker or bare Node/Python).
2. **Self-host, multi-user** — a shared instance (e.g., a coach hosting for clients). PostgreSQL, per-user OAuth 2.1 for the MCP connection, full row-level data isolation.
3. **Managed hosted (paid subscription)** — a multi-tenant FitVise-operated instance. Same codebase as self-host multi-user, with the operator running the OAuth Authorization Server, billing, and abuse controls.

The codebase is a single open-source project; the mode is selected by configuration. Single-user self-host remains the simplest path; multi-user/OAuth is **supported in v1, not deferred**.

---

## 2. High-Level Architecture

```
┌───────────────────────────────────────────────────┐
│                   User's Browser                   │
│              FitVise Web Frontend                  │
│         (React / Vue / SvelteKit — TBD)           │
└─────────────────────┬─────────────────────────────┘
                      │ REST / GraphQL
┌─────────────────────▼─────────────────────────────┐
│               FitVise Backend API                  │
│           (Node.js / Python — TBD)                │
│                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │   App API    │  │  MCP Server  │  │  OAuth   │ │
│  │  (CRUD ops)  │  │ (Streamable  │  │ AS / PRM │ │
│  │              │  │   HTTP)      │  │ (multi)  │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘ │
└─────────┼─────────────────┼───────────────┼───────┘
          │                 │               │
┌─────────▼─────────────────▼───────────────▼───────┐
│                    Database                         │
│           (SQLite for single-user /                 │
│            PostgreSQL for multi-user/managed)       │
└─────────────────────────────────────────────────────┘

         AI Client (Claude.ai / Claude Desktop / any MCP LLM)
                        │  MCP over Streamable HTTP (remote)
                        │  OAuth 2.1 per-user (multi-user/managed)
                        │  — or stdio + static key (local single-user)
                        ▼
                 FitVise MCP Server
```

---

## 3. Core Technical Components

### 3.1 Frontend Application

**Responsibilities:**
- Display workout programme (week, session, exercise level)
- Provide all logging interfaces (workout sets, diet, metrics, recovery, flags)
- Display progress charts and history
- Surface the **onboarding entry point** (the onboarding *conversation* happens in the LLM — see §3.5) plus a fallback in-app profile form and a read-only profile display
- Expose settings, MCP connection / "Add to your AI client" flow, and data export

**Requirements:**
- Mobile-first, responsive
- PWA support strongly preferred (installable, works offline for logging)
- Offline logging with sync on reconnect — critical for gym environments with poor connectivity
- No external analytics, tracking, or telemetry by default (self-hosted privacy commitment)
- Framework decision deferred to engineering team; must produce a single deployable build artifact

**Offline Behaviour:**
- Workout log, diet log, recovery log, and metrics log must function offline
- Programme view must be available offline (cached on first load)
- Progress charts can be gracefully unavailable offline
- Sync conflict strategy: last-write-wins with timestamp; no complex merge required in v1

---

### 3.2 Backend API

**Responsibilities:**
- All CRUD operations for the data model (see Section 4)
- Authentication and user session management (app web sessions)
- Serve the MCP server endpoint (Streamable HTTP)
- Host the OAuth 2.1 Authorization Server + Protected Resource Metadata for multi-user/managed modes
- Handle data export

**Requirements:**
- REST API is preferred for simplicity of self-hosting and debugging; GraphQL optional
- Stateless where possible
- All endpoints must require authentication except health check and OAuth discovery documents
- **Rate limiting, token revocation, and refresh-token rotation are required for multi-user and managed modes** (see §3.6). They may be disabled in single-user self-host.

**Language/Framework:** Engineering team's choice. Suggested candidates: Node.js (Express / Fastify) or Python (FastAPI). Must be containerisable and ship a mature MCP SDK + OAuth library.

---

### 3.3 MCP Server

This is the most architecturally critical component. It is what allows the AI client to act as a coach with full context.

**Transport:** MCP over **Streamable HTTP** for remote connections (the modern standard; a single `/mcp` endpoint serving both POST and GET, with `MCP-Protocol-Version` and `MCP-Session-Id` headers; SSE survives only as an optional response framing). The legacy standalone **HTTP+SSE transport is deprecated** and not targeted. **stdio** is supported only for local single-user setups (e.g., Claude Desktop with the server on the same machine) and for development.

**MCP Server Behaviour:**
- The MCP server is essentially a read/write interface into the FitVise database, **always scoped to the authenticated user**
- It must return structured, well-labelled data so the AI can interpret it without ambiguity
- All MCP tools must include clear descriptions that the AI can use for tool selection

**Required MCP Tools:**

| Tool Name | Description | Returns |
|---|---|---|
| `get_user_profile` | Full user profile: name, age, weight, height, goal, diet type, training modality, injuries, days available | JSON profile object |
| `get_onboarding_status` | Whether onboarding is complete; which fields are still missing | Status object + missing-field list |
| `get_current_programme` | Active programme: week number, current training split, phase | Programme metadata + this week's sessions |
| `get_session_plan` | Specific session by day/type: all exercises, sets, reps, notes | Session object with exercise array |
| `get_workout_logs` | All logged workout sessions (filterable by date range) | Array of session logs with sets × reps × weight |
| `get_diet_logs` | Meal logs (filterable by date range) | Array of daily diet logs with meal entries and flags |
| `get_body_metrics` | Weight and measurement history (filterable by date range) | Array of metric snapshots with timestamps |
| `get_recovery_logs` | Energy, sleep, soreness history | Array of recovery entries |
| `get_behaviour_flags` | Slip/behaviour pattern logs | Array of flagged events with timestamps |
| `get_injury_log` | Injury and discomfort records | Array of injury entries |
| `get_checkin_history` | Previous check-in summaries | Array of check-in records |
| `get_lift_progression` | Progress for a specific exercise over time | Time-series of weight × reps for named exercise |
| `get_non_scale_victories` | User-logged wins | Array of NSV entries |
| `update_programme` | Write a new or modified programme (AI calls this when changing workouts). **Validated against the programme schema before persisting.** | Confirmation + updated programme |
| `complete_onboarding` | Marks onboarding complete (the lock-in handshake): persists profile, sets `onboarding_completed_at`, unlocks app features | Confirmation + onboarding status |
| `write_checkin_summary` | AI writes its check-in summary to the app after a session | Confirmation |
| `set_weekly_targets` | AI sets next-week goals (weight target, behavioural goal, training goal) | Confirmation |
| `add_exercise_substitution` | AI flags an exercise substitution with reason | Confirmation |

**MCP Prompts (server-defined workflow templates):**
The conversational workflows run **inside the LLM**, invoked as MCP **Prompts** that surface in the client as slash commands (e.g. `/mcp__fitvise__onboard`). Each prompt template instructs the AI to fetch the relevant context via read tools first (the AI has no cross-session memory — all continuity comes from MCP reads).

| Prompt | Purpose | First actions it instructs |
|---|---|---|
| `onboard` | Run onboarding, capture profile incl. training modality, propose & lock a programme | `get_onboarding_status`, then on completion `update_programme` + `complete_onboarding` |
| `weekly_checkin` | Conduct the weekly check-in | `get_checkin_history`, `get_workout_logs`, `get_body_metrics`, then `write_checkin_summary` + `set_weekly_targets` |
| `change_workout` | Modify the current programme on request | `get_current_programme`, then `update_programme` |
| `log_review` | Review recent logs and surface patterns | `get_workout_logs`, `get_diet_logs`, `get_behaviour_flags` |

> **Fallback:** MCP Prompt / slash-command surfacing is robust in Claude Desktop/Code and should be
> verified on claude.ai web. Where prompts are unavailable (or on other MCP clients), the app provides
> **equivalent copy-paste starter prompts** users can paste into their AI session. The app cannot inject
> text into the AI session itself.

**MCP Context Strategy:**
- When the AI calls `get_current_programme`, it should receive a compact but complete summary — programme phase, week number, remaining weeks, and this week's sessions
- When the AI calls `get_workout_logs`, the default should return the last 4 weeks unless a range is specified — not all-time (to avoid context bloat)
- All timestamps must be ISO 8601 with timezone

**MCP Authentication:**
- **Remote, multi-user and managed modes — OAuth 2.1 per user (required):**
  - Authorization-code flow with **PKCE (`S256`)** and per-user consent. The user clicks "Connect" in their AI client and authorizes against their FitVise account; the client manages token storage and refresh.
  - The MCP server publishes **Protected Resource Metadata** (RFC 9728) at `/.well-known/oauth-protected-resource` and **Authorization Server Metadata** at `/.well-known/oauth-authorization-server`, advertising `"code_challenge_methods_supported": ["S256"]`.
  - Client registration via **Dynamic Client Registration (RFC 7591)** and/or **Client ID Metadata Documents (CIMD)**.
  - Every MCP tool call carries the user's access token; the server resolves **`token → user_id`** and scopes **every** query to that user. This is what enforces multi-tenant isolation.
- **Single-user local (stdio) mode:** a simple static API key generated at setup remains acceptable, since there is exactly one user and no remote exposure.
- **Important:** Static API keys and tokens embedded in the connector URL are **not supported by claude.ai remote connectors** — do not rely on them for the remote/multi-user path.

---

### 3.4 Programme Engine

**Responsibilities:**
- Store and serve structured workout programmes
- Handle programme phases (e.g., Week 1–4, 5–8, 9–12)
- Support AI-authored programme updates (via MCP write tools), **validating structure on write**
- Track which session falls on which day based on user's schedule and chosen training modality

**Programme Data Model (conceptual):**
```
Programme
  ├── metadata: name, total_weeks, current_week, phase, goal_type, status
  ├── phases: array of phase objects
  │     └── Phase: week_range, focus, intensity_label
  └── sessions: array of session definitions
        └── Session: type (push/pull/lower/full/walk/run/class), day_of_week, exercises[]
              └── Exercise: name, sets, reps_range, rest_seconds, notes, substitutes[]
```

**Important:** The AI is the author of programme content. The app stores, **validates**, and serves it. The app does not generate or interpret programming logic — that is the AI's domain — but it **must reject structurally invalid writes** (see §7) with a clear MCP error so the AI can self-correct.

---

## 4. Data Model

### 4.1 Core Entities

**User**
```
id, name, age, email (optional), created_at, onboarding_completed_at (nullable)
weight_unit (kg/lbs), measurement_unit (cm/in)
```

**UserProfile** (onboarding data)
```
user_id, current_weight, height, goal_type, target_weight,
target_waist, diet_type, dietary_restrictions, training_days_per_week,
training_modality (enum: gym | home_bodyweight | walk_run | classes_zumba | hybrid),
preferred_activities (JSON array), equipment_available (JSON array),
session_length_preference, gym_access_type, injuries_notes, preferences_notes, updated_at
```

**Programme**
```
id, user_id, name, total_weeks, current_week, phase_count, status (active/archived/draft),
created_at, updated_at, created_by (ai / import / manual)
```

**ProgrammeSession**
```
id, programme_id, week_number, day_of_week, session_type,
estimated_duration_minutes, notes
```

**Exercise**
```
id, session_id, name, order_index, sets, reps_min, reps_max,
rest_seconds, form_notes, substitutes (JSON array of exercise names)
```

**WorkoutLog**
```
id, user_id, session_id (nullable — user may log ad hoc), date,
started_at, completed_at, notes
```

**WorkoutSetLog**
```
id, workout_log_id, exercise_name, set_number,
weight, reps, is_personal_best, logged_at
```

**DietLog**
```
id, user_id, date, meal_slot (morning/afternoon/evening/night),
description (free text), protein_quality (high/none/mixed),
flags (JSON array), logged_at
```

**BodyMetrics**
```
id, user_id, logged_at, weight, waist_cm, hip_cm (nullable),
chest_cm (nullable), left_arm_cm (nullable), right_thigh_cm (nullable),
body_fat_pct (nullable), notes
```

**RecoveryLog**
```
id, user_id, date, energy_level (1–5), sleep_hours,
soreness_level (none/mild/significant), soreness_location (nullable),
stress_level (1–3), logged_at
```

**BehaviourFlag**
```
id, user_id, date, flag_type (enum), note (nullable), logged_at
```

Flag types: `late_night_eating`, `sugar_craving`, `skipped_session`,
`stress_eating`, `emotional_eating`, `overate_at_meal`, `good_choice_moment`

**InjuryLog**
```
id, user_id, date, body_area, injury_type (pain/discomfort/stiffness/swelling),
severity (1–5), context (during_workout/after_workout/unrelated),
note (nullable), logged_at
```

**CheckInRecord**
```
id, user_id, date, weight_at_checkin, waist_at_checkin,
sessions_planned, sessions_completed,
ai_summary (text), targets_next_week (JSON), created_at
```

**NonScaleVictory**
```
id, user_id, date, description, logged_at
```

**WeeklyTarget**
```
id, user_id, week_start_date, weight_target (nullable),
waist_target (nullable), behavioural_goal (text),
training_goal (text), set_by (ai/user), created_at
```

### 4.2 OAuth Entities (multi-user / managed modes)
*Required only when OAuth is enabled; absent in single-user self-host. May be owned by an embedded Authorization Server library rather than hand-rolled tables.*
```
OAuthClient   : id, client_id, registration_type (dcr/cimd/preconfigured),
                redirect_uris (JSON), created_at
OAuthGrant    : id, user_id, client_id, scopes (JSON), code_challenge_method,
                issued_at, expires_at, revoked_at (nullable)
OAuthToken    : id, grant_id, user_id, access_token_hash, refresh_token_hash,
                scopes (JSON), expires_at, rotated_from (nullable), revoked_at (nullable)
```

---

## 5. Authentication & Multi-User

FitVise supports three modes on one codebase, selected by configuration.

### 5.1 Self-Hosted Single User
- Simple token-based auth with a setup wizard that generates credentials
- MCP via **stdio + a generated static API key** (local only)
- No email required; no external auth dependencies
- Session token stored in local storage or cookie

### 5.2 Self-Hosted Multi-User
- App web login: username + password, bcrypt hashed; JWT-based web sessions
- **MCP connection: per-user OAuth 2.1** (see §3.3) — this is how the AI client identifies the user
- Each user's data is fully isolated at the database query level, enforced by the resolved `user_id` from the OAuth token (no shared data except optionally coach-defined templates)
- Admin role for the instance owner (can see all users, manage accounts)

### 5.3 Managed Hosted (Paid Subscription)
- Same multi-tenant architecture as §5.2, operated by FitVise
- The operator runs the OAuth Authorization Server, billing/subscription, and abuse controls (§3.6)
- Optional social sign-in (Google, etc.) for the app login layer; the MCP path remains OAuth 2.1 per-user

---

## 6. MCP Server — Implementation Detail

### 6.1 Transport
- **Streamable HTTP (primary, remote):** single `/mcp` endpoint handling POST and GET, with `MCP-Protocol-Version` and `MCP-Session-Id` headers and Origin validation. This is the modern MCP remote transport and what claude.ai custom connectors expect.
- **stdio (local single-user / dev only):** for users running their AI client with a local MCP server on the same machine.
- The legacy standalone **HTTP+SSE transport is deprecated** and not a target.

### 6.2 Tool Response Format
All MCP tool responses must be structured JSON with consistent envelope:
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "user_id": "...",
    "fetched_at": "2026-06-28T10:00:00Z",
    "context_note": "Last 4 weeks of data returned. Specify date range for more."
  }
}
```

Error responses:
```json
{
  "success": false,
  "error": "...",
  "code": "NOT_FOUND | UNAUTHORIZED | INVALID_PARAMS | VALIDATION_FAILED"
}
```

### 6.3 Context Efficiency
The AI has a finite context window. MCP tool responses must be designed to be informative but compact:
- Diet logs: return meal descriptions only, not full metadata per entry
- Workout logs: return exercise name + weight × reps per set, not full timestamps per set
- Programme: return current week's sessions in full; reference past weeks only by summary
- All tools should support a `summary` parameter that returns a compact view vs. full detail

### 6.4 MCP Tool & Prompt Descriptions
Every MCP tool **and prompt** must include a well-written description that the AI reads to determine when and how to use it. These descriptions are as important as the logic itself — they are the AI's instruction manual for the app.

Example:
```
Tool: get_body_metrics
Description: "Returns the user's body weight and measurement history.
Call this during check-ins, when the user asks about their progress,
or when you need to assess fat loss trajectory. Default returns last
12 weeks. Use the start_date/end_date params to scope to a specific
period. The waist_cm field is the most reliable fat loss indicator —
prioritise it over weight in your assessment."
```

---

## 7. Programme Write, Validation & Versioning

**Validation on write.** When the AI calls `update_programme`, the app validates the payload against the programme schema (required fields, types, sane ranges). Invalid writes are rejected with `code: VALIDATION_FAILED` and a human-readable reason so the AI can correct and retry. The app validates *structure*, not coaching quality.

**Storage decision (resolves Open Question #6):** the programme is stored as the **AI-authored JSON, validated against a schema**, with a few **indexed columns** projected out for querying (`current_week`, `status`, `user_id`, `created_at`). This keeps writes simple from the AI side while remaining queryable from the app side.

**Versioning.** When the AI modifies a programme:
- The existing programme is **archived** (`status = archived`), not deleted
- A new programme version is created with `created_by = ai` and a timestamp
- The `CheckInRecord` for that week references the new programme version
- The user can view previous programme versions from the UI (read-only)

This ensures a complete audit trail of all coaching decisions.

---

## 8. Data Export

Users must be able to export all their data at any time. Two formats:

**JSON Export:** Full fidelity, all entities, all fields. Intended for re-import or migration.

**CSV Export:** One file per entity type (metrics, workouts, diet, etc.) for spreadsheet analysis.

Export must be triggerable from the UI and optionally via a direct API endpoint (for power users / scripting).

No data is ever deleted without explicit user action. Soft-delete with a `deleted_at` field preferred.

---

## 9. Deployment & Self-Hosting

### 9.1 Docker
- Single `docker-compose.yml` that starts the full stack (backend + frontend + database)
- Environment variables for all configuration (no hardcoded secrets)
- Default database: SQLite (zero-dependency, single-file — ideal for single-user self-host)
- Swap to PostgreSQL via env var for multi-user or managed deployments

### 9.2 Environment Configuration
Required env vars:
```
FITVISE_SECRET_KEY          # JWT / session signing secret
FITVISE_AUTH_MODE           # single_user | multi_user | managed
FITVISE_MCP_API_KEY         # Static key for single-user stdio mode only
FITVISE_OAUTH_ISSUER_URL    # OAuth issuer / base URL (multi_user, managed)
FITVISE_OAUTH_SIGNING_KEY   # Token signing key (multi_user, managed)
FITVISE_DB_TYPE             # sqlite | postgres
FITVISE_DB_PATH             # Path for SQLite file (if sqlite)
FITVISE_DB_URL              # Connection string (if postgres)
FITVISE_PORT                # Default: 3000
FITVISE_BASE_URL            # Public URL (used in MCP connection instructions + OAuth metadata)
```

### 9.3 Setup Wizard
On first run (empty database):
- Guided setup wizard in the browser
- Selects the auth mode; generates `FITVISE_SECRET_KEY`, and either `FITVISE_MCP_API_KEY` (single-user) or OAuth signing material (multi-user/managed) if not provided
- Creates first user / admin account
- Displays MCP connection instructions: for single-user, the static key + stdio config; for multi-user/managed, the "Add FitVise" / OAuth connect URL and discovery endpoints

### 9.4 Updates
- Version number visible in UI footer and API health endpoint
- Changelog linked in UI
- No auto-update (self-hosted); update instructions in docs

---

## 10. Performance Requirements

| Metric | Target |
|---|---|
| Page load (first meaningful paint) | < 2 seconds on 4G |
| Workout log save | < 500ms |
| MCP tool response | < 1 second (db read) / < 2 seconds (complex query) |
| Progress chart render | < 1 second (up to 52 weeks of data) |
| Offline log sync on reconnect | < 5 seconds for up to 50 queued entries |

---

## 11. Open Source Considerations

### 11.1 Licence
Suggest MIT or Apache 2.0. To be confirmed by project owner.

### 11.2 Repository Structure (suggested)
```
fitvise/
├── packages/
│   ├── frontend/       # Web app
│   ├── backend/        # API + MCP server + OAuth AS
│   └── shared/         # Type definitions, constants
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── self-hosting.md
│   ├── mcp-setup.md    # How to connect an AI client to FitVise
│   └── api-reference.md
└── README.md
```

### 11.3 MCP Setup Documentation
This is the most important piece of end-user documentation. It must walk a non-technical user through:
1. Finding their FitVise instance URL after self-hosting (or signing in to the managed instance)
2. Opening their AI client's connector settings (e.g., claude.ai)
3. Adding FitVise as a custom connector
4. Completing the OAuth connect/consent (multi-user/managed) or pasting the stdio config + key (single-user)
5. Verifying the connection (suggested test prompt) and finding the FitVise MCP prompts / copy-paste starters

### 11.4 Contribution Guidelines
- All MCP tool **and prompt** descriptions must be reviewed for clarity before merge (they affect AI behaviour directly)
- Database schema changes must include a migration file
- No LLM vendor dependencies in the codebase

---

## 12. Out of Scope for v1

- Push notifications (no backend push infrastructure)
- Native mobile apps (PWA handles mobile use cases for v1)
- Social features (sharing, leaderboards, friend connections)
- Dedicated coach-to-client management UX (multi-user is supported; a bespoke coach console is not)
- Wearable / fitness tracker integrations (Garmin, Apple Watch, etc.)
- In-app AI responses (all AI is via the user's external MCP session)
- Billing/subscription UX is required for the managed tier but the **payment processor integration**
  is tracked separately from the core app v1

---

## 13. Open Questions for Engineering Team

1. **Frontend framework:** React, Vue, or SvelteKit (all viable PWA paths; SvelteKit has the simplest self-hosting story).
2. **MCP SDK maturity:** Confirm the chosen language's MCP SDK fully supports Streamable HTTP + the OAuth/PRM discovery flow. *(Transport direction resolved: Streamable HTTP, SSE deprecated.)*
3. **SQLite concurrency:** For single-user self-hosting, SQLite is ideal. Is WAL mode sufficient for light multi-user, or do we always require PostgreSQL above single-user?
4. **Offline sync conflict resolution:** Last-write-wins is the v1 choice. Revisit only if simultaneous multi-device offline logging proves problematic.
5. **MCP tool granularity:** Keep `get_workout_logs` / `get_diet_logs` as filterable single tools, or add narrower convenience tools? (Leaning filterable single tools.)
6. **Programme storage format:** *Resolved* — AI-authored JSON validated against a schema + indexed columns (see §7).
7. **Health check / status endpoint:** What should `/health` return? Proposed: app version, DB connectivity, MCP server status, OAuth discovery reachable.
8. **OAuth AS build vs. integrate:** Build the Authorization Server in-house, or front it with an existing OSS IdP that already provides DCR/PKCE/metadata? Affects multi-user/managed effort most.
9. **Versioning API:** Version the REST API from day one (`/api/v1/...`) to avoid breaking self-hosters on updates.

---

*Document prepared for internal engineering review. Updated to reflect the first architecture sync: three deployment modes, per-user OAuth 2.1 for multi-user/managed MCP, Streamable HTTP transport, MCP Prompts with copy-paste fallback, and the onboarding completion handshake.*
