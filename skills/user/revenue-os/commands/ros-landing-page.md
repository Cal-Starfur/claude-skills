---
description: Generate high-converting landing page copy and structure
argument-hint: [full|hero|features|pricing|faq|html]
allowed-tools: Read, Bash(cat:*), Write
---

# Landing Page Generator

## Arguments: $ARGUMENTS

## Load Data

!`cat ~/.claude/revenue-os/product.json 2>/dev/null || echo '{"name": null}'`
!`cat ~/.claude/revenue-os/icp.json 2>/dev/null || echo '{}'`
!`cat ~/.claude/revenue-os/value-prop.json 2>/dev/null || echo '{}'`

## Instructions

### If $ARGUMENTS is empty or "full":

Generate complete landing page structure:

1. **Hero Section**
   - Headline (from value prop)
   - Subheadline
   - CTA button
   - Social proof snippet

2. **Problem Section**
   - Pain points (from ICP)
   - Current alternatives
   - Why they fail

3. **Solution Section**
   - How product solves problems
   - Key benefits

4. **Features Section**
   - 3-6 features with benefits
   - Icons/visual suggestions

5. **Social Proof Section**
   - Testimonial format
   - Logos section
   - Stats/metrics

6. **Pricing Section**
   - Tiers (if defined)
   - Feature comparison

7. **FAQ Section**
   - Objections as FAQs
   - Trust-building answers

8. **Final CTA**
   - Urgency/scarcity if appropriate
   - Risk reversal (guarantee)

### If $ARGUMENTS is "html":

Output as HTML/JSX components.

### For specific sections:

Generate just that section.

## Output Format

```markdown
## Landing Page: [Product Name]

### Hero Section

**Headline**
> [Headline from value prop]

**Subheadline**
> [Subheadline]

**CTA Button**: [Button text]

**Social Proof**: [Brief proof]

---

### Problem Section

**Header**: [Problem-focused header]

[Pain point 1 with elaboration]
[Pain point 2 with elaboration]
[Pain point 3 with elaboration]

---

### Solution Section

**Header**: [Solution-focused header]

[How the product solves each problem]

---

### Features Section

**Feature 1**: [Name]
[Description and benefit]

**Feature 2**: [Name]
[Description and benefit]

**Feature 3**: [Name]
[Description and benefit]

---

### Social Proof Section

**Testimonial Template**
> "[Quote about transformation/results]"
> — [Name], [Role] at [Company]

**Stats**
- [Metric 1]
- [Metric 2]

---

### Pricing Section

[Pricing tiers if available]

---

### FAQ Section

**Q: [Objection as question]**
A: [Trust-building answer]

---

### Final CTA Section

**Headline**: [Action-oriented headline]
**CTA Button**: [Button text]
**Risk Reversal**: [Guarantee/trial offer]

---

### Complete HTML (if requested)

```html
[Full HTML structure]
```
```
