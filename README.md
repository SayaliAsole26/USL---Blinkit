# USL Blinkit

Universal Shopping List — AI-powered cross-category recommendation engine for Blinkit.

## Phase 3 — Checkout Recommendations (current)

Path B checkout pipeline with explainable recommendations at checkout only.

| Layer | Stack |
| --- | --- |
| UI design | [Google Stitch](https://stitch.withgoogle.com) |
| Frontend | React + Vite → **Vercel** |
| Backend | FastAPI → **Railway** |
| LLM | Groq API |
| Database | PostgreSQL + pgvector |
| Cache / queue | Redis + Celery |
| Search | Meilisearch |

## Quick start (local)

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
copy ..\.env.example ..\.env
alembic upgrade head
python scripts/seed_catalog.py
uvicorn app.main:app --reload --app-dir .
```

API: http://localhost:8000 · Docs: http://localhost:8000/docs

### Phase 1 endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/v1/users/location` | Save city, state, pincode |
| `GET` | `/v1/users/location` | Get saved location |
| `POST` | `/v1/usl/items` | Add free-text USL item |
| `GET` | `/v1/usl/items?status=pending` | List items (filter: pending, purchased, all) |
| `PATCH` | `/v1/usl/items/{id}` | Update intent, status, priority |
| `DELETE` | `/v1/usl/items/{id}` | Remove item |

Auth header for local dev: `Authorization: Bearer dev`

### Phase 2 — Path A intent processing

After adding a USL item, a Celery worker enriches it asynchronously:

```bash
# Apply migration v002
cd backend
alembic upgrade head
python scripts/seed_catalog.py

# Terminal 1 — API
uvicorn app.main:app --reload

# Terminal 2 — Celery worker (requires Redis)
celery -A app.worker.celery_app worker -Q usl-intent -l info
```

Set `INTENT_WORKER_SYNC=true` in `.env` to run matching inline without Redis/Celery (local dev only).

Admin debug: `GET /v1/admin/matches`, `GET /v1/admin/pipeline/metrics` (when `ADMIN_DEBUG_ENABLED=true`)

Frontend: set `VITE_ADMIN_DEBUG=true` and use the **Match debug** button.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173

### 4. Groq smoke test (optional)

Set `GROQ_API_KEY` in `.env`, then:

```bash
curl -X POST http://localhost:8000/v1/integrations/groq/smoke
```

## Deploy

| Service | Platform | Config |
| --- | --- | --- |
| Frontend | Vercel | Root: `frontend/`, env `VITE_API_URL` |
| Backend | Railway | `railway.toml`, Postgres + Redis plugins |

## Project structure

```
USL-Blinkit/
├── backend/          # FastAPI, pipeline, integrations
├── frontend/         # React + Vite
├── data/             # Catalog fixtures (static dataset sample)
├── docs/             # Problem statement, architecture, plans
├── openapi/          # USL v1 API spec skeleton
└── docker-compose.yml
```

## Documentation

- [Problem Statement](docs/ProblemStatement.md)
- [Architecture](docs/architecture.md)
- [Implementation Plan](docs/implementation-plan.md)
- [Edge Cases](docs/edge-cases.md)

## Static dataset

Sample catalog fixtures mirror the [USL Static Dataset](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651). Replace `data/catalog-fixtures.json` with exported sheet data when available.
