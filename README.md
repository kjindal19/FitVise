# FitVise

**Open-source persistent data + logging layer for an AI fitness coach.**

FitVise is your fitness journal. The *coaching* happens in your own AI client
(Claude Desktop, claude.ai, or any MCP-compatible LLM), which connects to FitVise
over the **Model Context Protocol (MCP)** to read and write your programme, logs,
metrics, and progress. **FitVise itself never calls an LLM** — all intelligence
flows through your own AI session.

> Renamed from *CoachMCP*. The `FITVISE_` env prefix reflects the current name.

---

## What's in the box

| Layer | Tech | Notes |
|---|---|---|
| **Backend** | Python · FastAPI | REST API (`/api/v1`), MCP server (`/mcp`, Streamable HTTP), OAuth 2.1 AS, notification scheduler |
| **Frontend** | React + TypeScript · Vite · Tailwind v4 | Installable **PWA**, offline logging, mobile-first, light/dark |
| **Database** | SQLite *or* PostgreSQL | SQLite for single-user; Postgres for multi-user/managed |
| **Notifications** | Web Push (VAPID) + in-app center | Daily reminders, missed-workout nudges, programme/check-in events |

Three deployment modes share one codebase, selected by `FITVISE_AUTH_MODE`:

1. **`single_user`** — zero-config, SQLite, static MCP key. One person, local.
2. **`multi_user`** — Postgres, username/password web login, **per-user OAuth 2.1** for MCP.
3. **`managed`** — same as multi-user, operator-run (billing/abuse controls out of scope here).

---

## Quick start (Docker)

```bash
cp .env.example .env          # then edit FITVISE_SECRET_KEY etc.
docker compose up --build
```

- App (PWA): http://localhost:5173
- API + docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/health
- MCP endpoint: http://localhost:8000/mcp

Default `.env` runs **multi_user on PostgreSQL**. For the simplest single-person
setup, set `FITVISE_AUTH_MODE=single_user` and `FITVISE_DB_TYPE=sqlite` (then the
`db` service is optional).

### Enable Web Push notifications

```bash
docker compose run --rm backend python -m app.notifications.vapid_gen
```

Paste the printed `FITVISE_VAPID_PUBLIC_KEY` / `FITVISE_VAPID_PRIVATE_KEY` into
`.env`, restart, then in the app go to **Settings → Enable push on this device**.

---

## Repository layout

```
fitvise/
├── packages/
│   ├── backend/     # FastAPI: REST + MCP + OAuth AS + notifications
│   └── frontend/    # React PWA
├── docker-compose.yml
├── .env.example
├── docs/
│   ├── self-hosting.md
│   ├── mcp-setup.md      # connect an AI client to FitVise
│   └── api-reference.md
└── README.md
```

See [docs/self-hosting.md](docs/self-hosting.md) to deploy and
[docs/mcp-setup.md](docs/mcp-setup.md) to connect your AI client.

---

## Connecting your AI coach

1. Self-host (above) or sign in to a managed instance.
2. In your AI client's connector settings, add a custom MCP connector at
   `https://<your-host>/mcp`.
3. **multi_user/managed:** authorize via OAuth (PKCE). **single_user:** use the
   stdio config + static key from setup.
4. Run the slash command `/mcp__fitvise__onboard` (or paste the copy-paste
   starter prompt the app shows) to begin.

Full walkthrough: [docs/mcp-setup.md](docs/mcp-setup.md).

---

## Status

This is an initial full-stack scaffold built against the
[Technical PRD](PRD/PRD_Technical_FitVise.md). Core data model, REST CRUD, all 18
MCP tools + 4 prompts, the OAuth authorization-code/PKCE flow, the notification
service, and the PWA shell are in place and run under Docker. Areas explicitly
marked for follow-up in code comments: Alembic migrations (currently
`create_all` bootstrap), OAuth rate-limiting/CIMD, richer per-screen UI, and
deeper offline-sync conflict handling.

## Licence

MIT or Apache 2.0 — TBD by project owner (PRD §11.1).
