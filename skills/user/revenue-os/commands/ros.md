---
description: Revenue OS - Main dashboard and command hub
argument-hint: [help|status|reset]
allowed-tools: Read, Bash(cat:*), Bash(mkdir:*), Bash(ls:*), Bash(rm:*)
---

# Revenue OS Dashboard

## Load Current State

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`
!`ls ~/.claude/revenue-os/outreach/ 2>/dev/null | wc -l | tr -d ' '`

## Industry Benchmarks Reference

!`cat "${CLAUDE_PLUGIN_ROOT}/data/industry-benchmarks.json" 2>/dev/null || echo '{}'`

## Arguments: $ARGUMENTS

## Instructions

### If $ARGUMENTS is empty or "status":

Display the Revenue OS dashboard showing:

1. **Product Name** (from product.json or "Not Analyzed")

2. **Revenue Readiness Score** (0-100)
   Calculate based on the scoring logic below

3. **Checklist** with status indicators:
   - ✓ = Complete (green)
   - ⚠ = Partial (yellow)
   - ✗ = Missing (red)

4. **Next Action**
   - Recommend the single most important next command based on gaps

5. **Available Commands**
   - List all /ros commands with brief descriptions

### If $ARGUMENTS is "help":

Show detailed help for all commands:

```
/ros                 - This dashboard
/ros icp             - Find ideal customers (analyzes your codebase)
/ros value-prop      - Polish your value proposition
/ros pricing         - Design pricing architecture
/ros competitors     - Competitive intelligence (uses web search)
/ros outreach        - Generate email/LinkedIn sequences
/ros landing-page    - Create landing page copy
/ros objections      - Sales objection responses
/ros first-dollar    - Zero to revenue playbook
/ros audit           - Full revenue readiness audit
```

### If $ARGUMENTS is "reset":

Warn user that this will delete all saved data, then if confirmed:
- Delete ~/.claude/revenue-os/product.json
- Delete ~/.claude/revenue-os/icp.json
- Delete ~/.claude/revenue-os/value-prop.json
- Delete ~/.claude/revenue-os/outreach/*
Re-initialize with empty defaults.

## Scoring Logic

Calculate score out of 100 points:

| Area | Points | Criteria |
|------|--------|----------|
| Product Analysis | 15 | product.json has name (not null) |
| ICP Definition | 25 | icp.json has primary.name |
| Value Proposition | 25 | value-prop.json has headline |
| Pricing | 15 | pricing data exists |
| Outreach | 10 | outreach directory has files |
| Distribution | 10 | landing page or channels defined |

**Total: 100 points**

Score interpretation:
- 0-25: Just getting started
- 26-50: Foundation building
- 51-75: Making progress
- 76-90: Almost ready
- 91-100: Launch ready!

## Output Format

```
┌─────────────────────────────────────────────────────────────┐
│  REVENUE OS - [Product Name or "Not Analyzed"]              │
├─────────────────────────────────────────────────────────────┤
│  Revenue Readiness Score: XX/100  [Progress Bar]            │
│                                                             │
│  ✓ Product analyzed                                         │
│  ✓ ICP defined (Primary: [ICP Name])                        │
│  ✗ Value proposition (run /ros value-prop)                  │
│  ✗ Pricing strategy (run /ros pricing)                      │
│  ✗ Outreach sequences (run /ros outreach)                   │
│  ✗ Landing page (run /ros landing-page)                     │
│                                                             │
│  NEXT ACTION: Run /ros [command] to [benefit]               │
├─────────────────────────────────────────────────────────────┤
│  Commands:                                                  │
│  /ros icp         - Find ideal customers                    │
│  /ros value-prop  - Polish positioning                      │
│  /ros pricing     - Design pricing                          │
│  /ros outreach    - Generate sequences                      │
│  /ros competitors - Competitive intel                       │
│  /ros audit       - Full readiness audit                    │
│                                                             │
│  Type /ros help for detailed command info                   │
└─────────────────────────────────────────────────────────────┘
```

## Benchmarks Context

When displaying the score, provide context from industry benchmarks:
- At current score, typical time to first revenue: [X weeks/months]
- Recommended next milestone: [specific target]
