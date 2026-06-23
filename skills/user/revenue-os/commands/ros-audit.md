---
description: Comprehensive revenue readiness audit with scoring and action plan
argument-hint: [full|quick|export]
allowed-tools: Read, Glob, Bash(cat:*), Bash(ls:*), Write
---

# Revenue Readiness Audit

## Arguments: $ARGUMENTS

## Load All Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/pricing.json 2>/dev/null || echo '{"tiers": []}'`
!`ls -la ~/.claude/revenue-os/outreach/ 2>/dev/null || echo 'No outreach sequences'`

## Industry Benchmarks Reference

!`cat "${CLAUDE_PLUGIN_ROOT}/data/industry-benchmarks.json" 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS is empty or "full":

Perform comprehensive audit:

1. **Score Each Area** (0-100 total)

   | Area | Max Points | Scoring Criteria |
   |------|------------|------------------|
   | Product Analysis | 15 | Has name: 10pts, has features: +5pts |
   | ICP Definition | 25 | Has primary: 15pts, has where_to_find: +5pts, validated: +5pts |
   | Value Proposition | 25 | Has headline: 15pts, has benefits: +5pts, has angles: +5pts |
   | Pricing | 15 | Has tiers: 10pts, has psychology: +5pts |
   | Sales Collateral | 10 | Has outreach sequences: 10pts |
   | Distribution | 10 | Has channels defined: 10pts |

2. **Identify Critical Gaps**
   - Any area scoring 0 is CRITICAL
   - Any area scoring < 50% of max is WARNING
   - Recommend specific `/ros` command for each gap

3. **Create Action Plan**
   - 2-week sprint with prioritized daily actions
   - Focus on highest-impact gaps first
   - Reference industry benchmarks for context

4. **Project Revenue Timeline**
   - Use industry benchmarks to estimate:
     - Time to first sale
     - Time to first $1k MRR
     - Time to first $10k MRR

### If $ARGUMENTS is "quick":

Show just the score breakdown without detailed recommendations.

### If $ARGUMENTS is "export":

Export all Revenue OS data to a JSON file for backup or sharing.

## Output Format

```markdown
## Revenue Readiness Audit: [Product Name]

**Audit Date**: [Date]
**Codebase**: [Path if available]

---

### Overall Score: XX/100

```
[████████░░░░░░░░░░░░] XX%
```

**Status**: [Just Starting | Building Foundation | Making Progress | Almost Ready | Launch Ready]

---

### Detailed Breakdown

| Area | Score | Status | Action Required |
|------|-------|--------|-----------------|
| Product Analysis | X/15 | ✓/⚠/✗ | [Action or "Complete"] |
| ICP Definition | X/25 | ✓/⚠/✗ | [Action or "Complete"] |
| Value Proposition | X/25 | ✓/⚠/✗ | [Action or "Complete"] |
| Pricing | X/15 | ✓/⚠/✗ | [Action or "Complete"] |
| Sales Collateral | X/10 | ✓/⚠/✗ | [Action or "Complete"] |
| Distribution | X/10 | ✓/⚠/✗ | [Action or "Complete"] |

**Legend**: ✓ Complete | ⚠ Partial | ✗ Missing

---

### Critical Gaps (Fix These First)

1. ❌ **[Most Critical Gap]**
   - Impact: [Why this matters]
   - Fix: Run `/ros [command]`
   - Time: ~[X minutes]

2. ❌ **[Second Gap]**
   - Impact: [Why this matters]
   - Fix: Run `/ros [command]`
   - Time: ~[X minutes]

---

### What's Working

1. ✓ **[Strength 1]** - [Brief explanation]
2. ✓ **[Strength 2]** - [Brief explanation]

---

### Your 2-Week Sprint to Revenue

**Week 1: Foundation (Days 1-5)**

| Day | Task | Command | Est. Time |
|-----|------|---------|-----------|
| 1 | Define ideal customer | `/ros icp` | 30 min |
| 2 | Polish value proposition | `/ros value-prop` | 30 min |
| 3 | Research competitors | `/ros competitors` | 45 min |
| 4 | Design pricing | `/ros pricing` | 30 min |
| 5 | Handle objections prep | `/ros objections` | 20 min |

**Week 2: Distribution (Days 6-14)**

| Day | Task | Command | Est. Time |
|-----|------|---------|-----------|
| 6-7 | Create landing page | `/ros landing-page` | 1 hr |
| 8-9 | Generate outreach | `/ros outreach` | 45 min |
| 10-14 | Execute outreach | Manual | Ongoing |

---

### Revenue Projection

Based on your score of **XX/100** and industry benchmarks:

| Milestone | Conservative | Moderate | Aggressive |
|-----------|--------------|----------|------------|
| First Sale | X weeks | X weeks | X weeks |
| $1k MRR | X months | X months | X months |
| $10k MRR | X months | X months | X months |

**Key Assumptions**:
- Conversion rate: [X%] (industry avg for your category)
- Average deal size: $[X]/mo (based on pricing)
- Outreach response rate: [X%] (industry benchmark)

---

### Benchmarks Context

**Your Category**: [Developer Tools / SaaS / Productivity / etc.]

| Metric | Your Status | Industry Avg | Top Performers |
|--------|-------------|--------------|----------------|
| Trial-to-Paid | N/A | 15-25% | 30-50% |
| Monthly Churn | N/A | 3-5% | 1-2% |
| LTV:CAC Ratio | N/A | 3:1 | 5:1+ |

---

### Recommended Next Action

🎯 **Run: `/ros [most-important-command]`**

This will [specific benefit] and move your score from XX to ~YY.

---

### Export Data

To export all your Revenue OS data:
```
/ros audit export
```

Data location: `~/.claude/revenue-os/`
```

## Save Audit Results

After completing audit, optionally save results to ~/.claude/revenue-os/audit-history.json for tracking progress over time.
