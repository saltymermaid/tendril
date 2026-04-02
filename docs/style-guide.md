# Tendril — Style Guide & Design System

## Overview

Tendril uses a garden-inspired design system built on CSS custom properties (design tokens). The system supports light mode, dark mode (via `prefers-color-scheme`), and is optimized for iPhone PWA usage.

---

## Color Palette

### Primary — Garden Greens
| Token | Value | Usage |
|---|---|---|
| `--color-green-50` | `#f0fdf4` | Subtle backgrounds, hover states |
| `--color-green-100` | `#dcfce7` | Badges, light fills |
| `--color-green-200` | `#bbf7d0` | Focus rings, borders |
| `--color-green-300` | `#86efac` | Decorative accents |
| `--color-green-400` | `#4ade80` | Active states |
| `--color-green-500` | `#22c55e` | Primary light |
| `--color-green-600` | `#16a34a` | Success, primary actions |
| `--color-green-700` | `#15803d` | **Primary color** |
| `--color-green-800` | `#166534` | Header gradient |
| `--color-green-900` | `#14532d` | Primary dark |
| `--color-green-950` | `#052e16` | Deepest green |

### Secondary — Earth Tones
| Token | Value | Usage |
|---|---|---|
| `--color-earth-50` | `#faf6f1` | Fallow soil squares |
| `--color-earth-100` | `#f0e6d6` | Grid bed backgrounds |
| `--color-earth-200` | `#e0ccad` | Borders on soil elements |
| `--color-earth-300` – `900` | Warm browns | Accents, badges |

### Neutral — Grays
Standard gray scale from `--color-gray-50` (#f9fafb) to `--color-gray-900` (#111827).

### Semantic Colors
| Token | Usage |
|---|---|
| `--color-primary` | Main interactive color (green-700) |
| `--color-primary-light` | Hover/active variant (green-500) |
| `--color-primary-dark` | Pressed state (green-900) |
| `--color-background` | Page background (gray-50) |
| `--color-surface` | Card/panel background (white) |
| `--color-text` | Primary text (gray-900) |
| `--color-text-secondary` | Secondary text (gray-600) |
| `--color-border` | Borders and dividers (gray-200) |
| `--color-error` | Error states (#dc2626) |
| `--color-success` | Success states (green-600) |
| `--color-warning` | Warning states (#f59e0b) |

### Category Colors
Each plant category has a dedicated color for visual distinction:
| Category | Token | Color |
|---|---|---|
| Tomatoes | `--cat-tomatoes` | `#e53e3e` |
| Peppers | `--cat-peppers` | `#dd6b20` |
| Herbs | `--cat-herbs` | `#38a169` |
| Leafy Greens | `--cat-leafy-greens` | `#2f855a` |
| Root Vegetables | `--cat-root-vegetables` | `#975a16` |
| Squash | `--cat-squash` | `#d69e2e` |
| Legumes | `--cat-legumes` | `#68d391` |
| Brassicas | `--cat-brassicas` | `#4299e1` |
| Alliums | `--cat-alliums` | `#9f7aea` |
| Cucurbits | `--cat-cucurbits` | `#48bb78` |
| Flowers | `--cat-flowers` | `#ed64a6` |
| Melons | `--cat-melons` | `#f6ad55` |
| Corn | `--cat-corn` | `#ecc94b` |
| Tropical | `--cat-tropical` | `#f687b3` |

---

## Typography

**Font Family:** System font stack (`-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, ...`)

| Token | Size | Usage |
|---|---|---|
| `--font-size-xs` | 0.75rem (12px) | Badges, meta text |
| `--font-size-sm` | 0.875rem (14px) | Secondary text, nav links |
| `--font-size-base` | 1rem (16px) | Body text |
| `--font-size-lg` | 1.125rem (18px) | Section headings |
| `--font-size-xl` | 1.25rem (20px) | Page headings |
| `--font-size-2xl` | 1.5rem (24px) | Major headings |
| `--font-size-3xl` | 1.875rem (30px) | Login title |

---

## Spacing

8-point grid system using `--space-*` tokens:

| Token | Value |
|---|---|
| `--space-1` | 0.25rem (4px) |
| `--space-2` | 0.5rem (8px) |
| `--space-3` | 0.75rem (12px) |
| `--space-4` | 1rem (16px) |
| `--space-5` | 1.25rem (20px) |
| `--space-6` | 1.5rem (24px) |
| `--space-8` | 2rem (32px) |
| `--space-10` | 2.5rem (40px) |
| `--space-12` | 3rem (48px) |

---

## Border Radius

| Token | Value | Usage |
|---|---|---|
| `--radius-sm` | 0.25rem | Small elements, badges |
| `--radius-md` | 0.5rem | Buttons, inputs |
| `--radius-lg` | 0.75rem | Cards, panels |
| `--radius-xl` | 1rem | Login card, modals |
| `--radius-full` | 9999px | Pills, avatars |

---

## Shadows

| Token | Usage |
|---|---|
| `--shadow-sm` | Subtle card elevation |
| `--shadow-md` | Elevated cards, forms |
| `--shadow-lg` | Modals, login card |

---

## Components

### Buttons
| Class | Usage |
|---|---|
| `.btn` | Base button (44px min touch target) |
| `.btn-primary` | Primary action (green) |
| `.btn-outline` | Ghost button (for dark backgrounds) |
| `.btn-outline-dark` | Ghost button (for light backgrounds) |
| `.btn-danger` | Destructive action (red) |
| `.btn-success` | Positive action (green) |
| `.btn-sm` | Compact button (36px min touch target) |
| `.btn-google` | Google OAuth button |
| `.btn-dev` | Dev login button |

### Cards
| Class | Usage |
|---|---|
| `.detail-card` | Content card with shadow |
| `.form-card` | Form container card |
| `.dashboard-card` | Dashboard widget card |
| `.category-card` | Catalog category card (hover lift) |
| `.container-card` | Container list card |
| `.overview-card` | Garden overview card |

### Forms
| Class | Usage |
|---|---|
| `.form-group` | Form field wrapper |
| `.form-label` | Field label |
| `.form-help` | Help text below field |
| `.form-row` | Two-column form layout |
| `.input` | Text input / select |
| `.textarea` | Multi-line input |
| `select.input` | Custom select with arrow |

### Status Badges
| Class | Usage |
|---|---|
| `.status-badge.not_started` | Gray — planned |
| `.status-badge.in_progress` | Green — active |
| `.status-badge.complete` | Earth — finished |
| `.badge-primary` | Green pill |
| `.badge-warning` | Amber pill |
| `.badge-error` | Red pill |
| `.badge-info` | Blue pill |

### Modals
| Class | Usage |
|---|---|
| `.modal-overlay` | Full-screen backdrop |
| `.modal-content` | Modal panel (560px max) |
| `.modal-content.modal-sm` | Small modal (420px max) |
| `.modal-header` | Title + close button |
| `.modal-actions` | Bottom action buttons |

---

## Visual Motif — Tendril Vine

The tendril vine motif is a decorative SVG element used throughout the app:

- **`.tendril-motif`** — Small inline vine (120×24px)
- **`.tendril-motif-lg`** — Large centered vine (200×40px)
- **Login card** — Vine accent at bottom via `::after`
- **Header** — Gradient vine accent line via `::after`

---

## Animations & Transitions

| Name | Duration | Usage |
|---|---|---|
| `fadeInUp` | 0.3s | Page content entrance |
| `shimmer` | 1.5s | Loading skeleton |
| `spin` | 0.8s | Loading spinner |
| `pulse` | 1.5s | Status dot loading |
| `--transition-fast` | 0.15s | Hover states |
| `--transition-normal` | 0.25s | Card transitions |
| `--transition-slow` | 0.35s | Complex animations |

All animations respect `prefers-reduced-motion: reduce`.

---

## Loading States

| Class | Usage |
|---|---|
| `.loading-spinner` | Inline spinner (24px) |
| `.loading-spinner.lg` | Large spinner (40px) |
| `.loading-center` | Centered loading with text |
| `.skeleton` | Base skeleton shimmer |
| `.skeleton-text` | Text line skeleton |
| `.skeleton-text.short` | 60% width text skeleton |
| `.skeleton-text.medium` | 80% width text skeleton |
| `.skeleton-card` | Card-shaped skeleton |
| `.skeleton-circle` | Avatar/icon skeleton |

---

## Empty & Error States

| Class | Usage |
|---|---|
| `.empty-state` | Centered empty message with icon |
| `.empty-state-sm` | Compact empty state |
| `.error-state` | Error message with icon and retry |

---

## Accessibility

- **Touch targets:** All interactive elements have 44px minimum height/width
- **Focus visible:** 2px green outline on keyboard focus
- **Reduced motion:** All animations disabled when `prefers-reduced-motion: reduce`
- **Color contrast:** Text meets WCAG AA contrast ratios
- **Category colors:** Chosen for distinguishability (not relying on color alone)

---

## Dark Mode

Dark mode activates automatically via `prefers-color-scheme: dark`. Key changes:
- Background shifts to deep forest green (`#0f1a0a`)
- Surface becomes dark green (`#1a2614`)
- Text inverts to light green-tinted white
- Shadows become more pronounced
- Images slightly dimmed (92% opacity)
- Error/warning backgrounds use dark variants

---

## Responsive Breakpoints

| Breakpoint | Target |
|---|---|
| `≤ 390px` | iPhone SE / Mini |
| `≤ 480px` | Small phones |
| `≤ 640px` | Large phones |
| `≤ 768px` | Tablets |

### PWA Standalone Mode
When running as installed PWA on mobile:
- Header becomes sticky
- Navigation moves to bottom tab bar
- Pull-to-refresh disabled
- Safe area insets applied

---

## Print Styles

Header, navigation, buttons, and modals are hidden. Cards lose shadows and get simple borders.
