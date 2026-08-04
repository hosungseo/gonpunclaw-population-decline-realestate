# DESIGN.md — 인구감소지역 부동산

Guided by [Impeccable](https://impeccable.style): distinctive type, tinted neutrals, no SaaS slop, hierarchy over decoration.

## SEED foundation bridge

The site remains static HTML/CSS/Vanilla JS. It does not bundle SEED React components or pretend to be a React integration. Instead, `assets/css/seed-foundation.css` maps the official SEED foundation model onto the existing interface:

- role-based colors: brand actions are separate from decline/interest/data states
- semantic layer colors: basement, default, floating, pressed
- relative typography scale for product UI, while the editorial display face remains in narrative sections
- shared spacing, radius, elevation, focus, pressed, and reduced-motion tokens

This keeps GitHub Pages simple while making the product surfaces behave consistently with SEED.

## Direction
**Editorial civic atlas** — 관보·지도실·정책 브리핑의 차분한 권위. Warm paper field, forest ink, copper signal.

## Type
| Role | Family | Notes |
|------|--------|--------|
| Display / H1–H2 | **Fraunces** | Soft serif, optical size, not Inter/Arial |
| Body / UI | **Pretendard** | Korean-first, high legibility |
| Mono / codes | **IBM Plex Mono** | LAWD codes, data captions |

Scale (approx): 12 / 14 / 16 / 18 / 22 / 28 / 36 / 48 / 64. Tight tracking only on large display.

## Color (always tinted — no pure black/gray)
| Token | Hex | Use |
|-------|-----|-----|
| `--bg` | `#efe8db` | Page field |
| `--paper` | `#fbf6ec` | Surfaces |
| `--ink` | `#18231c` | Text (green-black) |
| `--muted` | `#5a635c` | Secondary text |
| `--line` | `rgba(24,35,28,.12)` | Borders |
| `--accent` | `#1b5c48` | Primary actions, decline |
| `--accent-2` | `#a66b2b` | Interest, warmth |
| `--decline` | `#1b5c48` | Population-decline |
| `--interest` | `#8a5a22` | Interest regions |
| `--danger-soft` | `#7a3b32` | Warnings (tinted) |

Never gray-on-saturated-color for body copy. Hero text stays near-white on deep forest overlay.

## Layout
- Max content ~1120px; generous section rhythm (48–80px)
- Markets: list | map | panel — not nested cards-in-cards
- Sticky nav + sticky panel on desktop
- Mobile: search → list → panel → map

## Components
- **Buttons**: solid forest primary; outline secondary on paper; no glow
- **Badges**: pill, type-colored, high contrast
- **Charts**: flat bars, average line, captions with period
- **Tables**: quiet header wash, sortable headers, no zebra noise
- **Toast**: dark ink pill, short

## Motion
- 150–250ms ease for hovers
- No bounce/elastic
- Map interactions stay crisp (Leaflet)

## Anti-patterns (reject)
- Inter / system-ui as brand face
- Purple–blue gradients, glassmorphism stacks
- Icon tile above every heading
- Nested white cards inside cards
- Pure `#000` / `#666` / `#999`
- Investment ranking gamification
