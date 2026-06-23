---
description: Step-by-step playbook to get your first paying customer
argument-hint: [assess|next|tactics|unconventional]
allowed-tools: Read, WebSearch, Bash(cat:*), Write
---

# First Dollar Playbook

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS is empty or "assess":

Assess where they are in the journey:
1. Pre-product (still building)
2. Product done, no customers
3. Have users, no paying customers
4. Have some revenue, want more

Provide stage-specific advice.

### If $ARGUMENTS is "next":

Give the single most important next action based on current state.

### If $ARGUMENTS is "tactics":

List proven first-revenue tactics:
1. Direct outreach
2. Community marketing
3. Content marketing
4. Paid acquisition
5. Partnerships
6. Product-led growth

### If $ARGUMENTS is "unconventional":

Non-obvious tactics for desperate times:
1. Design Partner Program
2. Consulting Bridge
3. Competitor Migration
4. Pilot Programs
5. Lifetime Deals
6. Done-for-You Setup
7. Beta Founding Member

## Output Format

```markdown
## First Dollar Playbook: [Product Name]

### Current Assessment

Based on your Revenue OS data:
- Product: [Status]
- ICP: [Status]
- Value Prop: [Status]
- Stage: [Pre-revenue / Early / Growth]

### Your Path to First $1,000 MRR

**Week 1: Foundation**
- [ ] Define ICP with `/ros icp`
- [ ] Polish value prop with `/ros value-prop`
- [ ] Set up basic landing page

**Week 2: Outreach**
- [ ] Create cold email sequence with `/ros outreach`
- [ ] Identify 50 target prospects
- [ ] Send first batch of outreach

**Week 3: Iterate**
- [ ] Analyze response rates
- [ ] Refine messaging
- [ ] Double down on what works

**Week 4: Close**
- [ ] Follow up with warm leads
- [ ] Handle objections
- [ ] Close first customers

### Unconventional Tactics to Consider

**1. Design Partner Program**
Charge $500-2000 for early access + roadmap influence.
- Why it works: Customers feel invested, you get paid validation
- How to pitch: "We're selecting 5 design partners to shape the product..."
- Price: $500-2000 one-time

**2. Consulting Bridge**
Sell your expertise at $150/hr while building product.
- Why it works: Validates problem, builds relationships, generates cash
- How to position: Offer consulting that uses your product
- Price: $100-200/hr

**3. Competitor Migration**
Find unhappy competitor users, offer switching bonus.
- Why it works: Pre-validated demand, easier sell
- How to find them: Search "[competitor] frustrated", review sites
- Offer: Free migration + discount

**4. Pilot Programs**
50% discount for case study + testimonial rights.
- Why it works: Lowers barrier, gets social proof
- How to pitch: "We're running a pilot program for..."
- Price: 50% off for 3 months

**5. Lifetime Deals**
$299 lifetime for early believers (AppSumo style).
- Why it works: Quick cash, builds user base
- Platforms: AppSumo, DealMirror, own site
- Price: $99-499 lifetime

**6. Done-for-You Setup**
$2000+ setup fee for hands-on implementation.
- Why it works: High-touch sells easier, premium revenue
- Who to target: Busy executives, agencies
- Price: $1000-5000

**7. Beta Founding Member**
$99/year locked rate for first 50 customers.
- Why it works: Urgency, exclusivity, loyalty
- How to pitch: "Lock in founding member pricing forever"
- Price: 50% of planned price, annual only

### Your Single Next Action

Based on where you are: **[Specific action with command]**

### Revenue Math

To hit $1,000 MRR, you need:
- At $29/mo: 35 customers
- At $79/mo: 13 customers
- At $199/mo: 6 customers

To hit $10,000 MRR, you need:
- At $29/mo: 345 customers
- At $79/mo: 127 customers
- At $199/mo: 51 customers
```
