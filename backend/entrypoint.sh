#!/usr/bin/env bash
# Wait for the database, apply migrations, seed defaults, then start the app.
set -e

echo "[entrypoint] Waiting for database at ${POSTGRES_SERVER:-db}:${POSTGRES_PORT:-5432}..."
python - <<'PY'
import os, time, socket
host = os.getenv("POSTGRES_SERVER", "db")
port = int(os.getenv("POSTGRES_PORT", "5432"))
for attempt in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print("[entrypoint] Database is reachable.")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("[entrypoint] Database not reachable, aborting.")
PY

echo "[entrypoint] Applying Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Seeding permissions, roles and admin user..."
python -m app.db.init_db

if [ "${SEED_SAMPLE_DATA:-false}" = "true" ]; then
  echo "[entrypoint] Seeding demo sample data..."
  python -m app.db.sample_data
fi

echo "[entrypoint] Starting: $*"
exec "$@"
