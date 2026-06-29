#!/usr/bin/env bash
set -euo pipefail

echo "[fitvise] auth_mode=${FITVISE_AUTH_MODE:-single_user} db_type=${FITVISE_DB_TYPE:-sqlite}"

# Apply database migrations (creates schema on first run).
echo "[fitvise] running migrations..."
python -m app.db.migrate

exec "$@"
