---
description: Design pricing architecture with psychology and market research
argument-hint: [analyze|design|psychology|model|implement]
allowed-tools: Read, WebSearch, Bash(cat:*), Write
---

# Pricing Architecture

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/pricing.json 2>/dev/null || echo '{"tiers": []}'`

## Pricing Psychology Reference

!`cat "${CLAUDE_PLUGIN_ROOT}/data/pricing-psychology.json" 2>/dev/null || echo '{}'`

## Industry Benchmarks

!`cat "${CLAUDE_PLUGIN_ROOT}/data/industry-benchmarks.json" 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS contains "analyze":

Research competitor pricing:
1. WebSearch for "[competitor] pricing"
2. Document tier structures
3. Identify market range
4. Compare to industry benchmarks

### If $ARGUMENTS is empty or "design":

1. **Load Context**
   - Read ICP data for budget expectations
   - Check industry benchmarks for pricing ranges
   - Review any existing pricing.json data

2. **Research Competitors** (WebSearch)
   - Search for competitor pricing pages
   - Document their tier structures and pricing
   - Note feature distribution across tiers

3. **Design Tier Structure**
   - Apply pricing psychology principles
   - Create 3 tiers (anchor, target, decoy)
   - Distribute features strategically
   - Set prices based on ICP budget and market

4. **Calculate Projections**
   - Revenue modeling at different customer counts
   - Break-even analysis if applicable

5. **Save Results**
   - Save to ~/.claude/revenue-os/pricing.json

### If $ARGUMENTS is "psychology":

Deep dive on pricing tactics:
- Explain each strategy from pricing-psychology.json
- Recommend which to apply based on product/ICP
- Show before/after examples
- Provide implementation guidance

### If $ARGUMENTS is "model":

Revenue modeling mode:
- Input: Number of customers, conversion rates
- Output: MRR/ARR projections
- Break-even analysis
- Growth scenarios (conservative, moderate, aggressive)

### If $ARGUMENTS is "implement":

Generate Stripe integration code:
- Product creation
- Price configuration
- Checkout session setup
- Webhook handling basics

## Output Format

```markdown
## Pricing Strategy: [Product Name]

### Market Research

**Competitor Pricing** (from web search)
| Competitor | Entry | Pro | Enterprise |
|------------|-------|-----|------------|
| [Comp 1] | $X/mo | $Y/mo | $Z/mo |
| [Comp 2] | $X/mo | $Y/mo | $Z/mo |

**Market Range**: $X - $Y/mo for similar products
**ICP Budget**: $X - $Y/mo (from ICP analysis)

---

### Recommended Pricing Architecture

| Tier | Monthly | Annual (17% off) | Target Customer |
|------|---------|------------------|-----------------|
| **Starter** | $29 | $24/mo | Price-sensitive, testing |
| **Pro** ⭐ | $79 | $66/mo | Serious users (target) |
| **Enterprise** | $249 | $207/mo | Teams, premium needs |

---

### Psychology Applied

- ✓ **Charm Pricing**: $79 not $80 (8-15% lift)
- ✓ **3-Tier Anchoring**: Enterprise makes Pro look reasonable
- ✓ **Decoy Effect**: Starter lacks key features, pushing to Pro
- ✓ **Annual Discount**: 17% off (~2 months free) for commitment
- ✓ **Visual Hierarchy**: Pro tier highlighted as "Most Popular"

---

### Feature Distribution

| Feature | Starter | Pro | Enterprise |
|---------|:-------:|:---:|:----------:|
| [Core Feature 1] | ✓ | ✓ | ✓ |
| [Core Feature 2] | ✓ | ✓ | ✓ |
| [Power Feature 1] | Limited | ✓ | ✓ |
| [Power Feature 2] | - | ✓ | ✓ |
| [Premium Feature] | - | - | ✓ |
| Priority Support | - | Email | Dedicated |
| Custom Integrations | - | - | ✓ |

---

### Revenue Projections

**At 100 customers** (typical distribution: 60% Starter, 35% Pro, 5% Enterprise):
- Monthly: $(60×29 + 35×79 + 5×249) = $4,740 MRR
- Annual: $56,880 ARR

**Growth Scenarios**:

| Customers | MRR | ARR |
|-----------|-----|-----|
| 50 | $2,370 | $28,440 |
| 100 | $4,740 | $56,880 |
| 250 | $11,850 | $142,200 |
| 500 | $23,700 | $284,400 |
| 1,000 | $47,400 | $568,800 |

---

### Implementation (if requested)

```typescript
// Stripe Product & Price Setup
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

// Create products and prices
const starterProduct = await stripe.products.create({
  name: '[Product] Starter',
  description: 'Perfect for getting started'
});

const starterMonthly = await stripe.prices.create({
  product: starterProduct.id,
  unit_amount: 2900, // $29
  currency: 'usd',
  recurring: { interval: 'month' }
});

// ... (complete implementation)
```

---

### Next Steps

1. Implement pricing page with `/ros landing-page pricing`
2. Set up Stripe products
3. A/B test pricing with different anchors
4. Monitor conversion rates by tier

### Data Saved

Pricing strategy saved to `~/.claude/revenue-os/pricing.json`
```

## Save Results

After generating pricing strategy, save to ~/.claude/revenue-os/pricing.json with structure:
```json
{
  "tiers": [
    {"name": "Starter", "monthly": 29, "annual": 24, "features": [...]},
    {"name": "Pro", "monthly": 79, "annual": 66, "features": [...], "recommended": true},
    {"name": "Enterprise", "monthly": 249, "annual": 207, "features": [...]}
  ],
  "psychology_applied": ["charm_pricing", "anchor_pricing", "decoy_effect"],
  "competitor_pricing": [...],
  "created_at": "ISO date"
}
```
