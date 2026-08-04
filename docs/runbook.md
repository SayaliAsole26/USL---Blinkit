# USL Production Runbook

Operational guide for incident response, feature flags, and rollout controls on **Railway** (backend) and **Vercel** (frontend).

## Quick Links

| Service | Platform | Health |
| --- | --- | --- |
| Backend API | Railway | `GET /health` |
| Frontend | Vercel | Preview / production URL |
| Postgres | Railway plugin | Connection via `DATABASE_URL` |
| Redis | Railway plugin | Connection via `REDIS_URL` |

## Kill Switches (Feature Flags)

Set these on **Railway** and redeploy:

| Variable | Effect when disabled / zero |
| --- | --- |
| `USL_ENABLED=false` | All USL APIs return 404; app shows disabled state |
| `USL_CHECKOUT_RECOMMENDATIONS=false` | Checkout module hidden; Path B not invoked |
| `ROLLOUT_PERCENTAGE=0` | Recommendations API returns empty list (soft kill) |
| `EXPERIMENTS_ENABLED=false` | All users get control ranker weights |
| `GROQ_API_KEY=` (empty) | Template fallbacks for intent + explanations |

**Emergency checkout disable:** set `USL_CHECKOUT_RECOMMENDATIONS=false` and `ROLLOUT_PERCENTAGE=0`.

## Rollout Stages

| Stage | `ROLLOUT_PERCENTAGE` | Audience |
| --- | --- | --- |
| Internal | `100` | Team dogfood |
| Beta | `1`–`5` | Hash-bucketed % of user IDs |
| GA | `100` | All users with kill switch ready |

Rollout uses deterministic SHA-256 bucketing on `user_id`.

## Incident Response

### Elevated 5xx / healthcheck failures

1. Check Railway deploy logs and `GET /health`.
2. Verify `DATABASE_URL` and migrations.
3. If startup slow: `EMBEDDINGS_ENABLED=false`, `MEILI_ENABLED=false`.
4. Roll back to last green Railway deployment if needed.

### Groq rate limits (429)

- Mitigation: `EXPLANATION_CACHE_TTL_SECONDS=86400`; reduce `ROLLOUT_PERCENTAGE`.
- Template fallbacks are active by default.

### Bad recommendations

1. Set `ROLLOUT_PERCENTAGE=0`.
2. Inspect `recommendation_events` table.
3. Tune `data/ranker-weights.json` or `RANKER_WEIGHTS_JSON`.

### CORS / frontend cannot reach API

- `CORS_ORIGINS` must include Vercel URL.
- `VITE_API_URL` = Railway base URL (no `/v1` suffix).

## Caching

| Cache | TTL env |
| --- | --- |
| Checkout recommendations | `CHECKOUT_CACHE_TTL_SECONDS` (default 300) |
| Explanation text | `EXPLANATION_CACHE_TTL_SECONDS` (default 86400) |
| Context (weather/season) | `CONTEXT_CACHE_TTL_SECONDS`, `WEATHER_CACHE_TTL_SECONDS` |

Set TTL to `0` to disable during debugging.

## Observability

Grafana Cloud and Sentry are optional:

- **Sentry:** `SENTRY_DSN` on Railway
- **Grafana:** recommendation funnel, Groq latency, shortlist p95

Built-in: `/health`, API `latency_ms` / `shortlist_size`, `recommendation_events` audit log.

## Deployment Checklist

**Railway:** `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `GROQ_API_KEY`, `CORS_ORIGINS`; run migrations/seed once.

**Vercel:** `VITE_API_URL`, `VITE_ADMIN_DEBUG=false`.
