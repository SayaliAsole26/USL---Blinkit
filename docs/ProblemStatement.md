# Problem Statement

## Universal Shopping List (USL) — AI-Powered Cross-Category Recommendation Engine

### Background

Users rarely shop from a single e-commerce platform. They purchase products across Blinkit, Amazon, Nykaa, Flipkart, Myntra, Zepto, and many other apps depending on the category they need. Although Blinkit has expanded far beyond groceries, most users still perceive it as a grocery-only platform.

As a result, when users need products such as skincare, electronics, home essentials, pet supplies, baby products, gifting items, or personal care products, they either purchase them from other apps or simply forget to buy them. This causes shopping intent to leak outside Blinkit, reducing cross-category purchases and limiting customer lifetime value.

The core problem is that users do not have a single place to remember everything they intend to buy online, and Blinkit has no persistent memory of those future shopping needs.

---

## Objective

Build an AI-powered **Universal Shopping List (USL)** that acts as the user's long-term shopping memory.

Instead of remembering only what the user wants to buy today, the application should remember everything the user intends to purchase online in the future, regardless of which platform they originally planned to use.

The Universal Shopping List becomes a persistent memory that powers intelligent recommendations during every Blinkit shopping session.

The goal is not to interrupt shopping but to remind users of relevant products at the perfect moment—just before checkout—using contextual, human-like reasoning.

Ultimately, the product should increase:

- Cross-category purchases
- Average Order Value (AOV)
- Customer Lifetime Value (CLV)
- Product discovery
- Shopping completion
- User convenience

---

## User Journey

### Step 1 — Capture User Location

When a user opens the application for the first time, collect:

- City
- State
- Pincode

This location determines product availability throughout the experience.

---

### Step 2 — Create Universal Shopping List

After onboarding, users create a Universal Shopping List.

Unlike a grocery shopping list, this list contains **everything** the user may buy online in the future.

Examples:

- Face Wash
- AirPods
- Dog Food
- Bedsheet
- Hair Dryer
- Protein Powder
- Birthday Gift
- Coffee Machine
- Extension Board
- Moisturizer
- Printer Ink

The Universal Shopping List is platform-agnostic.

It is not limited to Blinkit products.

Its purpose is to capture future shopping intent.

This list serves as the user's persistent shopping memory.

---

### Step 3 — AI Processes the Universal Shopping List

Every item entered into the USL is automatically processed.

The system should:

- Understand the user's intent.
- Categorize the product.
- Match it with Blinkit's catalog.
- Determine availability for the user's location.
- Store structured metadata for future recommendations.

The Universal Shopping List continuously evolves and becomes the user's long-term shopping memory.

---

### Step 4 — Normal Blinkit Shopping Experience

Users browse Blinkit exactly as they normally would.

They:

- Search products
- Browse categories
- Add groceries and essentials to the cart

No recommendations should interrupt this browsing experience.

---

### Step 5 — AI Recommendation at Checkout

When the user reaches the checkout page, the recommendation engine is triggered.

Instead of recommending random products, the AI uses the Universal Shopping List as long-term memory.

The engine compares:

- Universal Shopping List
- Current Cart
- Blinkit Product Catalog
- User Location
- Product Availability
- Purchase History (if available)
- Previous Recommendation History
- Seasonal Context
- Weather Context
- Event Context
- Replenishment Patterns
- Cross-Category Relationships

The AI then selects the most relevant products that the user has already expressed an intent to buy.

---

### Human-Like Recommendation Logic

Recommendations should feel like a helpful shopping companion rather than a generic recommendation engine.

Examples include:

#### Memory Reminder

> "You added this Face Wash to your Universal Shopping List a few weeks ago. It's available on Blinkit today."

#### Replenishment Reminder

> "You purchased this Face Wash about 15 days ago. Based on your usual usage, you may need another one."

#### Weather Context

> "Rainy weather is expected this week. You may want to add an umbrella or raincoat from your saved shopping list."

#### Seasonal Context

> "Summer has started. Your saved sunscreen is available for quick delivery."

#### Event-Based Reminder

> "Your friend's birthday is approaching. You had previously saved a birthday gift in your Universal Shopping List."

#### Cross-Category Discovery

> "You came to buy groceries today, but your saved Bluetooth Earbuds are also available on Blinkit."

#### Shopping Completion

> "You can complete more of your shopping today without ordering from another app."

---

### Step 6 — User Decision

For every recommendation, users can:

- Add to Cart
- Save for Later
- Dismiss Recommendation

The recommendation should always explain **why** it is being shown.

Users should never see unexplained recommendations.

---

### Step 7 — Checkout

After optionally adding recommended products, the user proceeds with checkout.

The Universal Shopping List is updated automatically to reflect purchased items while retaining future shopping needs.

---

## Expected Product Outcome

The Universal Shopping List transforms Blinkit from a grocery app into a shopping memory platform.

Instead of recommending random products, the AI reminds users about products they already intended to purchase, using contextual reasoning that feels natural and personalized.

By surfacing relevant cross-category products at checkout, the system helps users consolidate purchases into a single order, reducing shopping leakage to competing platforms while increasing cross-category adoption, Average Order Value (AOV), Customer Lifetime Value (CLV), and overall shopping completion.

---

## Tech Stack & Deployment

| Concern | Choice |
| --- | --- |
| **UI design** | [Google Stitch](https://stitch.withgoogle.com) |
| **Frontend** | React + Vite on **[Vercel](https://vercel.com)** |
| **Backend** | FastAPI / Express on **[Railway](https://railway.app)** |
| **LLM** | Groq API (free tier) |
| **Database / cache** | Railway PostgreSQL + Redis plugins |

See [`architecture.md`](./architecture.md) §16 (deployment) and §18 (full stack).

---

## References

- Project context: [`context.md`](./context.md)
- System architecture: [`architecture.md`](./architecture.md)
- Implementation plan: [`implementation-plan.md`](./implementation-plan.md)
- Static dataset: [USL Static Dataset (Google Sheets)](https://docs.google.com/spreadsheets/d/17ZSEhQJDX9GuOes7RYIU23aGea-o179X/edit?gid=651319651#gid=651319651)
