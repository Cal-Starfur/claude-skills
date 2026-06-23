---
description: Handle sales objections with proven responses
argument-hint: [generate|handle <objection>|script|practice]
allowed-tools: Read, Bash(cat:*), Write
---

# Objection Handler

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat "${CLAUDE_PLUGIN_ROOT}/data/objection-library.json" 2>/dev/null`

## Instructions

### If $ARGUMENTS is empty or "generate":

Generate likely objections for this specific product:
1. Based on ICP (budget concerns, decision process)
2. Based on product type (build vs buy, switching cost)
3. Based on pricing (if known)

Provide responses customized to this product.

### If $ARGUMENTS contains "handle":

Provide detailed response to the specific objection:
- Multiple response tactics
- Customized for this product
- Example scripts

### If $ARGUMENTS is "script":

Generate a full sales conversation script including:
- Opening
- Discovery questions
- Product presentation
- Objection handling
- Closing

### If $ARGUMENTS is "practice":

Interactive objection practice mode.

## Output Format

```markdown
## Objection Handling: [Product Name]

### Most Likely Objections for Your ICP

Based on [ICP name] selling [Product]:

1. **[Objection 1]**
   - Why they say it: [psychology]
   - Response: [customized response]

2. **[Objection 2]**
   - Why they say it: [psychology]
   - Response: [customized response]

3. **[Objection 3]**
   - Why they say it: [psychology]
   - Response: [customized response]

### Universal Responses (Memorize These)

**Price Objection Framework**
1. Acknowledge: "I understand price is a concern..."
2. Question: "What would [outcome] be worth to you?"
3. Reframe: "Compared to [alternative], this is..."
4. Proof: "Our customers typically see ROI in..."

**Competitor Objection Framework**
1. Acknowledge: "That's a great product..."
2. Question: "What do you wish it did better?"
3. Differentiate: "The key difference is..."
4. Offer: "Would you like to see a comparison?"

**Timing Objection Framework**
1. Acknowledge: "I understand timing is tricky..."
2. Question: "When would be better?"
3. Urgency: "The cost of waiting is..."
4. Easy start: "We could start with just..."

### Quick Reference Card

| Objection | Quick Response |
|-----------|----------------|
| Too expensive | "What would [outcome] be worth to you?" |
| No budget | "When's your next budget cycle?" |
| Using competitor | "What do you wish it did better?" |
| Build ourselves | "How many engineer-months would that take?" |
| Need approval | "What info would help you make the case?" |
| Prove ROI | "Let's run a measured pilot." |
| Tried before | "What didn't work? We might be different." |

### Role-Play Scenarios

**Scenario 1: Price Pushback**
[Example dialogue]

**Scenario 2: Competitor Lock-in**
[Example dialogue]

**Scenario 3: Need to Think**
[Example dialogue]
```
