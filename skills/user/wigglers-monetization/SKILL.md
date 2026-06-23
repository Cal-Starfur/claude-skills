---
name: wigglers-monetization
description: >
  Wigglers Room monetization strategy and implementation skill. Load this when
  planning in-app purchases, Reddit Gold products, Developer Funds targets,
  pricing, or any revenue discussion for Wigglers Room or Wigglers Room Jr.
  Covers three revenue channels: Reddit Developer Funds 2026, Devvit in-app
  payments (Reddit Gold), and future Wigglers Room Jr. premium product.
  Triggers on: "monetize", "revenue", "gold", "payments", "products",
  "how do we make money", "developer funds", "payout", "pricing", "shop",
  "what should we sell", "in-app purchase", "wigglers jr pricing".
---

# Wigglers Room — Monetization Skill

## Context

- **Game:** Wigglers Room — multiplayer idle worm composting simulator on Devvit
- **Developer:** Cal Starfur — solo dev, iPhone-only, launches July 1 2026
- **Future product:** Wigglers Room Jr. — kids edition ages 5-7, additive only, star rewards
- **Platform:** Devvit web experience, hosted by Reddit, KV store backend
- **Marketing:** 160 scheduled posts, 8 target subreddits, pre-launch posts begin June 23

---

## Revenue Channel 1 — Reddit Developer Funds 2026

Program runs April 1 2025 to July 31 2026. Cal qualifies. 30 days post-launch to hit tiers.

### Payout Tiers (one-time per tier per app)

| Threshold | Payout |
|---|---|
| 500 Daily Qualified Engagers (7-day rolling avg) | $500 |
| 2,500 Daily Qualified Engagers | $2,500 |
| 10,000 Daily Qualified Engagers | $10,000 |
| 250 Qualified Installs in 1,000+ member subs | $1,000 |
| 1,000 Qualified Installs | $5,000 |

Rules: DQE = unique logged-in user in 200+ member SFW sub. Max 3 apps per developer.

### Install Strategy
- Priority subs for Qualified Installs: r/compost (180k), r/incremental_games (300k+), r/CozyGamers
- Idle loop + weekly drain = natural daily return = DQE accumulation
- Tunnel glow GIF on launch day is the single highest-conversion asset

---

## Revenue Channel 2 — Devvit In-App Payments (Reddit Gold)

Products defined in devvit.json. Client uses usePurchase hook. Server fulfills via endpoint.
Price reference: 1 Gold is approximately $0.01 USD.
Sweet spot: 25-100 Gold for cosmetics, 50-200 Gold for boosts.

### Wigglers Room Product Lineup

COSMETICS (no gameplay impact):
- glow-amber | Amber Glow Pack | 25 Gold | Warm amber tunnel glow
- glow-neon | Neon Glow Pack | 25 Gold | Electric green tunnel glow
- glow-cosmic | Cosmic Glow Pack | 50 Gold | Deep purple galaxy glow
- worm-gold | Golden Worm Skin | 50 Gold | Gold-tinted worm segments
- worm-rainbow | Rainbow Worm Skin | 75 Gold | Colour-shifting worm
- theme-moonlight | Moonlight Bin Theme | 100 Gold | Dark aesthetic skin
- name-worm | Name Your Worm | 25 Gold | Permanent worm nickname

BOOSTS (time-limited, weekly cap — not pay-to-win):
- boost-compost | Compost Boost | 50 Gold | 2x castingEnrichment for 1 hour
- boost-worm | Worm Boost | 75 Gold | +2 worms for 24 hours
- boost-tea | Tea Boost | 50 Gold | Worm tea drains slower for 1 hour

### Implementation Files
See skills/user/devvit-payments/src/ for working TypeScript patterns:
- src/client/hooks/usePurchase.ts — client purchase hook
- src/server/index.ts — server fulfillment endpoint
- devvit.json — product definition schema

CRITICAL: Add all products to devvit.json BEFORE Reddit App Review submission.
Payment product changes require a new review cycle.

---

## Revenue Channel 3 — Wigglers Room Jr. (Post-Launch)

Model: Standalone paid product or premium IAP inside main game.
Target: Parents of 5-7 year olds, educators, r/Parenting, r/HomesteadingToday.
Pricing anchor: $2.99-$4.99 one-time.
Constraint: No FOMO, no timers, additive stars only.
Earliest date: September 2026 after launch stabilisation.

---

## Marketing x Monetization Integration

Dev Story posts: explain how Reddit Gold cosmetics work — drives curiosity
Worm Story posts: educational content — builds r/compost audience = Qualified Installs
Gamer Story posts: tunnel glow GIF — drives daily engagement = Qualified Engagers
Skills Story posts: r/ClaudeAI, r/SoloDev — credibility, not direct revenue

Key insight: 500 returning daily players for 7 days = first $500 payout.
That is the July launch target.

---

## Revenue OS Commands (load revenue-os skill for full implementation)

- /ros icp — who exactly is the Wigglers Room player
- /ros pricing — validate Gold price points against psychology data
- /ros value-prop — sharpen the worm composting simulator hook
- /ros audit — full monetization readiness score before July 1
- /ros first-dollar — fastest path to first Gold purchase in-game

---

## Risks

- Pay-to-win perception: r/incremental_games is allergic to P2W. All paid items must be
  cosmetic or time-limited boosts with weekly caps. State this explicitly in launch posts.
- Gold conversion rate: Reddit Gold pricing can change. Never promise specific USD to players.
- Program ends July 31: Need Qualified Installs in large subs within first 2 weeks of launch.
- App Review lag: Payment product changes require Reddit App Review. Add upfront.
