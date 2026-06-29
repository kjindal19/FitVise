# Self-hosting FitVise

FitVise ships as a Docker stack: a FastAPI backend (REST + MCP + OAuth +
notifications), a React PWA frontend, and a database (SQLite or PostgreSQL).

## Prerequisites

- Docker + Docker Compose v2
- A public URL if you want a remote AI client (e.g. claude.ai) to reach your MCP
  endpoint over OAuth (a reverse proxy with TLS in front of the backend).

## 1. Configure

```bash
cp .env.example .env
```

Key variables (full list in `.env.example`):

| Variable | Purpose |
|---|---|
| `FITVISE_SECRET_KEY` | JWT / session signing secret. `openssl rand -hex 32` |
| `FITVISE_AUTH_MODE` | `single_user` \| `multi_user` \| `managed` |
| `FITVISE_BASE_URL` | Public URL (used in MCP + OAuth metadata) |
| `FITVISE_DB_TYPE` | `sqlite` \| `postgres` |
| `FITVISE_DB_URL` | Postgres connection string (compose sets this) |
| `FITVISE_MCP_API_KEY` | Static key for single-user stdio mode only |
| `FITVISE_OAUTH_SIGNING_KEY` | OAuth token signing (multi/managed) |
| `FITVISE_VAPID_PUBLIC_KEY` / `_PRIVATE_KEY` | Web Push keys |

## 2. Choose a deployment mode

### Single-user (simplest)

```ini
FITVISE_AUTH_MODE=single_user
FITVISE_DB_TYPE=sqlite
FITVISE_DB_PATH=/data/fitvise.sqlite3
```

The sole user is auto-provisioned on first boot; no login required. The `db`
(Postgres) service is unused — start just backend + frontend:

```bash
docker compose up --build backend frontend
```

### Multi-user / managed

Keep the defaults (`multi_user`, `postgres`). The first account registered
through the app becomes the admin. MCP connections authenticate per-user via
OAuth 2.1.

```bash
docker compose up --build
```

## 3. First run

On boot the backend runs `app.db.migrate` (creates the schema; provisions the
single user in single-user mode). Watch logs:

```bash
docker compose logs -f backend
```

You should see `migrations complete`, `notification scheduler started`,
`StreamableHTTP session manager started`, and `Application startup complete`.

Verify:

```bash
curl http://localhost:8000/health
```

## 4. Web Push (optional)

Generate a VAPID keypair and put it in `.env`:

```bash
docker compose run --rm backend python -m app.notifications.vapid_gen
```

Restart, then enable push per-device from **Settings** in the app. Notifications
also always appear in the in-app notification center (the bell).

## 5. Database

- **SQLite** runs in WAL mode in the `/data` volume — ideal for one user.
- **PostgreSQL** is the `db` service; the backend waits for it to be healthy.

> Schema changes: the scaffold uses `Base.metadata.create_all`. An `alembic/`
> migration setup is the intended path for production schema evolution.

## 6. Data export & backup

Users can export all their data (Settings → Export JSON / CSV) or via the API
(`GET /api/v1/export/json`, `/csv`). For full-instance backups, snapshot the
Postgres volume (`fitvise_pgdata`) or the SQLite file in `fitvise_appdata`.

## 7. Updating

`docker compose pull && docker compose up -d --build`. The running version is
shown at `GET /health` and in the app footer.
