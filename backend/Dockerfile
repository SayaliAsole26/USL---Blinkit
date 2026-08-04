FROM python:3.12-slim

WORKDIR /app

# Build from repo root: docker build -f backend/Dockerfile .
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ /app/data/

ENV PYTHONPATH=/app
ENV PORT=8000
# Production-friendly defaults (override in Railway dashboard)
ENV EMBEDDINGS_ENABLED=false
ENV MEILI_ENABLED=false
ENV ADMIN_DEBUG_ENABLED=false
ENV RUN_MIGRATIONS_ON_STARTUP=false
ENV SEED_CATALOG_ON_STARTUP=false

RUN chmod +x /app/docker-entrypoint.sh /app/start-worker.sh

EXPOSE 8000

# Railway sets PORT; entrypoint runs migrations when RUN_MIGRATIONS_ON_STARTUP=true
CMD ["/app/docker-entrypoint.sh"]
