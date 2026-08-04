#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
docker compose up -d
cd backend
pip install -r requirements.txt -q
alembic upgrade head
python scripts/seed_catalog.py
echo "Phase 0 setup complete. Run: uvicorn app.main:app --reload --app-dir backend"
