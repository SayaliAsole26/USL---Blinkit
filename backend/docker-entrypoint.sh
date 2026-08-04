#!/bin/sh
set -e

if [ "${RUN_MIGRATIONS_ON_STARTUP}" = "true" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

if [ "${SEED_CATALOG_ON_STARTUP}" = "true" ]; then
  echo "Seeding catalog fixtures..."
  python scripts/seed_catalog.py
fi

PORT="${PORT:-8000}"
echo "Starting API on port ${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT}"
