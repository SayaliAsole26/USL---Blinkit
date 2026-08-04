#!/bin/sh
set -e

CONCURRENCY="${CELERY_CONCURRENCY:-2}"
echo "Starting Celery worker (concurrency=${CONCURRENCY})..."
exec celery -A app.worker.celery_app worker -Q usl-intent -l info --concurrency="${CONCURRENCY}"
