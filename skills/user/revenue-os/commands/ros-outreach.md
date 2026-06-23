---
description: Generate personalized outreach sequences for customer acquisition
argument-hint: [cold-email|linkedin|twitter|follow-up|for <company>]
allowed-tools: Read, WebSearch, Bash(cat:*), Write
---

# Outreach Generator

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`
!`cat "${CLAUDE_PLUGIN_ROOT}/data/outreach-templates.json" 2>/dev/null`

## Instructions

### Prerequisites Check
- If no ICP defined, prompt user to run /ros icp first
- If no value prop defined, prompt user to run /ros value-prop first

### If $ARGUMENTS is empty or "cold-email":

Generate a 4-email cold outreach sequence:
1. Use ICP data to understand the target
2. Use value prop for messaging
3. Apply templates but customize for specific product/audience
4. Include personalization variables

### If $ARGUMENTS is "linkedin":

Generate LinkedIn outreach:
- Connection request (under 300 chars)
- First message after accept
- Follow-up pitch message

### If $ARGUMENTS is "twitter":

Generate Twitter/X DM sequence.

### If $ARGUMENTS is "follow-up":

Generate follow-up sequences for warm leads.

### If $ARGUMENTS contains "for":

Personalize for specific target company:
1. WebSearch for company info, recent news
2. Find decision maker info
3. Customize outreach with specific details

## Output Format

```markdown
## Cold Email Sequence: [ICP Name]

### Sequence Overview
- 4 emails over 14 days
- Expected response rate: 5-15%
- Best send times: Tuesday-Thursday, 9-11am

---

### Email 1: The Pattern Interrupt
**Day 1 | Subject**: [Subject line]

Hi {{first_name}},

[Body using ICP pain points and value prop]

[Your name]

---

### Email 2: The Value Bomb
**Day 3 | Subject**: Re: [previous]

{{first_name}},

[Pure value content]

---

### Email 3: The Social Proof
**Day 7 | Subject**: [Social proof subject]

{{first_name}},

[Case study + soft CTA]

---

### Email 4: The Breakup
**Day 14 | Subject**: Closing the loop

{{first_name}},

[Final CTA + door open]

---

### Personalization Guide
- {{first_name}} - First name
- {{company}} - Company name
- {{specific_pain}} - Their specific pain point
- {{recent_news}} - Recent company news to reference

### Tips for Success
1. [Tip 1]
2. [Tip 2]
3. [Tip 3]
```

Save generated sequences to ~/.claude/revenue-os/outreach/
