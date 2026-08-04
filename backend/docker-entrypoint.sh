#!/bin/sh
# Railway: bind API first so /health passes, then run optional DB setup in background.

PORT="${PORT:-8000}"

if [ -z "${DATABASE_URL}" ]; then
  echo "WARNING: DATABASE_URL is not set. Link Postgres in Railway Variables."
  echo "         API will start but database routes will fail until DATABASE_URL is set."
fi

echo "Starting API on port ${PORT} (health check: GET /health)..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT}" &
UVICORN_PID=$!

run_db_setup() {
  if [ -z "${DATABASE_URL}" ]; then
    return 0
  fi

  if [ "${RUN_MIGRATIONS_ON_STARTUP}" = "true" ]; then
    echo "Running database migrations..."
    if ! alembic upgrade head; then
      echo "ERROR: migrations failed. Ensure Postgres has pgvector and DATABASE_URL is correct."
    fi
  fi

  if [ "${SEED_CATALOG_ON_STARTUP}" = "true" ]; then
    echo "Seeding catalog (fast mode: no embeddings / no Meili)..."
    EMBEDDINGS_ENABLED=false MEILI_ENABLED=false python scripts/seed_catalog.py || \
      echo "WARNING: catalog seed failed."
  fi
}

if [ "${RUN_MIGRATIONS_ON_STARTUP}" = "true" ] || [ "${SEED_CATALOG_ON_STARTUP}" = "true" ]; then
  run_db_setup &
fi

wait "${UVICORN_PID}"
