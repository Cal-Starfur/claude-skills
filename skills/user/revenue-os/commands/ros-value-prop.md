---
description: Polish your value proposition with proven frameworks and ready-to-use copy
argument-hint: [analyze|generate|test|framework <name>|for <icp>]
allowed-tools: Read, Glob, Grep, WebSearch, Bash(cat:*), Write
---

# Value Proposition Polisher

## Arguments: $ARGUMENTS

## Load Existing Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`

## Frameworks Reference

!`cat "${CLAUDE_PLUGIN_ROOT}/data/value-prop-frameworks.json" 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS is empty or "generate":

1. **Load Context**
   - Read ICP from saved data (or ask user to run /ros icp first)
   - Analyze product from codebase if not already done

2. **Research Competitors** (WebSearch)
   - Search for competitor positioning
   - Note their headlines, value props
   - Identify gaps in their messaging

3. **Generate Value Propositions**
   - Apply each framework to create options
   - Focus on ICP's specific pain points
   - Differentiate from competitors

4. **Polish and Output**
   - Provide headline, subheadline, one-liner
   - Multiple positioning angles for A/B testing
   - Ready-to-use copy snippets

### If $ARGUMENTS is "analyze":

Analyze existing positioning (README, website if provided):
- Identify current messaging
- Highlight weak points
- Suggest improvements

### If $ARGUMENTS is "test":

Generate 3-4 variant headlines/value props for A/B testing.

### If $ARGUMENTS contains "framework":

Use the specified framework exclusively.

### If $ARGUMENTS contains "for":

Tailor specifically for the named ICP segment.

## Output Format

```markdown
## Value Proposition: [Product Name]

### For: [ICP Name]

---

### Product Understanding
- **What it does**: [core function]
- **Key differentiator**: [unique aspect]
- **Alternatives**: [what people use instead]

---

### The Winning Value Proposition

**Headline** (8 words max)
> [Compelling headline]

**Subheadline** (20 words max)
> [Clarification of what, for whom, why it matters]

**One-Liner** (for bios, tweets, conversations)
> "[Product] helps [ICP] [achieve outcome] without [pain point]."

---

### The 3 Key Benefits

1. **[Benefit 1]**
   - Feature: [underlying feature]
   - So what: [why it matters]
   - Proof: [how to prove it]

2. **[Benefit 2]**
   - Feature: [underlying feature]
   - So what: [why it matters]
   - Proof: [how to prove it]

3. **[Benefit 3]**
   - Feature: [underlying feature]
   - So what: [why it matters]
   - Proof: [how to prove it]

---

### Positioning Angles (A/B Test These)

**Angle A: Pain-Killer**
> "[Pain-focused headline]"
Best for: Frustrated audiences seeking relief

**Angle B: Gain-Creator**
> "[Gain-focused headline]"
Best for: Ambitious audiences seeking growth

**Angle C: Competitive**
> "[Differentiation headline]"
Best for: Audiences comparing alternatives

**Angle D: Social Proof**
> "[Social proof headline]"
Best for: Risk-averse audiences

---

### Elevator Pitch (30 seconds)

"You know how [ICP] struggle with [problem]? They usually [current solution] which [limitation].

[Product] is a [category] that [key differentiator]. Unlike [alternative], we [unique mechanism].

Our users [specific outcome with metric]."

---

### Ready-to-Use Copy

**Hero Section**
[Headline]
[Subheadline]
[CTA button text]

**Email Subject Lines**
1. [Option 1]
2. [Option 2]
3. [Option 3]

**Tweet**
[Ready-to-post tweet]

**LinkedIn Post**
[Ready-to-post LinkedIn content]

---

### Next Steps
1. A/B test headlines with `/ros landing-page`
2. Create outreach using this messaging with `/ros outreach`
```

## Save Results

Save generated value prop to ~/.claude/revenue-os/value-prop.json
