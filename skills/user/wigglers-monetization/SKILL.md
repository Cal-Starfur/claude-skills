---
name: wigglers-monetization
description: >
  Wigglers Room monetization strategy and implementation guide. Covers
  Reddit Developer Funds 2026 payout tiers, Devvit in-app payments via
  Reddit Gold (useProducts API), and Revenue OS audit commands. Load this
  skill when discussing Wigglers Room revenue, pricing, adding purchasable
  items, tracking Daily Qualified Engagers, or running a monetization audit.
  Triggers on: "how do we make money", "add payments", "Reddit Gold",
  "developer funds", "payout tiers", "monetize", "in-app purchase",
  "useProducts", "/ros", "revenue audit".
---

# Wigglers Room — Monetization Skill

## Three Revenue Channels

### Channel 1 — Reddit Developer Funds 2026
**Program runs April 1, 2025 → July 31, 2026. Wigglers Room launches July 1.**

**Payout tiers (one-time per tier, per app):**

| Threshold | Payout |
|---|---|
| 500 Daily Qualified Engagers (7-day rolling avg) | $500 |
| 1,000 DQE | $1,000 |
| 5,000 DQE | $2,500 |
| 10,000 DQE | $5,000 |
| 250 Qualified Installs (in 1,000+ member subs) | $1,000 |
| 1,000 Qualified Installs | $5,000 |

**DQE Rules:**
- Must be logged-in Reddit users
- Community must have 200+ members
- Community must be SFW / eligible for monetization
- No bots or spam — Reddit audits this

**What counts as an engagement for Wigglers Room:**
Any interaction with the game post (opening the bin, placing worms, collecting tea, checking karma). Idle games naturally accumulate engagements — daily check-ins are built into the loop.

**Action items:**
- Register for Developer Funds at r/devvit if not already done
- Ensure the subreddit Wigglers Room is installed in has 200+ members
- Track DQE via Devvit analytics dashboard after launch

---

### Channel 2 — In-App Payments (Reddit Gold)
**Implementation: `useProducts` hook from `@devvit/public-api`**

Reddit Gold is Reddit's virtual currency. Users buy Gold with real money and spend it in Devvit apps.

**How it works in Wigglers Room:**
```
Player buys Reddit Gold on Reddit → Player sees Gold purchase button in game
→ `useProducts` triggers Reddit's native payment flow → Reddit handles transaction
→ Your server-side `onPurchase` handler fires → Grant the item in KV store
```

**Suggested purchasable items for Wigglers Room:**

| Item | Gold Price | Description |
|---|---|---|
| Tunnel Glow Pack | 50 Gold | Unlocks amber/purple/rainbow tunnel glow colors |
| Worm Speed Boost | 25 Gold | 2x worm movement speed for 24 hours |
| Compost Accelerator | 30 Gold | 2x casting rate for 24 hours |
| Premium Worm Skin | 75 Gold | Rare worm appearance (glowing, spotted, golden) |
| Mega Bin | 100 Gold | Unlock a second, larger worm bin |
| Worm Tea Flask | 40 Gold | +50% worm tea output for 24 hours |

**Key API pattern (from reddit/devvit-payments-example):**
```typescript
// In devvit.json — define your products
"products": [
  {
    "sku": "tunnel_glow_pack",
    "displayName": "Tunnel Glow Pack",
    "description": "Unlock special tunnel glow colors",
    "price": 50,
    "images": { "icon": "assets/glow-icon.png" }
  }
]

// In client — trigger purchase
const { purchase } = useProducts();
await purchase('tunnel_glow_pack');

// In server — handle fulfillment
Devvit.addPaymentHandler({
  fulfillOrder: async ({ productSku, userId }, { redis }) => {
    if (productSku === 'tunnel_glow_pack') {
      await redis.hset(`user:${userId}:unlocks`, { tunnelGlow: 'true' });
    }
    return { success: true };
  }
});
```

**Files to reference:**
- `payments-sdk/src/server/index.ts` — full server-side payment handler
- `payments-sdk/src/client/hooks/usePurchase.ts` — client hook pattern
- `payments-sdk/devvit.json` — product definition format

---

### Channel 3 — Revenue OS Audit
**Run `/ros audit` to score Wigglers Room's monetization readiness.**

Available Revenue OS commands:
- `/ros` — overview and readiness score
- `/ros icp` — who is the ideal Wigglers Room player that would spend Gold?
- `/ros value-prop` — sharpen the "why play Wigglers Room" message
- `/ros pricing` — validate Gold pricing against psychology frameworks
- `/ros competitors` — how do other idle Reddit games monetize?
- `/ros first-dollar` — fastest path to first real revenue
- `/ros audit` — full monetization audit with action plan

---

## Priority Order for July 1 Launch

1. **Register for Developer Funds** — takes 5 minutes, unlocks $500+ in milestone payments
2. **Add 1 purchasable item** — Tunnel Glow Pack is the highest-fit first item (visual, non-pay-to-win, tied to the #1 marketing asset)
3. **Ensure install subreddit has 200+ members** — required for DQE to count
4. **Run `/ros first-dollar`** — find fastest path to first Gold transaction
5. **Run `/ros audit`** — full monetization readiness score

---

## Notes
- Reddit handles all payment processing — no Stripe, no PayPal, no tax complexity
- Gold purchases are non-refundable by Reddit policy
- Items must be cosmetic or time-limited — pay-to-win is banned by Devvit guidelines
- Revenue splits: Reddit takes a cut of Gold (typically ~30%), developer gets remainder
- Wigglers Room Jr. (kids edition) should have ZERO paid items — keep that edition clean
