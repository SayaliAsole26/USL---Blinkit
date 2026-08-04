# Stitch UI Design — USL Blinkit

Design all USL screens in **[Google Stitch](https://stitch.withgoogle.com)** before implementing in React.

## Phase 0 — Screens to design (Phase 1 preview)

| Screen | Purpose | Stitch checklist |
| --- | --- | --- |
| **Onboarding** | City, state, pincode capture | Location form, Blinkit-style branding |
| **USL Home** | List pending / purchased items | Empty state, add button, status filters |
| **Add Item** | Free-text cross-category intent | Input placeholder examples from problem statement |
| **Checkout Recommendations** | Memory + cross-category cards | Reason text, Add / Save / Dismiss actions |

## Implementation flow

```
Stitch mockups → React components (frontend/) → Deploy on Vercel
```

## Design tokens (suggested)

- Primary: Blinkit green `#00A651` (or project palette)
- Cards: white, 16px radius, soft shadow
- Reason text: secondary gray, readable at checkout

Export Stitch screens as reference PNGs into `docs/stitch/exports/` when ready.
