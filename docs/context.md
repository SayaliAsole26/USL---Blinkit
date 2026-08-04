# Project Context — Universal Shopping List (USL)

> Condensed context derived from [`ProblemStatement.md`](./ProblemStatement.md). Use this file for onboarding, AI-assisted development, and alignment on product intent.

---

## What We Are Building

**Universal Shopping List (USL)** is an AI-powered cross-category recommendation engine for Blinkit. It gives users a single, persistent place to remember everything they intend to buy online—not just groceries—and uses that memory to surface relevant products at checkout with human-like reasoning.

USL is **not** a generic product recommender. It is a **shopping memory platform** that converts saved intent into timely, explainable checkout recommendations.

---

## Core Problem

| Issue | Impact |
| --- | --- |
| Users shop across many apps (Blinkit, Amazon, Nykaa, Flipkart, Myntra, Zepto, etc.) | Shopping intent leaks outside Blinkit |
| Blinkit is still perceived as grocery-only | Cross-category purchases are missed |
| No single place to track future online purchases | Users forget items or buy elsewhere |
| Blinkit has no persistent memory of future needs | Lower AOV, CLV, and shopping completion |

**Root cause:** Users lack a unified shopping memory, and Blinkit cannot act on intent the user expressed outside a single session or category.

---

## Product Vision

Transform Blinkit from a grocery app into a **shopping memory platform** that:

1. Captures long-term purchase intent in a platform-agnostic list
2. Processes and maps that intent to Blinkit's catalog and local availability
3. Reminds users at the **right moment** (checkout only—not during browse)
4. Explains every recommendation in natural, contextual language
5. Helps users consolidate orders and reduce multi-app shopping

---

## Success Metrics

The product should increase:

- Cross-category purchases
- Average Order Value (AOV)
- Customer Lifetime Value (CLV)
- Product discovery
- Shopping completion
- User convenience

---

## Key Concepts

### Universal Shopping List (USL)

- A **platform-agnostic** list of everything the user may buy online in the future
- Not limited to Blinkit products or groceries
- Serves as the user's **persistent shopping memory**
- Continuously updated as items are added, purchased, or deferred

**Example items:** Face Wash, AirPods, Dog Food, Bedsheet, Hair Dryer, Protein Powder, Birthday Gift, Coffee Machine, Extension Board, Moisturizer, Printer Ink

### Recommendation Trigger Point

- Recommendations fire **only at checkout**
- Browsing, search, and cart-building must remain **uninterrupted**
- No random or unexplained suggestions

### Explainability Rule

Every recommendation **must** include a clear reason. Users should never see unexplained recommendations.

---

## User Journey (7 Steps)

| Step | Name | Summary |
| --- | --- | --- |
| 1 | Capture Location | On first open: collect City, State, Pincode for availability |
| 2 | Create USL | User builds a long-term, cross-category shopping list |
| 3 | AI Processing | System interprets, categorizes, maps to catalog, checks availability, stores metadata |
| 4 | Normal Shopping | User browses Blinkit as usual; no USL interruptions |
| 5 | Checkout Recommendations | AI compares USL + cart + context; surfaces intent-based matches |
| 6 | User Decision | User can Add to Cart, Save for Later, or Dismiss (with reason shown) |
| 7 | Checkout | User completes order; USL auto-updates (purchased vs. still pending) |

---

## AI Processing (Step 3)

When a user adds an item to the USL, the system must:

1. Understand user intent
2. Categorize the product
3. Match against Blinkit's catalog
4. Determine availability for the user's location
5. Store structured metadata for future recommendations

The USL evolves over time and becomes richer long-term memory.

---

## Recommendation Engine Inputs (Step 5)

At checkout, the engine compares:

- Universal Shopping List
- Current cart
- Blinkit product catalog
- User location
- Product availability
- Purchase history (if available)
- Previous recommendation history
- Seasonal context
- Weather context
- Event context
- Replenishment patterns
- Cross-category relationships

**Output:** The most relevant products the user has **already expressed intent to buy**—not random upsells.

---

## Recommendation Types (Human-Like Logic)

Recommendations should feel like a helpful shopping companion:

| Type | Example |
| --- | --- |
| Memory reminder | "You added this Face Wash to your Universal Shopping List a few weeks ago. It's available on Blinkit today." |
| Replenishment | "You purchased this Face Wash about 15 days ago. Based on your usual usage, you may need another one." |
| Weather | "Rainy weather is expected this week. You may want to add an umbrella or raincoat from your saved shopping list." |
| Seasonal | "Summer has started. Your saved sunscreen is available for quick delivery." |
| Event-based | "Your friend's birthday is approaching. You had previously saved a birthday gift in your Universal Shopping List." |
| Cross-category discovery | "You came to buy groceries today, but your saved Bluetooth Earbuds are also available on Blinkit." |
| Shopping completion | "You can complete more of your shopping today without ordering from another app." |

---

## User Actions on Recommendations

For each recommendation, the user can:

- **Add to Cart**
- **Save for Later**
- **Dismiss Recommendation**

---

## Design & Product Constraints

### Do

- Treat USL as long-term memory across sessions and categories
- Show recommendations only at checkout
- Explain why each recommendation is shown
- Respect location-based availability
- Update USL after purchase while keeping unresolved items
- Use contextual signals (weather, season, events, replenishment) when relevant

### Do Not

- Interrupt browsing with recommendations
- Recommend random or unrelated products
- Show recommendations without explanation
- Limit the USL to groceries or Blinkit-only items
- Assume the user only shops for today's needs

---

## Expected Outcome

USL reduces shopping leakage to competing platforms by reminding users of intent they already expressed. Checkout becomes the moment to consolidate cross-category purchases into one Blinkit order—driving higher AOV, CLV, cross-category adoption, and overall shopping completion through personalized, natural recommendations.

---

## Static Dataset

Development and catalog-matching work uses the Blinkit product static dataset:

**[USL Static Dataset (Google Sheets)](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651)**

Use this sheet for mock catalog data, SKU metadata, category mappings, and local integration testing when Blinkit staging APIs are unavailable.

---

## Tech Stack (Free)

USL uses a **zero-cost development stack**. Full details in [architecture §18](./architecture.md#18-tech-stack--free--open-source).

| Layer | Tool |
| --- | --- |
| **UI design** | [Google Stitch](https://stitch.withgoogle.com) |
| **Frontend** | React + Vite → deployed on **[Vercel](https://vercel.com)** |
| **Backend** | FastAPI or Express.js → deployed on **[Railway](https://railway.app)** |
| **LLM** | [Groq API](https://console.groq.com) — `llama-3.3-70b-versatile` |
| **Database** | PostgreSQL + pgvector (Railway Postgres plugin / Docker local) |
| **Cache / Queue** | Redis + BullMQ or Celery (Railway Redis plugin) |
| **Search** | Meilisearch (OSS) + pgvector embeddings |
| **Embeddings** | sentence-transformers (local, free) |
| **Weather** | Open-Meteo (free, no API key) |
| **CI/CD** | GitHub Actions → Vercel + Railway |
| **Monitoring** | Grafana Cloud + Sentry (free tiers) |

**Deployment split:** Stitch designs the UI → React implements it → **Vercel** hosts the frontend → **Railway** hosts API, worker, Postgres, and Redis.

---

## Reference

- Full problem statement and detailed user journey: [`ProblemStatement.md`](./ProblemStatement.md)
- System architecture: [`architecture.md`](./architecture.md)
- Implementation plan: [`implementation-plan.md`](./implementation-plan.md)
- Edge cases & QA catalog: [`edge-cases.md`](./edge-cases.md)
