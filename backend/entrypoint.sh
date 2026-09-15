#!/bin/sh
set -e

echo "Waiting for database..."
python - <<'PY'
import os, time
import psycopg

host = os.environ.get("POSTGRES_HOST", "db")
port = os.environ.get("POSTGRES_PORT", "5432")
name = os.environ.get("POSTGRES_DB", "call_intelligence")
user = os.environ.get("POSTGRES_USER", "postgres")
password = os.environ.get("POSTGRES_PASSWORD", "postgres")

for attempt in range(60):
    try:
        with psycopg.connect(
            host=host, port=port, dbname=name, user=user, password=password, connect_timeout=3
        ) as conn:
            conn.execute("SELECT 1")
        print("Database is ready.")
        break
    except Exception as exc:
        print(f"DB not ready ({attempt + 1}/60): {exc}")
        time.sleep(2)
else:
    raise SystemExit("Database did not become ready in time.")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

if [ "${SEED_DEMO:-false}" = "true" ]; then
  python manage.py seed_demo
fi

exec "$@"
