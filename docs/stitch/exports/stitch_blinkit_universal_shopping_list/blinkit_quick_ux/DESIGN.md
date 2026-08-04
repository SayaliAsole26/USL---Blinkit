---
name: Blinkit Quick-UX
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1b1b'
  on-surface-variant: '#3f4a3c'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#6f7a6a'
  outline-variant: '#becab7'
  surface-tint: '#006e16'
  primary: '#006714'
  on-primary: '#ffffff'
  primary-container: '#0c831f'
  on-primary-container: '#e0ffd7'
  inverse-primary: '#74dd6e'
  secondary: '#755b00'
  on-secondary: '#ffffff'
  secondary-container: '#ffcb13'
  on-secondary-container: '#6f5700'
  tertiary: '#523fcc'
  on-tertiary: '#ffffff'
  tertiary-container: '#6b5be6'
  on-tertiary-container: '#f9f4ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#8ffb87'
  primary-fixed-dim: '#74dd6e'
  on-primary-fixed: '#002203'
  on-primary-fixed-variant: '#00530e'
  secondary-fixed: '#ffe08e'
  secondary-fixed-dim: '#f2c000'
  on-secondary-fixed: '#241a00'
  on-secondary-fixed-variant: '#584400'
  tertiary-fixed: '#e4dfff'
  tertiary-fixed-dim: '#c6bfff'
  on-tertiary-fixed: '#160066'
  on-tertiary-fixed-variant: '#4029ba'
  background: '#fcf9f8'
  on-background: '#1b1b1b'
  surface-variant: '#e5e2e1'
  ai-surface: '#F0EDFF'
  ai-text: '#6C5CE7'
  price-red: '#E74C3C'
  surface-gray: '#F4F6F8'
  border-subtle: '#E8ECEF'
typography:
  display-hero:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 24px
  section-title:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '700'
    lineHeight: 20px
  body-primary:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-medium:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  body-secondary:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  badge-label:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '700'
    lineHeight: 14px
  cta-text:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 16px
  price-display:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  margin-page: 1rem
  gutter-card: 0.75rem
  stack-sm: 0.25rem
  stack-md: 0.5rem
  stack-lg: 1rem
---

## Brand & Style

The design system is built for speed, utility, and modern commerce. It captures the high-energy, "instant gratification" nature of quick-commerce while introducing a sophisticated, intelligent layer for the Universal Shopping List feature.

The aesthetic follows a **Corporate / Modern** direction with **Minimalist** influences. It prioritizes clarity through a stark white canvas, punchy brand accents, and a clear typographic hierarchy. The intelligence of the system—driven by AI—is signaled through a distinctive violet accent, creating a visual "safe space" for smart recommendations within the fast-paced shopping environment. The overall mood is approachable, trustworthy, and incredibly efficient.

## Colors

This design system uses a strategic color palette to drive user behavior and highlight smart features:

- **Primary Green:** Reserved for success states, completion, and primary conversion actions (Add to Cart, Save List).
- **Brand Yellow:** Used sparingly for high-level brand moments and urgent callouts.
- **AI Violet:** A dedicated functional color used exclusively for "Smart" features, including the Shopping Completion Score and AI-categorized badges.
- **Neutrals:** A range of grays from `#1C1C1C` for readability to `#F4F6F8` for soft background layering and containment.

## Typography

The typography system is designed for high-density mobile information. **Inter** is the standard for its exceptional legibility at small sizes.

Key rules:
- **Prices:** Always use `price-display` for visibility. Strikethrough prices should use `body-secondary` in a muted gray or red.
- **Hierarchy:** Use `section-title` for grouping items in the Universal Shopping List to ensure the list remains scannable.
- **Action:** Button labels should always be centered with `cta-text` to ensure they feel substantial and tappable.

## Layout & Spacing

The layout is optimized for a single-column mobile experience. It utilizes a **Fluid Grid** with a consistent 16px (`1rem`) side margin.

- **Vertical Rhythm:** Elements are stacked using 4px, 8px, and 16px increments. 
- **Product Grids:** When displaying search results or suggestions, a 2-column fluid layout is used with 12px gutters.
- **Safe Areas:** Buttons are typically anchored to the bottom of the screen with a 16px padding from the bottom edge or within a fixed sticky container.

## Elevation & Depth

Depth is used to distinguish the "shopping canvas" from actionable containers.

- **Tonal Layers:** The primary background is white. Secondary information (like the list category headers or inactive list items) uses the `surface-gray` tier.
- **Soft Shadows:** Cards use a very subtle drop shadow: `0px 4px 12px rgba(0,0,0,0.05)`. This creates a sense of "lift" without visual clutter.
- **Bottom Sheets:** Use a higher elevation with a backdrop dim (40% black) to focus the user on "Add" or "Edit" actions.

## Shapes

The shape language is friendly and modern, moving away from sharp edges to create a "softer" utility feel.

- **Cards:** Use a standard 12px radius.
- **Buttons:** Primary CTAs use 12px, while smaller "Add" buttons or "Pills" use a 10px or full pill (circular) radius.
- **Input Fields:** 10px radius with a subtle 1px border.
- **Bottom Sheets:** 24px top-only radius to create a distinct "drawer" feel.

## Components

### AI Signal Pill
Used to denote AI-driven categorization or insights. 
- **Style:** `ai-surface` background, `ai-text` color.
- **Iconography:** Leading "✨" (sparkle) icon in 12px size.
- **Typography:** `badge-label`.

### Shopping Completion Score Widget
A high-visibility card placed in the cart or dashboard.
- **Structure:** Card container with 12px radius. 
- **Visuals:** A horizontal progress bar using `primary-green` for the filled state and `border-subtle` for the track.
- **Text:** Displays a percentage (e.g., "82%") using `headline-sm` in `ai-text`.

### Buttons
- **Primary:** Solid `#0C831F` with white text. 48px height.
- **Add Product:** Outline button with 1px `primary-green` border and green text. Transitions to solid green when "Added".

### Product Cards
- **Structure:** Vertical layout for grids, horizontal for lists.
- **Details:** Must include Image, Title (`body-medium`), Price (`price-display`), and the "Add" action clearly separated.

### Checkboxes & List Items
- **Checked State:** Circle icon with solid `primary-green` fill and white checkmark.
- **List Item:** 1px `border-subtle` bottom divider; 12px vertical padding.