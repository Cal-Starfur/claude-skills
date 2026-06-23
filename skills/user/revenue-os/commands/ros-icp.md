---
description: Discover and validate your Ideal Customer Profile through codebase analysis and market research
argument-hint: [discover|refine|validate|personas|find]
allowed-tools: Read, Glob, Grep, WebSearch, Bash(cat:*), Bash(mkdir:*), Write
---

# ICP Finder

## Arguments: $ARGUMENTS

## Load Existing Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`

## ICP Templates Reference

!`cat "${CLAUDE_PLUGIN_ROOT}/data/icp-templates.json" 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS is empty or "discover":

**FULL CODEBASE ANALYSIS MODE**

1. **Analyze the Project**
   - Use Glob to find: README.md, package.json, *.config.*, main source files
   - Use Read to examine key files
   - Use Grep to search for keywords indicating purpose

2. **Extract Product Intelligence**
   - What does this product do? (core function)
   - What problem does it solve?
   - What technologies does it use?
   - Who would benefit from this?

3. **Generate ICP Hypotheses**
   - Create 2-3 ICP hypotheses based on the product
   - Use templates from icp-templates.json as starting points
   - Customize based on what you discovered

4. **Web Research**
   - Use WebSearch to find communities where these ICPs gather
   - Search for: "[problem] forum", "[product type] community", "[industry] slack groups"
   - Find validation signals (people complaining about the problem)

5. **Output Complete ICP Profile**

### If $ARGUMENTS is "validate":

Use WebSearch to validate the existing ICP:
- Search for communities mentioned
- Look for discussions about the pain points
- Find competitor users complaining
- Verify budget expectations are realistic

### If $ARGUMENTS is "refine":

Ask clarifying questions to improve the existing ICP.

### If $ARGUMENTS is "find":

Use WebSearch to find actual potential customers:
- Search for job postings with relevant keywords
- Find company announcements related to the problem
- Look for social media posts expressing the pain point

### If $ARGUMENTS is "personas":

Generate detailed buyer personas from the ICP with:
- Name, role, day-in-the-life
- Goals, frustrations, fears
- How they evaluate solutions
- Objections they'll raise

## Output Format

```markdown
## Ideal Customer Profile: [Product Name]

### Product Analysis
Based on analyzing your codebase:
- **Core function**: [what it does]
- **Key features**: [feature list]
- **Tech stack**: [technologies]
- **Problem solved**: [the pain it addresses]

---

### Primary ICP: [Specific Title]

**Demographics**
- Company size: X-Y employees
- Industry: [industries]
- Stage: [company stage]
- Annual revenue: $X - $Y
- Tech stack: [what they use]

**Psychographics**
- Cares deeply about: [values]
- Frustrated by: [pain points]
- Currently solving with: [alternatives]
- Budget mindset: [how they think about spending]

**Buying Behavior**
- Decision maker: [role]
- Budget authority: $X-Y/mo without approval
- Buying triggers: [events]
- Likely objections: [concerns]

**Where to Find Them** (Web Research)
- Communities: [specific places with links]
- Twitter/X: [hashtags, accounts]
- Events: [conferences, meetups]
- Keywords they search: [search terms]

---

### Secondary ICP: [Alternative Title]
[Similar structure]

---

### Validation Checklist
- [ ] Found 100+ potential customers in identified communities
- [ ] Confirmed pain point exists (evidence found)
- [ ] Competitors exist (validates market)
- [ ] Budget range is realistic
- [ ] Can reach through available channels

### Next Steps
1. [Specific action 1]
2. [Specific action 2]
3. Run `/ros value-prop` to create messaging for this ICP
```

## Save Results

After generating the ICP, save to ~/.claude/revenue-os/icp.json
