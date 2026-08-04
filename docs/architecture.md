# System Architecture — Universal Shopping List (USL)

> Detailed technical architecture for the AI-powered Universal Shopping List and checkout recommendation engine.  
> Derived from [`ProblemStatement.md`](./ProblemStatement.md) and [`context.md`](./context.md).

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Core Processing Framework](#2-core-processing-framework)
3. [Design Principles](#3-design-principles)
4. [High-Level System Diagram](#4-high-level-system-diagram)
5. [Core Services](#5-core-services)
6. [Data Architecture](#6-data-architecture)
7. [AI & Recommendation Pipeline](#7-ai--recommendation-pipeline)
8. [Context Enrichment Layer](#8-context-enrichment-layer)
9. [User Journey — Technical Flows](#9-user-journey--technical-flows)
10. [API Design](#10-api-design)
11. [Integration with Blinkit](#11-integration-with-blinkit)
12. [Explainability & Recommendation UX Contract](#12-explainability--recommendation-ux-contract)
13. [Security, Privacy & Compliance](#13-security-privacy--compliance)
14. [Scalability & Performance](#14-scalability--performance)
15. [Observability & Success Metrics](#15-observability--success-metrics)
16. [Deployment Topology](#16-deployment-topology)
17. [Future Extensions](#17-future-extensions)
18. [Tech Stack — Free & Open Source](#18-tech-stack--free--open-source)

---

## 1. Architecture Overview

USL is a **shopping memory platform** composed of four logical layers:

| Layer | Responsibility |
| --- | --- |
| **Experience Layer** | Blinkit app surfaces: onboarding, USL management, cart, checkout recommendations — **designed in Stitch**, built with React, deployed on **Vercel** |
| **Application Layer** | USL CRUD, recommendation orchestration, user actions, list lifecycle |
| **Intelligence Layer** | Intent understanding, catalog matching, ranking, explainability generation |
| **Data & Context Layer** | **Fixed Dataset** — persistent memory, catalog/availability, purchase history, external context signals |

The Intelligence Layer implements the four framework stages: **Filtering** (Catalog Matcher, Ranker rules), **LLM** (Intent Processor, Explainability Engine), orchestrated between **Fixed Dataset** (Data layer) and **Output** (checkout response).

The system is designed around one architectural invariant:

> **Recommendations are computed and rendered only at checkout.** All other shopping flows remain unchanged.

All intelligence work follows the **[Dataset → Filter → LLM → Output](#2-core-processing-framework)** framework (see §2).

```mermaid
flowchart TB
    subgraph Experience["Experience Layer (Blinkit App)"]
        ONB[Onboarding / Location]
        USL_UI[Universal Shopping List UI]
        SHOP[Browse / Search / Cart]
        CHK[Checkout + USL Recommendations]
    end

    subgraph Application["Application Layer"]
        USL_SVC[USL Service]
        REC_ORCH[Recommendation Orchestrator]
        ACTION_SVC[Recommendation Action Service]
        ORDER_HOOK[Order Completion Hook]
    end

    subgraph Intelligence["Intelligence Layer"]
        INTENT[Intent Processor]
        MATCH[Catalog Matcher]
        RANK[Recommendation Ranker]
        EXPLAIN[Explainability Engine]
    end

    subgraph Data["Data & Context Layer"]
        USL_DB[(USL Store)]
        USER_DB[(User Profile & Location)]
        CATALOG[(Blinkit Catalog)]
        AVAIL[(Availability Service)]
        HISTORY[(Purchase History)]
        REC_HIST[(Recommendation History)]
        CTX[Context Enrichment]
    end

    ONB --> USER_DB
    USL_UI --> USL_SVC
    USL_SVC --> INTENT
    INTENT --> MATCH
    MATCH --> CATALOG
    MATCH --> AVAIL
    MATCH --> USL_DB

    SHOP --> CHK
    CHK --> REC_ORCH
    REC_ORCH --> USL_DB
    REC_ORCH --> HISTORY
    REC_ORCH --> REC_HIST
    REC_ORCH --> CTX
    REC_ORCH --> RANK
    RANK --> EXPLAIN
    EXPLAIN --> CHK

    CHK --> ACTION_SVC
    ACTION_SVC --> USL_DB
    ACTION_SVC --> REC_HIST
    ORDER_HOOK --> USL_DB
```

---

## 2. Core Processing Framework

USL follows a **Dataset → Filter → LLM → Output** processing framework. This is the primary backend pattern for all intelligence work: start from a fixed data corpus, narrow candidates with deterministic rules, apply the LLM only on a small shortlisted set, then return a bounded, explainable result.

This keeps the LLM focused on reasoning and language—not on searching the full Blinkit catalog.

### 2.1 Framework Diagram

```mermaid
flowchart TB
    subgraph Frontend["Frontend — Stitch → React · Vercel"]
        IN1[Location · City / State / Pincode]
        IN2[Universal Shopping List · free-text intent]
        IN3[Cart · current checkout items]
        IN4[Context · event dates · etc.]
    end

    API[API Layer · REST / BFF]

    subgraph Backend["Backend — USL Intelligence Pipeline"]
        DS[("Fixed Dataset\nBlinkit Catalog + USL Memory\n+ Purchase / Rec History")]
        FIL["Filtering\nRules R1–R7 · Availability · Pincode\nCart exclusion · Cooldowns"]
        LLM["LLM · Groq API\nllama-3.3-70b / mixtral"]
        OUT["Output\nTop 3–5 explainable\n checkout recommendations"]
    end

    IN1 & IN2 & IN3 & IN4 --> API
    API --> DS
    DS --> FIL
    FIL -->|"~20–80 candidates"| LLM
    LLM --> OUT
    OUT --> API
    API --> Frontend
```

### 2.2 Stage Mapping (USL)

| Framework Stage | USL Implementation | Purpose |
| --- | --- | --- |
| **Frontend inputs** | Pincode, USL items, cart, optional event dates | Capture user intent and checkout context |
| **API** | `/v1/usl/*`, `/v1/recommendations/checkout`, `/v1/users/location` | Auth, validation, orchestration boundary |
| **Fixed Dataset** | Blinkit product catalog + [static dataset](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651) (dev) + USL Store + purchase/recommendation history | Single source corpus; no LLM catalog scan |
| **Filtering** | Candidate rules, pincode availability, cart dedup, dismiss cooldown, match confidence threshold | Narrow full corpus to a small shortlist (~20–80) |
| **LLM** | [Groq API](https://console.groq.com) (free tier) — Intent Processor + Explainability Engine; template fallback on rate limit | Reasoning and natural-language explanations only |
| **Output** | Top 3–5 recommendations with `reason_type` + `reason_text` + `sku_id` | Bounded, intent-first checkout suggestions |

### 2.3 Two Pipeline Paths

The same framework applies in two places:

#### Path A — USL Item Ingestion (async, on add/edit)

```
User intent text
  → API (POST /v1/usl/items)
  → Fixed Dataset (full catalog index)
  → Filtering (category + embedding + fuzzy match → top SKUs)
  → LLM (normalize intent, disambiguate, classify)
  → Output (enriched USL item + catalog_matches stored)
```

#### Path B — Checkout Recommendations (sync, at checkout only)

```
Checkout session + USL + cart + context
  → API (GET /v1/recommendations/checkout)
  → Fixed Dataset (USL items + catalog_matches + history + context)
  → Filtering (R1–R7, availability, exclusions → shortlist)
  → LLM (reason_text generation, optional re-rank)
  → Output (Top 3–5 explainable recommendations)
```

### 2.4 Filtering vs LLM — Responsibility Split

| Responsibility | Handled By | Why |
| --- | --- | --- |
| Search full Blinkit catalog | **Fixed Dataset** + search index | Scale; deterministic; auditable |
| Pincode availability | **Filtering** | Must be exact; fail-closed |
| Exclude cart / dismissed items | **Filtering** | Business rules; no model drift |
| Apply USL intent rules (R1–R7) | **Filtering** | Intent-first; never random |
| Narrow to shortlist | **Filtering** | Cost and latency control for LLM |
| Parse ambiguous free-text intent | **LLM** | Language understanding |
| Generate human-like `reason_text` | **LLM** | Personalised copy from structured signals |
| Final tie-break among close candidates | **LLM** (optional) | When weighted scores are near-equal |
| Decide Top N SKUs | **Ranker** (deterministic weights) + validation gate | Reproducible ordering; LLM does not pick random SKUs |

### 2.5 Output Contract

The framework always produces a **bounded, explainable** result—never an open-ended list:

| Path | Output | Max Size |
| --- | --- | --- |
| USL ingestion | Enriched item + best catalog match(es) | Top 3 SKU matches stored |
| Checkout | Ranked recommendations | Top 3–5 (configurable) |

Every checkout output item **must** include `reason_type` and `reason_text` before leaving the backend.

---

## 3. Design Principles

These principles translate product constraints from the problem statement into engineering decisions.

| Principle | Product Requirement | Architectural Implication |
| --- | --- | --- |
| **Checkout-only activation** | No interruptions during browse | Recommendation Orchestrator is bound to checkout events only; no hooks in search/category APIs |
| **Intent-first recommendations** | No random upsells | Ranker scores only USL-linked or replenishment-derived candidates |
| **Mandatory explainability** | Every recommendation has a reason | Explainability Engine is a required pipeline stage; responses without `reason` are rejected |
| **Platform-agnostic memory** | USL captures cross-platform intent | USL items store free-text intent + normalized metadata, not SKU-only records |
| **Location-aware availability** | Pincode drives fulfillment | All catalog matches and recommendations filter by user location at query time |
| **Persistent long-term memory** | USL evolves across sessions | USL Store retains pending, purchased, deferred, and dismissed states with timestamps |
| **Non-invasive shopping** | Normal Blinkit experience | USL integrates as an additive module; cart and catalog paths are read-only consumers |
| **Dataset → Filter → LLM → Output** | Scale + explainability + cost control | Fixed corpus first; deterministic filter to shortlist; LLM only on shortlisted candidates; bounded Top N output |

---

## 4. High-Level System Diagram

### 4.1 Component Interaction (Checkout Path)

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant App as Blinkit App
    participant Checkout as Checkout Service
    participant Orch as Recommendation Orchestrator
    participant USL as USL Service
    participant Ctx as Context Enrichment
    participant Rank as Ranker + Explainer
    participant Cat as Catalog / Availability

    User->>App: Proceed to Checkout
    App->>Checkout: GET checkout session
    Checkout->>Orch: Trigger recommendation request
    Orch->>USL: Fetch active USL items
    Orch->>Checkout: Fetch current cart
    Orch->>Cat: Resolve SKUs + availability (pincode)
    Orch->>Ctx: Fetch weather, season, events
    Orch->>Rank: Score + generate explanations
    Rank-->>Orch: Ranked recommendations with reasons
    Orch-->>App: Recommendation payload
    App-->>User: Show explainable recommendations

    User->>App: Add / Save / Dismiss
    App->>Orch: POST recommendation action
    Orch->>USL: Update item state + history
```

### 4.2 USL Item Ingestion Path

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant App as Blinkit App
    participant USL as USL Service
    participant Intent as Intent Processor
    participant Match as Catalog Matcher
    participant Store as USL Store

    User->>App: Add "Bluetooth Earbuds" to USL
    App->>USL: POST /usl/items
    USL->>Intent: Parse intent + category
    Intent->>Match: Match against Blinkit catalog
    Match->>Match: Check pincode availability
    Match-->>USL: Normalized metadata + match confidence
    USL->>Store: Persist enriched USL item
    Store-->>App: Item created (pending)
```

---

## 5. Core Services

### 5.1 User & Location Service

**Purpose:** Capture and serve user location for availability and contextual recommendations.

| Capability | Details |
| --- | --- |
| Onboarding | Collect city, state, pincode on first app open |
| Profile storage | Persist default delivery location per user |
| Availability key | Expose `pincode` (and optional lat/long) to downstream services |

**Key entities:** `User`, `UserLocation`

---

### 5.2 USL Service (Shopping Memory)

**Purpose:** CRUD and lifecycle management for the Universal Shopping List.

| Capability | Details |
| --- | --- |
| Add item | Accept free-text or structured product intent |
| List items | Return pending, saved-for-later, purchased, dismissed views |
| Update item | Edit intent text, notes, priority, event dates |
| State transitions | `pending` → `purchased` / `saved_for_later` / `dismissed` |
| Auto-sync | On order completion, mark matched items as purchased |

**Processing trigger:** Every new or updated item asynchronously invokes the Intent Processor.

---

### 5.3 Intent Processor

**Purpose:** Understand what the user meant and normalize it for catalog matching.

| Step | Output |
| --- | --- |
| Intent extraction | Product type, brand hints, attributes, use case |
| Category classification | Map to Blinkit taxonomy (e.g., Personal Care → Face Wash) |
| Entity resolution | Canonical name, synonyms, cross-category tags |
| Confidence score | Match reliability for downstream ranking |

**Implementation (free stack):**

- **LLM:** Groq API — `llama-3.3-70b-versatile` (intent parsing), `mixtral-8x7b-32768` (explanation copy fallback)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` via Hugging Face (local or free Inference API)
- **Phase 2+:** Rule-based overrides for top 50 intents to reduce Groq calls

---

### 5.4 Catalog Matcher

**Purpose:** Map USL intent to Blinkit SKUs and local availability.

| Input | Output |
| --- | --- |
| Normalized intent, user pincode | `matched_skus[]`, `availability_status`, `match_confidence` |

**Matching strategy (layered):**

1. Exact / fuzzy title match against catalog index
2. Embedding-based semantic search over product catalog
3. Category-filtered re-ranking
4. Availability filter by pincode and inventory service

**States:**

- `available` — SKU in stock at user location
- `unavailable` — Known SKU but not serviceable
- `unmatched` — Intent stored; no confident catalog mapping yet

---

### 5.5 Recommendation Orchestrator

**Purpose:** Single entry point for checkout recommendations. Orchestrates the **Dataset → Filter → LLM → Output** pipeline (§2): aggregates fixed dataset sources, runs deterministic filtering, delegates LLM explainability, and returns validated Top N output.

**Trigger:** Checkout page load or explicit `GET /recommendations/checkout` call.

**Candidate generation sources:**

| Source | Recommendation Type |
| --- | --- |
| USL pending items with available SKUs | Memory reminder, Cross-category discovery |
| Purchase history + replenishment model | Replenishment reminder |
| USL items + weather API | Weather context |
| USL items + season calendar | Seasonal context |
| USL items + user events | Event-based reminder |
| Cart category vs. USL category gap | Shopping completion |

**Exclusions:**

- Items already in cart
- Items dismissed within cooldown window
- Unmatched or unavailable items (unless surfaced with "notify when available" UX in future)

---

### 5.6 Recommendation Ranker

**Purpose:** Score and order candidates by relevance at this checkout moment.

**Scoring dimensions (weighted):**

| Signal | Weight Driver |
| --- | --- |
| USL recency & dwell time | Memory reminder strength |
| Availability certainty | Only surface fulfillable items |
| Cart complementarity | Cross-category discovery |
| Replenishment due score | Time since last purchase vs. usage cycle |
| Context urgency | Weather, season, upcoming events |
| Prior dismissals | Negative signal |
| Prior acceptance rate | Personalization feedback |

**Output:** Ordered list of max N recommendations (configurable, e.g., 3–5).

---

### 5.7 Explainability Engine

**Purpose:** Generate human-like recommendation copy with structured reason codes.

Every recommendation **must** include:

```json
{
  "recommendation_id": "rec_abc123",
  "sku_id": "blinkit_sku_456",
  "product_name": "Face Wash",
  "reason_type": "memory_reminder",
  "reason_text": "You added this Face Wash to your Universal Shopping List a few weeks ago. It's available on Blinkit today.",
  "confidence": 0.92
}
```

**Reason types (enum):**

- `memory_reminder`
- `replenishment_reminder`
- `weather_context`
- `seasonal_context`
- `event_based`
- `cross_category_discovery`
- `shopping_completion`

The orchestrator **rejects** any candidate missing `reason_type` and `reason_text`.

---

### 5.8 Recommendation Action Service

**Purpose:** Handle user decisions on each recommendation.

| Action | System Behavior |
| --- | --- |
| **Add to Cart** | Add SKU to cart; log acceptance; optionally mark USL item as `in_cart` |
| **Save for Later** | Set USL item to `saved_for_later`; suppress for N days |
| **Dismiss** | Set USL item to `dismissed`; log reason; apply cooldown before re-surfacing |

All actions write to **Recommendation History** for model feedback and deduplication.

---

### 5.9 Order Completion Hook

**Purpose:** Sync USL after successful checkout.

| Behavior | Details |
| --- | --- |
| Match purchased SKUs to USL items | Fuzzy match on SKU or normalized intent |
| Update state | Mark as `purchased` with `purchased_at` |
| Retain unresolved items | Pending / saved items remain in USL |
| Feed replenishment model | Update purchase history for future reminders |

---

## 6. Data Architecture

### 6.1 Entity Relationship (Logical Model)

```mermaid
erDiagram
    USER ||--o| USER_LOCATION : has
    USER ||--o{ USL_ITEM : owns
    USER ||--o{ PURCHASE_HISTORY : has
    USER ||--o{ RECOMMENDATION_EVENT : receives
    USL_ITEM ||--o{ USL_ITEM_METADATA : enriched_by
    USL_ITEM ||--o{ CATALOG_MATCH : maps_to
    CATALOG_MATCH }o--|| PRODUCT_SKU : references
    RECOMMENDATION_EVENT }o--o| USL_ITEM : targets
    RECOMMENDATION_EVENT }o--o| PRODUCT_SKU : suggests
```

### 6.2 Core Schemas

#### `users`

| Field | Type | Notes |
| --- | --- | --- |
| `user_id` | UUID | Primary key |
| `created_at` | timestamp | |
| `onboarding_completed` | boolean | |

#### `user_locations`

| Field | Type | Notes |
| --- | --- | --- |
| `user_id` | UUID | FK |
| `city` | string | |
| `state` | string | |
| `pincode` | string | Availability key |
| `updated_at` | timestamp | |

#### `usl_items`

| Field | Type | Notes |
| --- | --- | --- |
| `item_id` | UUID | Primary key |
| `user_id` | UUID | FK |
| `raw_intent` | string | User-entered text, e.g. "AirPods" |
| `normalized_name` | string | AI-normalized product name |
| `category` | string | Blinkit taxonomy category |
| `status` | enum | `pending`, `saved_for_later`, `dismissed`, `purchased`, `in_cart` |
| `priority` | int | Optional user ranking |
| `event_date` | date | Optional, for birthday/gift reminders |
| `created_at` | timestamp | Used for memory reminders |
| `updated_at` | timestamp | |
| `purchased_at` | timestamp | Nullable |

#### `usl_item_metadata`

| Field | Type | Notes |
| --- | --- | --- |
| `item_id` | UUID | FK |
| `attributes` | JSONB | Brand, size, color, etc. |
| `intent_confidence` | float | |
| `tags` | string[] | cross-category, seasonal, etc. |

#### `catalog_matches`

| Field | Type | Notes |
| --- | --- | --- |
| `item_id` | UUID | FK |
| `sku_id` | string | Blinkit SKU |
| `match_confidence` | float | |
| `availability_status` | enum | `available`, `unavailable`, `unknown` |
| `pincode` | string | Location at match time |
| `matched_at` | timestamp | Re-evaluate on location change |

#### `recommendation_events`

| Field | Type | Notes |
| --- | --- | --- |
| `event_id` | UUID | |
| `user_id` | UUID | |
| `checkout_session_id` | string | |
| `item_id` | UUID | Nullable |
| `sku_id` | string | |
| `reason_type` | enum | See Explainability Engine |
| `reason_text` | string | |
| `action` | enum | `shown`, `added_to_cart`, `saved_for_later`, `dismissed` |
| `created_at` | timestamp | |

#### `purchase_history`

| Field | Type | Notes |
| --- | --- | --- |
| `user_id` | UUID | |
| `sku_id` | string | |
| `product_name` | string | |
| `category` | string | |
| `purchased_at` | timestamp | Feeds replenishment model |
| `quantity` | int | |

### 6.3 Storage Strategy

Default stack uses **free and open-source** tools. Paid upgrades are optional for production scale.

| Store | Technology (Free Default) | Paid Upgrade (Optional) | Data |
| --- | --- | --- | --- |
| Primary transactional DB | **PostgreSQL** (Docker local / **Railway Postgres** plugin) | Managed RDS | Users, USL items, recommendation events |
| Catalog index | **PostgreSQL FTS** + in-memory fuzzy match; [Meilisearch](https://www.meilisearch.com) self-hosted (OSS) | Elasticsearch / OpenSearch | Product search and semantic matching |
| Vector store | **pgvector** extension on PostgreSQL | Pinecone | Embedding-based intent ↔ catalog matching |
| Cache | **Redis** (Docker local / **Railway Redis** plugin) | ElastiCache | Pincode availability, checkout recommendation cache |
| Event stream | **Redis Streams** + [BullMQ](https://docs.bullmq.io) (Node) or **Celery + Redis** (Python) | Kafka / Pub/Sub | Async intent processing, order hooks |
| LLM | **[Groq API](https://console.groq.com)** free tier | OpenAI / Anthropic | Intent parse, explainability copy |
| Embeddings | **sentence-transformers** (local CPU) | Hugging Face paid inference | Catalog semantic search |
| Weather | **[Open-Meteo](https://open-meteo.com)** (no API key) | Commercial weather API | Pincode forecast for R4 |
| Observability | **Grafana Cloud** free tier + **Sentry** free tier | Datadog / PagerDuty | Metrics, errors, alerts |
| CI/CD | **GitHub Actions** (free for public repos) | — | Build, test, deploy |
| **Frontend hosting** | **[Vercel](https://vercel.com)** | Free tier | React app (Stitch-designed UI) |
| **Backend hosting** | **[Railway](https://railway.app)** | Free tier / usage-based | API + BullMQ/Celery worker |

### 6.4 Static Dataset (Development & Testing)

Local development, catalog matching, and Phase 0–2 integration tests use the Blinkit product static dataset:

**[USL Static Dataset (Google Sheets)](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651)**

| Usage | Details |
| --- | --- |
| Mock catalog | Seed product SKUs, names, categories, and prices |
| Intent matching | Validate USL free-text → SKU mapping accuracy |
| Availability simulation | Pair with pincode fixtures for local inventory checks |
| Recommendation QA | Test memory, cross-category, and checkout recommendation flows |

In **development**, import or sync this sheet in place of live Blinkit Catalog API responses. In **staging/production**, use live catalog and inventory services.

---

## 7. AI & Recommendation Pipeline

The pipeline implements the [Core Processing Framework (§2)](#2-core-processing-framework): **Dataset → Filter → LLM → Output**.

### 7.1 Pipeline Stages

```mermaid
flowchart LR
    subgraph Dataset["Fixed Dataset"]
        D1[Blinkit Catalog]
        D2[USL Store]
        D3[History + Context]
    end

    subgraph Filter["Filtering"]
        F1[Rules R1–R7]
        F2[Availability · Pincode]
        F3[Cart / Dismiss Exclusions]
    end

    subgraph LLM["LLM"]
        L1[Explainability Engine]
        L2[Optional Rank Tie-break]
    end

    subgraph Output["Output"]
        O1[Top 3–5 Recommendations]
        O2[Validation Gate]
    end

    D1 & D2 & D3 --> F1
    F1 --> F2 --> F3
    F3 -->|"shortlist"| L1
    L1 --> L2 --> O1 --> O2
```

### 7.2 Candidate Generation Rules

| Rule ID | Rule | Recommendation Type |
| --- | --- | --- |
| R1 | USL item pending + SKU available + not in cart | Memory reminder |
| R2 | Prior purchase + replenishment interval elapsed | Replenishment reminder |
| R3 | USL item tagged seasonal + current season match | Seasonal context |
| R4 | USL item + adverse weather forecast in pincode | Weather context |
| R5 | USL item with `event_date` within threshold | Event-based |
| R6 | Cart category ≠ USL item category + SKU available | Cross-category discovery |
| R7 | Multiple available USL items not in cart | Shopping completion |

### 7.3 Replenishment Model

Estimates when a user may need to repurchase consumables.

| Input | Model Approach |
| --- | --- |
| Purchase history | Compute inter-purchase interval per SKU/category |
| Product type | Default cycles (e.g., face wash ~30 days) if sparse history |
| User override | Future: allow "remind me every X days" |

**Output:** `replenishment_due_score` ∈ [0, 1]

### 7.4 LLM Usage Boundaries

**Provider:** Groq API (free tier). Store `GROQ_API_KEY` in environment secrets.

| Model | Use Case |
| --- | --- |
| `llama-3.3-70b-versatile` | Intent parsing, category classification, disambiguation |
| `mixtral-8x7b-32768` | Explanation copy generation (fallback if primary model rate-limited) |

| Use Case | LLM Role |
| --- | --- |
| Intent parsing | Extract category, attributes, normalized name via Groq structured JSON output |
| Explanation copy | Generate natural-language `reason_text` from structured signals |
| Ambiguous matching | Disambiguate free-text when catalog search is inconclusive |

| Not LLM-driven | Reason |
| --- | --- |
| Availability checks | Must be deterministic from inventory service |
| Final rank order | Weighted scoring for auditability |
| Cart mutations | Transactional, idempotent operations |

**Groq free-tier safeguards:**

- Filter **before** every Groq call (shortlist ≤ 80 candidates)
- Template fallback for `reason_text` when Groq returns 429/5xx
- Cache explanation copy in Redis keyed by `(reason_type, usl_item_id, context_hash)` TTL 24h
- Batch intent processing via BullMQ/Celery worker (not synchronous on API hot path)

---

## 8. Context Enrichment Layer

External and internal signals combined at checkout.

### 8.1 Context Providers

| Provider | Signal | Used For |
| --- | --- | --- |
| **Season Calendar** | Summer, monsoon, winter, festivals (static JSON — no API cost) | Seasonal context |
| **Weather API** | [Open-Meteo](https://open-meteo.com) — free, no API key; cache by pincode + date | Weather context |
| **User Events** | Birthday, anniversary dates on USL items | Event-based reminders |
| **Time Context** | Day of week, time of day | Optional ranking tie-breaker |
| **Cart Analyzer** | Categories and items in current cart | Cross-category discovery, shopping completion |

### 8.2 Context Service Interface

```
GET /context/checkout?user_id=&pincode=&cart_id=
```

**Response:**

```json
{
  "season": "summer",
  "weather": {
    "forecast": "rain",
    "severity": "moderate",
    "days_ahead": 5
  },
  "cart_categories": ["groceries", "dairy"],
  "upcoming_events": [
    { "item_id": "...", "event_date": "2026-08-10", "label": "friend_birthday" }
  ]
}
```

Context is fetched once per checkout session and cached for the session TTL.

---

## 9. User Journey — Technical Flows

### Step 1 — Capture User Location

```
App → POST /users/onboarding/location { city, state, pincode }
     → User Location Service persists profile
     → Returns serviceability flag (optional)
```

### Step 2 — Create Universal Shopping List

```
App → POST /usl/items { raw_intent: "Moisturizer" }
     → USL Service persists pending item
     → Async: Intent Processor → Catalog Matcher → update metadata
```

### Step 3 — AI Processes USL (Async)

```
Event: usl.item.created
  → Intent Processor: classify + normalize
  → Catalog Matcher: search catalog, check pincode availability
  → Persist usl_item_metadata + catalog_matches
```

### Step 4 — Normal Shopping

No USL recommendation calls. Cart and catalog services operate independently.

### Step 5 — Checkout Recommendations

```
App → GET /recommendations/checkout?session_id=
     → Orchestrator aggregates USL, cart, catalog, history, context
     → Ranker + Explainer produce validated payload
     → Log recommendation_events (action: shown)
```

### Step 6 — User Decision

```
App → POST /recommendations/{id}/actions { action: add_to_cart | save_for_later | dismiss }
     → Action Service updates USL state + recommendation history
     → Add to cart delegates to Cart Service
```

### Step 7 — Checkout Complete

```
Order Service → Event: order.completed
     → Order Completion Hook matches SKUs → USL items
     → Mark purchased; update purchase_history
     → Pending items remain active
```

---

## 10. API Design

### 10.1 USL APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/v1/usl/items` | Add item to Universal Shopping List |
| `GET` | `/v1/usl/items` | List user's USL items (filter by status) |
| `PATCH` | `/v1/usl/items/{item_id}` | Update intent, event date, priority |
| `DELETE` | `/v1/usl/items/{item_id}` | Remove item |

### 10.2 Location APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/v1/users/location` | Set or update city, state, pincode |
| `GET` | `/v1/users/location` | Get current user location |

### 10.3 Recommendation APIs

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/v1/recommendations/checkout` | Get ranked, explainable recommendations |
| `POST` | `/v1/recommendations/{rec_id}/actions` | Record user action |

### 10.4 Sample Checkout Recommendation Response

```json
{
  "checkout_session_id": "chk_789",
  "recommendations": [
    {
      "recommendation_id": "rec_001",
      "usl_item_id": "item_abc",
      "sku_id": "sku_face_wash_123",
      "product_name": "Cetaphil Gentle Face Wash",
      "price": 499,
      "image_url": "https://...",
      "reason_type": "memory_reminder",
      "reason_text": "You added this Face Wash to your Universal Shopping List a few weeks ago. It's available on Blinkit today.",
      "confidence": 0.91
    },
    {
      "recommendation_id": "rec_002",
      "usl_item_id": "item_def",
      "sku_id": "sku_earbuds_456",
      "product_name": "Bluetooth Earbuds",
      "reason_type": "cross_category_discovery",
      "reason_text": "You came to buy groceries today, but your saved Bluetooth Earbuds are also available on Blinkit.",
      "confidence": 0.84
    }
  ]
}
```

---

## 11. Integration with Blinkit

USL integrates as a **modular capability** within the existing Blinkit ecosystem.

| Blinkit System | Integration Pattern |
| --- | --- |
| **Auth / User Identity** | USL services trust Blinkit user JWT; no separate auth |
| **Catalog Service** | Read-only access for SKU metadata and search |
| **Inventory / Availability** | Real-time or near-real-time pincode-level stock checks |
| **Cart Service** | Read cart at checkout; write on "Add to Cart" action |
| **Order Service** | Subscribe to `order.completed` events for USL sync |
| **Checkout UI** | Inject USL recommendation module below cart summary |

### Integration Constraints

- USL must not modify browse/search ranking or inject banners mid-session
- Catalog matching reads from Blinkit's canonical product index
- All prices and inventory shown in recommendations must come from live Blinkit sources

---

## 12. Explainability & Recommendation UX Contract

The checkout UI and API share a strict contract aligned with the product rule: **no unexplained recommendations**.

### Required Fields (UI + API)

| Field | Required | Purpose |
| --- | --- | --- |
| `reason_type` | Yes | Structured analytics and iconography |
| `reason_text` | Yes | User-facing explanation |
| `product_name` | Yes | Clear product identity |
| `sku_id` | Yes | Cart add action |
| Actions | Yes | Add to Cart, Save for Later, Dismiss |

### Validation Gate

Before returning recommendations to the client:

1. Every item has non-empty `reason_text`
2. Every `reason_type` maps to a known enum
3. Every SKU passes availability check for user's pincode
4. No SKU already present in cart
5. Dismissed items respect cooldown policy

---

## 13. Security, Privacy & Compliance

| Area | Approach |
| --- | --- |
| **Authentication** | Blinkit SSO / JWT; all USL endpoints require authenticated user |
| **Authorization** | Users can only access their own USL and recommendation history |
| **PII** | Location (pincode) stored with consent at onboarding; event dates optional |
| **Data retention** | USL items retained while account active; purchase history per Blinkit policy |
| **LLM data handling** | Minimize PII in prompts; log prompts/responses with redaction |
| **Audit trail** | All recommendation events logged with reason codes for compliance review |

---

## 14. Scalability & Performance

### Latency Targets

| Operation | Target |
| --- | --- |
| USL item add | < 200ms API response (async enrichment) |
| Checkout recommendations | < 800ms p95 (parallel context + rank fetches) |
| Catalog re-match on pincode change | Async background job |

### Scaling Strategy

| Component | Strategy |
| --- | --- |
| USL Service | Horizontal scale; stateless app tier |
| Intent processing | Queue-backed workers scale independently |
| Catalog search | Read replicas + CDN for product metadata |
| Checkout recommendations | Redis cache keyed by `(user_id, cart_hash, pincode)` with 60s TTL |
| Context enrichment | Cache weather/season by pincode + date |

### Checkout Critical Path (Parallelized)

```
Parallel:
  - Fetch USL items
  - Fetch cart
  - Fetch purchase history
  - Fetch context (weather, season, events)
  - Fetch recommendation history
Then:
  - Candidate generation → rank → explain → validate
```

---

## 15. Observability & Success Metrics

Architecture instrumentation maps directly to product success metrics from the problem statement.

| Product Metric | Technical Signals |
| --- | --- |
| Cross-category purchases | USL-recommended SKU categories vs. cart categories; attach rate |
| AOV uplift | Order value delta when USL recommendations accepted |
| CLV | Repeat USL usage, replenishment acceptance over 90-day window |
| Product discovery | First-time category purchase via USL recommendation |
| Shopping completion | Count of USL items resolved per user per month |
| User convenience | Time-to-checkout, dismiss rate, save-for-later rate |

### Key Dashboards

- Recommendation funnel: shown → add / save / dismiss
- Reason type performance by category
- Catalog match rate for free-text USL intents
- Availability-filtered candidate drop-off
- Checkout latency p50 / p95 / p99
- **Framework pipeline:** fixed dataset size → filter shortlist size → LLM invocation rate → Top N output count

### Alerting

- Checkout recommendation error rate > 1%
- p95 latency > 1s
- Empty explanation rate > 0% (hard invariant)
- Catalog match failure spike
- **LLM invoked without prior filter stage** (invariant violation)
- **Filter shortlist size > configured max** (e.g., 80) before LLM call

---

## 16. Deployment Topology

Production deployment splits **frontend on Vercel** and **backend on Railway**. UI screens are designed in **[Stitch](https://stitch.withgoogle.com)** and implemented in React + Vite.

```mermaid
flowchart TB
    subgraph Design["Design"]
        STITCH[Google Stitch · UI design]
    end

    subgraph Vercel["Vercel · Frontend"]
        WEB[React + Vite + TypeScript]
    end

    subgraph Railway["Railway · Backend"]
        API_GW[FastAPI / Express API]
        WORKER[Intent Worker · BullMQ/Celery]
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis)]
    end

    subgraph External["External Services"]
        GROQ[Groq API]
        WEATHER[Open-Meteo]
        MEILI[Meilisearch · optional]
    end

    STITCH -.->|export / implement| WEB
    WEB -->|HTTPS REST| API_GW
    API_GW --> PG
    API_GW --> REDIS
    API_GW --> WORKER
    WORKER --> GROQ
    WORKER --> PG
    WORKER --> MEILI
    API_GW --> WEATHER

    subgraph Pipeline["Dataset → Filter → LLM → Output"]
        DS_NODE[Fixed Dataset]
        FIL_NODE[Filtering]
        LLM_NODE[LLM · Groq]
        OUT_NODE[Top N Output]
        DS_NODE --> FIL_NODE --> LLM_NODE --> OUT_NODE
    end

    API_GW --> Pipeline
    WORKER --> Pipeline
```

### 16.1 Deployment Split

| Surface | Platform | Contains |
| --- | --- | --- |
| **UI design** | [Stitch](https://stitch.withgoogle.com) | Onboarding, USL list, checkout recommendation cards |
| **Frontend app** | **Vercel** | React + Vite build; env `VITE_API_URL` → Railway API |
| **Backend API** | **Railway** | USL Service, Recommendation Orchestrator, Context Service |
| **Background worker** | **Railway** (separate service) | Path A intent processing, catalog matching |
| **Database** | **Railway PostgreSQL** plugin (+ pgvector) | USL Store, users, events, vectors |
| **Cache / queue** | **Railway Redis** plugin | Checkout cache, BullMQ/Celery jobs |

### 16.2 Environment Variables

**Vercel (frontend):**

```bash
VITE_API_URL=https://usl-api.up.railway.app
```

**Railway (backend):**

```bash
GROQ_API_KEY=gsk_...
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
CORS_ORIGINS=https://your-app.vercel.app
MEILI_URL=...  # optional
```

### 16.3 Legacy Internal Topology (Logical Services)

```mermaid
flowchart TB
    subgraph Client
        APP[React App · Vercel]
    end

    subgraph Gateway
        API_GW[API · Railway]
    end

    subgraph Services["USL Microservices"]
        USL[USL Service]
        REC[Recommendation Orchestrator]
        INTENT_W[Intent Worker]
    end

    subgraph Pipeline["Dataset → Filter → LLM → Output"]
        DS_NODE[Fixed Dataset]
        FIL_NODE[Filtering]
        LLM_NODE[LLM]
        OUT_NODE[Top N Output]
        DS_NODE --> FIL_NODE --> LLM_NODE --> OUT_NODE
    end

    REC --> Pipeline
    INTENT_W --> Pipeline

    subgraph BlinkitCore["Blinkit Core (Existing)"]
        CART[Cart Service]
        CAT[Catalog Service]
        INV[Inventory Service]
        ORD[Order Service]
    end

    subgraph DataStores
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis · Railway)]
        MEILI[(Meilisearch · optional)]
        QUEUE[(BullMQ / Celery)]
    end

    APP --> API_GW
    API_GW --> USL
    API_GW --> REC
    API_GW --> CART
    REC --> USL
    REC --> CAT
    REC --> INV
    REC --> CART
    USL --> QUEUE
    QUEUE --> INTENT_W
    INTENT_W --> CAT
    INTENT_W --> INV
    USL --> PG
    REC --> PG
    REC --> REDIS
    INTENT_W --> PG
    INTENT_W --> MEILI
    ORD --> QUEUE

    subgraph ExternalFree["Free External Services"]
        GROQ[Groq API]
        WEATHER[Open-Meteo]
    end

    INTENT_W --> GROQ
    REC --> GROQ
    REC --> WEATHER
```

### Environment Strategy

| Environment | Purpose |
| --- | --- |
| **Development** | Docker Compose locally; Stitch for UI mockups; [static dataset](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651); Groq API key |
| **Staging** | Vercel preview deployments + Railway staging service; Groq free tier |
| **Production** | **Vercel** (frontend) + **Railway** (API + worker + Postgres + Redis); feature flag `usl_checkout_recommendations` |

---

## 18. Tech Stack — Free & Open Source

Recommended stack for building USL at **zero infrastructure cost** during development and demo. All choices align with the [Dataset → Filter → LLM → Output](#2-core-processing-framework) framework.

### 18.1 Stack Overview

```mermaid
flowchart TB
    subgraph Design["UI Design"]
        STITCH[Google Stitch]
    end

    subgraph Vercel["Vercel · Frontend"]
        REACT[React + Vite + TypeScript]
    end

    subgraph Railway["Railway · Backend"]
        API[FastAPI or Express.js]
        WORKER[BullMQ / Celery Worker]
        PG[(PostgreSQL + pgvector)]
        REDIS[(Redis)]
    end

    subgraph AI["AI · Free"]
        GROQ[Groq API]
        ST[sentence-transformers]
    end

    subgraph External["External · Free"]
        WEATHER[Open-Meteo]
        SHEETS[Google Sheets · static dataset]
    end

    STITCH -.-> REACT
    REACT -->|VITE_API_URL| API
    API --> PG
    API --> REDIS
    API --> WORKER
    WORKER --> GROQ
    WORKER --> ST
    API --> WEATHER
    WORKER --> SHEETS
```

### 18.2 Component Selection

| Layer | Tool | Cost | Role in USL |
| --- | --- | --- | --- |
| **UI design** | [Google Stitch](https://stitch.withgoogle.com) | Free | Design onboarding, USL screens, checkout recommendation cards |
| **Frontend** | React + Vite + TypeScript | Free | Implement Stitch designs; deploy on Vercel |
| **Frontend hosting** | [Vercel](https://vercel.com) | Free tier | CDN, preview deploys, CI from GitHub |
| **Backend hosting** | [Railway](https://railway.app) | Free tier / usage-based | API service + intent worker + Postgres + Redis |
| **API** | FastAPI (Python) or Express (Node.js) | Free | REST `/v1/usl/*`, `/v1/recommendations/checkout` |
| **LLM** | [Groq API](https://console.groq.com) | Free tier | Intent parsing + `reason_text` generation |
| **LLM models** | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` | Free tier | Primary + fallback models on Groq |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Free (local CPU) | Catalog semantic search in Filtering stage |
| **Database** | PostgreSQL 16 + pgvector | Railway Postgres plugin / Docker local | USL Store, users, events, vectors |
| **Cache** | Redis | Railway Redis plugin / Docker local | Checkout rec cache, Groq explanation cache, job queue |
| **Search** | Meilisearch or PostgreSQL FTS | Free (OSS / built-in) | Catalog fuzzy + full-text match |
| **Job queue** | BullMQ (Redis) or Celery (Redis) | Free | Async Path A intent processing |
| **Weather** | Open-Meteo | Free (no key) | Rule R4 weather context |
| **Season / events** | Static JSON calendar | Free | Rule R3, R5 — no external API |
| **Auth (dev/demo)** | Mock JWT or Supabase Auth | Free tier | User scoping |
| **CI/CD** | GitHub Actions → Vercel + Railway | Free | Frontend auto-deploy on push; Railway deploy on merge |
| **Monitoring** | Grafana Cloud + Sentry | Free tiers | Latency, errors, Groq 429 alerts |

### 18.3 Groq Integration

#### Path A — Intent parsing (async worker)

```python
# Example: Groq structured intent extraction
from groq import Groq

client = Groq(api_key=os.environ["GROQ_API_KEY"])

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "Extract product intent as JSON: normalized_name, category, attributes, confidence."},
        {"role": "user", "content": f"USL intent: {raw_intent}"}
    ],
    response_format={"type": "json_object"},
    temperature=0.1,
)
```

#### Path B — Explainability copy (checkout)

```python
response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "Generate one sentence reason_text for a checkout recommendation. Use only provided structured signals."},
        {"role": "user", "content": json.dumps(structured_signals)},
    ],
    temperature=0.3,
    max_tokens=120,
)
```

**On Groq 429 (rate limit):** fall back to template-based `reason_text` — never block checkout.

### 18.4 Local Development (Docker Compose)

Local backend mirrors Railway services. Frontend runs via `npm run dev` or Vercel dev.

| Service | Image / Tool | Port |
| --- | --- | --- |
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` | 5432 |
| Redis | `redis:7-alpine` | 6379 |
| Meilisearch | `getmeili/meilisearch:latest` | 7700 |
| Frontend | React + Vite (`npm run dev`) | 5173 |
| UI design | [Google Stitch](https://stitch.withgoogle.com) | — |

Environment variables:

```bash
# Local frontend (.env.local)
VITE_API_URL=http://localhost:8000

# Local / Railway backend
GROQ_API_KEY=gsk_...
DATABASE_URL=postgresql://usl:usl@localhost:5432/usl
REDIS_URL=redis://localhost:6379
MEILI_URL=http://localhost:7700
CORS_ORIGINS=http://localhost:5173
```

### 18.5 Deployment (Vercel + Railway)

| Step | Platform | Action |
| --- | --- | --- |
| 1 | **Stitch** | Design USL onboarding, list, checkout recommendation UI |
| 2 | **React + Vite** | Implement Stitch screens as components |
| 3 | **Vercel** | Connect GitHub repo; set `VITE_API_URL`; deploy frontend |
| 4 | **Railway** | Deploy API service + worker service + Postgres + Redis plugins |
| 5 | **Railway** | Set `CORS_ORIGINS` to Vercel production + preview URLs |

### 18.6 Free-Tier Limits & Mitigations

| Service | Free limit | Mitigation in USL |
| --- | --- | --- |
| Groq API | Rate limits (RPM/TPM vary by model) | Filter before LLM; template fallback; explanation cache |
| Railway | Usage-based free credit | Single worker service; connection pooling; sleep acceptable for demo |
| Vercel | Bandwidth / build minutes on free tier | Static asset caching; preview deploys for PRs |
| Open-Meteo | Fair use | Cache forecast by pincode + date (24h TTL) |

### 18.7 Paid Upgrades (Optional, Post-Demo)

| Component | When to upgrade |
| --- | --- |
| Groq → OpenAI / Anthropic | Higher quality copy or higher rate limits at scale |
| Railway Redis → ElastiCache | Production traffic > Railway free tier |
| Railway Postgres → RDS | Enterprise SLA, larger storage |
| Meilisearch → Elasticsearch | Catalog > 500K SKUs with complex facets |
| BullMQ → Kafka | Event volume > Redis Streams capacity |

---

## 17. Future Extensions

Not in MVP but architecturally anticipated:

| Extension | Description |
| --- | --- |
| **Notify when available** | Alert when unmatched USL item becomes available at pincode |
| **Voice / NLP input** | "Add dog food and birthday gift to my list" |
| **Shared USL** | Household shopping lists |
| **External platform import** | Parse wishlists from Amazon/Nykaa URLs |
| **Smart replenishment tuning** | User-editable reminder intervals |
| **A/B experiment framework** | Test ranker weights and copy templates |

---

## References

- Product requirements: [`ProblemStatement.md`](./ProblemStatement.md)
- Condensed product context: [`context.md`](./context.md)
- Phase-wise implementation plan: [`implementation-plan.md`](./implementation-plan.md) — [§2 Framework Alignment by Phase](./implementation-plan.md#2-core-processing-framework-alignment)
- Edge cases & QA catalog: [`edge-cases.md`](./edge-cases.md)
- Static dataset: [USL Static Dataset (Google Sheets)](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651)
- Free tech stack: [§18 Tech Stack](./architecture.md#18-tech-stack--free--open-source)
