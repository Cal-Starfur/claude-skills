---
name: wigglers-monetization
description: Wigglers Room monetization strategy and implementation guide. Load when discussing revenue, Reddit Developer Funds payouts, in-app Gold purchases, or adding purchasable items to the game. Covers Dev Fund tier tracking, useProducts hook integration, and product design for Wigglers Room specifically.
---

# Wigglers Room Monetization Skill

## Two Revenue Channels

### Channel 1 — Reddit Developer Funds 2026
Program runs April 1, 2025 → July 31, 2026. Wigglers Room launches July 1.

**Payout tiers (one-time per tier):**
| Threshold | Payout |
|---|---|
| 500 Daily Qualified Engagers (7-day rolling avg) | $500 |
| 1,000 DQEs | Higher tier (check current terms) |
| 250 Qualified Installs (communities 1,000+ members) | $1,000 |

**DQE Rules:**
- User must be logged in
- In a community with 200+ members
- Community must be SFW / eligible under Earn Policy
- No bots or manipulation
- Up to 3 apps per developer qualify

**What this means for Wigglers Room:**
- Post to large SFW subs (r/incremental_games ~500k, r/GrowAGarden ~200k, r/compost ~150k)
- Each engaged player in those subs = 1 DQE
- 500 DQEs over a 7-day rolling window = first $500

### Channel 2 — In-App Reddit Gold Purchases (useProducts)
Reddit's payments SDK lets players spend Gold inside the game.

**Integration pattern (from reddit/devvit-payments-example):**

In `devvit.json` define products:
```json
{
  "products": [
    {
      "sku": "tunnel_glow_pack",
      "displayName": "Tunnel Glow Pack",
      "description": "Unlock amber, violet, and cyan tunnel glow colors",
      "price": 25,
      "images": { "icon": "assets/glow-icon.png" },
      "metadata": { "type": "cosmetic" }
    }
  ]
}
```

In client, use `usePurchase` hook:
```typescript
import { usePurchase } from './hooks/usePurchase';
const { purchase, isPurchasing } = usePurchase();
await purchase('tunnel_glow_pack');
```

In server `index.ts`, handle fulfillment:
```typescript
Devvit.addPaymentHandler({
  fulfillOrder: async ({ productSku, userId }) => {
    if (productSku === 'tunnel_glow_pack') {
      await redis.hset(`user:${userId}:unlocks`, { tunnelGlowPack: 'true' });
    }
    return { success: true };
  }
});
```

## Wigglers Room Product Ideas (Cosmetic / Non-P2W)

| Product | SKU | Gold Price | Notes |
|---|---|---|---|
| Tunnel Glow Pack | `tunnel_glow_pack` | 25 | Amber/violet/cyan glow colors |
| Golden Worm Skin | `golden_worm` | 50 | Cosmetic only, same physics |
| Cozy Bin Theme | `cozy_bin_theme` | 30 | Dark wood + fairy lights UI skin |
| Worm Name Tag | `worm_nametag` | 10 | Name your lead worm |
| Casting Rain | `casting_rain` | 75 | Visual effect: castings rain from top |

**Philosophy: cosmetic only, never gameplay advantage.**
Wigglers Room is an idle compost game — pay-to-win would kill the community.
Gold purchases = prestige + personalization, not faster worms.

## Dev Fund Strategy for July Launch

1. Launch July 1 in r/Wigglers subreddit (create it if needed)
2. Immediately cross-post to r/incremental_games, r/GrowAGarden, r/compost
3. Target 200+ active players = first DQE threshold
4. 500 daily average over 7 days = $500 payout
5. 250 qualified installs (large subs) = $1,000 payout

## Running /ros on Wigglers Room
Load revenue-os skill and run:
- `/ros icp` → Who is the Wigglers Room player? (idle gamer + composter crossover)
- `/ros value-prop` → Why does Wigglers Room exist vs other idle games?
- `/ros pricing` → What should Gold products cost?
- `/ros first-dollar` → Fastest path to first revenue before July 31
