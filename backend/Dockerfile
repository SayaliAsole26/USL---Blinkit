FROM python:3.12-slim

WORKDIR /app

# Build from repo root: docker build -f backend/Dockerfile .
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY data/ /app/data/

ENV PYTHONPATH=/app
ENV PORT=8000

RUN chmod +x /app/docker-entrypoint.sh /app/start-worker.sh

EXPOSE 8000

# Railway sets PORT; entrypoint runs migrations when RUN_MIGRATIONS_ON_STARTUP=true
CMD ["/app/docker-entrypoint.sh"]
