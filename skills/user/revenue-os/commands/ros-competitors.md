---
description: Competitive intelligence through web research
argument-hint: [analyze <name>|matrix|gaps|steal]
allowed-tools: Read, WebSearch, Bash(cat:*), Write
---

# Competitive Intelligence

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat "${CLAUDE_PLUGIN_ROOT}/data/competitor-analysis.json" 2>/dev/null`

## Instructions

### If $ARGUMENTS contains "analyze":

Deep dive on the named competitor:
1. WebSearch for their website, pricing page, features
2. WebSearch for reviews (G2, Capterra, Reddit mentions)
3. Analyze positioning, pricing, strengths, weaknesses
4. Identify attack angles

### If $ARGUMENTS is empty or "matrix":

1. Identify competitors (from product analysis or ask user)
2. WebSearch for each competitor
3. Create comparison matrix
4. Identify your unique advantages

### If $ARGUMENTS is "gaps":

Focus on finding market gaps:
1. WebSearch for "[category] missing features"
2. Search for competitor complaints
3. Identify underserved segments

### If $ARGUMENTS is "steal":

Generate competitor migration campaign:
1. Identify competitor weaknesses
2. Create targeted outreach for their users
3. Generate comparison content

## Output Format

```markdown
## Competitive Intelligence: [Your Product]

### Competitors Analyzed
- [Competitor 1] - [brief description]
- [Competitor 2] - [brief description]

### Feature Comparison Matrix

| Feature | You | Comp 1 | Comp 2 |
|---------|-----|--------|--------|
| [Feature] | ✓/✗ | ✓/✗ | ✓/✗ |

### Pricing Comparison

| | You | Comp 1 | Comp 2 |
|-|-----|--------|--------|
| Entry Price | $X | $X | $X |
| Pro Price | $X | $X | $X |

### Vulnerability Analysis

**[Competitor 1]**
- Weakness: [specific issue from research]
- Attack angle: "[Your product] does X that they can't"
- Evidence: "[quote from review/complaint]"

### Your Unique Advantages
1. [Advantage 1]
2. [Advantage 2]
3. [Advantage 3]

### Competitor Migration Campaign

**Target**: [Competitor] users unhappy with [issue]

**Outreach**:
Subject: Switching from [Competitor]?

[Email template targeting their users]
```
