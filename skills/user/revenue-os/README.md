# Revenue OS

[![Claude Code Plugin](https://img.shields.io/badge/Claude%20Code-Plugin-blueviolet)](https://claude.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

> **From code to customers to cash** — The monetization operating system for developers

Revenue OS is a powerful [Claude Code](https://claude.ai) plugin that transforms the journey from building a product to generating revenue. It analyzes your codebase, identifies ideal customers, polishes your value proposition, and generates everything you need to start making money.

**Perfect for:** Indie hackers, solo founders, startup developers, SaaS builders, and anyone who builds great products but struggles to monetize them.

---

## Why Revenue OS?

Developers are great at building products but often struggle with:

| Challenge | Revenue OS Solution |
|-----------|-------------------|
| **WHO** would pay for this? | AI-powered ICP (Ideal Customer Profile) discovery |
| **WHY** choose us over alternatives? | Value proposition frameworks that convert |
| **HOW MUCH** to charge? | Psychology-based pricing architecture |
| **WHERE** to find customers? | Community and channel identification |
| **WHAT** to say to them? | Ready-to-use outreach sequences |

Revenue OS provides a systematic, engineering-minded approach to monetization — because revenue is just another system to be designed and optimized.

---

## Features

- **Codebase Analysis** — Understands YOUR specific product, not generic advice
- **ICP Discovery** — Find exactly who will pay for your product
- **Value Proposition** — Multiple proven frameworks (JTBD, PAS, Before/After)
- **Pricing Psychology** — Research-backed tier design with competitor analysis
- **Outreach Generation** — Cold email, LinkedIn, and Twitter sequences
- **Landing Page Copy** — Conversion-optimized page structure
- **Objection Handling** — Proven responses to common sales objections
- **Revenue Audit** — Score your monetization readiness with action plan

---

## Installation

```bash
# Clone the plugin to your project
git clone https://github.com/anthropics/revenue-os.git

# Or add as a submodule
git submodule add https://github.com/anthropics/revenue-os.git .claude-plugins/revenue-os

# The plugin will be automatically detected by Claude Code
```

---

## Quick Start

```bash
# 1. See your revenue readiness score
/ros

# 2. Discover who will pay for your product
/ros icp

# 3. Polish your value proposition
/ros value-prop

# 4. Design your pricing
/ros pricing

# 5. Generate outreach sequences
/ros outreach

# 6. Get a full audit with action plan
/ros audit
```

---

## Commands

| Command | Description | Key Feature |
|---------|-------------|-------------|
| `/ros` | Main dashboard | Revenue readiness score |
| `/ros icp` | Find ideal customers | Codebase + web analysis |
| `/ros value-prop` | Polish your positioning | Multiple frameworks |
| `/ros pricing` | Design pricing architecture | Psychology + competitor research |
| `/ros competitors` | Competitive intelligence | Web search analysis |
| `/ros outreach` | Generate sequences | Email, LinkedIn, Twitter |
| `/ros landing-page` | Create landing page copy | Conversion-optimized |
| `/ros objections` | Handle sales objections | Proven responses |
| `/ros first-dollar` | Zero to revenue playbook | Unconventional tactics |
| `/ros audit` | Full readiness audit | Score + 2-week action plan |

---

## How It Works

### 1. Analyzes Your Code
Revenue OS scans your codebase to understand:
- What problem your product solves
- Key features and capabilities
- Technology stack
- Potential use cases

### 2. Finds Your Customers
Using AI analysis and web research:
- Generates ICP (Ideal Customer Profile) hypotheses
- Finds communities where they gather
- Validates pain points exist
- Identifies buying triggers

### 3. Polishes Your Pitch
Creates compelling messaging using proven frameworks:
- Jobs-to-be-Done (JTBD)
- Problem-Agitate-Solution (PAS)
- Before/After Transformation
- Unique Mechanism

### 4. Designs Pricing
Research-backed pricing architecture:
- Competitor analysis via web search
- Psychology-based tier design (charm pricing, anchoring, decoy effect)
- Revenue projections
- Stripe integration code

### 5. Generates Assets
Ready-to-use marketing materials:
- Cold email sequences (4-email series)
- LinkedIn outreach templates
- Landing page copy
- Objection handling scripts

---

## Example: 2-Week Revenue Sprint

### Week 1: Foundation

```bash
# Day 1: Understand your product and customers
/ros icp

# Day 2: Create compelling messaging
/ros value-prop

# Day 3: Research the competition
/ros competitors

# Day 4: Set your prices
/ros pricing

# Day 5: Prepare for objections
/ros objections
```

### Week 2: Distribution

```bash
# Day 6-7: Build your landing page
/ros landing-page full

# Day 8-9: Create outreach sequences
/ros outreach cold-email
/ros outreach linkedin

# Day 10-14: Execute and iterate
# Send outreach, track responses, refine
```

---

## Data Persistence

Revenue OS stores your data in `~/.claude/revenue-os/`:

```
~/.claude/revenue-os/
├── product.json      # Product analysis
├── icp.json          # Ideal customer profiles
├── value-prop.json   # Value propositions
├── pricing.json      # Pricing strategy
└── outreach/         # Generated sequences
```

Data persists across sessions, allowing commands to build on each other.

---

## Command Reference

### `/ros icp` - Ideal Customer Profile

| Argument | Description |
|----------|-------------|
| `discover` | Full codebase analysis (default) |
| `validate` | Use web search to validate ICP |
| `personas` | Generate detailed buyer personas |
| `find` | Find actual prospects via web search |

### `/ros value-prop` - Value Proposition

| Argument | Description |
|----------|-------------|
| `generate` | Create value propositions (default) |
| `analyze` | Analyze existing positioning |
| `test` | Generate A/B test variants |
| `framework <name>` | Use specific framework (jtbd, pas, before_after) |

### `/ros pricing` - Pricing Strategy

| Argument | Description |
|----------|-------------|
| `design` | Design pricing tiers (default) |
| `analyze` | Research competitor pricing |
| `psychology` | Deep dive on pricing tactics |
| `model` | Revenue projections |
| `implement` | Generate Stripe integration code |

### `/ros outreach` - Outreach Sequences

| Argument | Description |
|----------|-------------|
| `cold-email` | Email sequences (default) |
| `linkedin` | LinkedIn messages |
| `twitter` | Twitter/X DMs |
| `for <company>` | Personalize for specific target |

---

## Use Cases

- **Indie Hackers** — Go from side project to paying customers
- **SaaS Founders** — Find product-market fit faster
- **Developer Tools** — Monetize your open source work
- **Freelancers** — Package your skills into products
- **Agencies** — Create productized services

---

## Contributing

Contributions are welcome! Areas that could use help:

- Additional ICP templates for new industries
- More outreach templates and sequences
- Improved pricing psychology data
- Better Stripe integration examples
- Translations

See [CLAUDE.md](CLAUDE.md) for development documentation.

---

## GitHub Topics

When publishing this repo, add these topics for discoverability:
`claude-code`, `claude-plugin`, `monetization`, `saas`, `indie-hackers`, `pricing`, `sales`, `marketing`, `icp`, `value-proposition`, `outreach`, `developer-tools`, `startup`, `revenue`

---

## Author

Created by **[Vladyslav Podoliako](https://vladyslavpodoliako.com/)**

- **Website:** [vladyslavpodoliako.com](https://vladyslavpodoliako.com/)
- **Newsletter:** [vladsnewsletter.com](https://www.vladsnewsletter.com/) — Weekly insights on AI, development, and building products
- **Twitter/X:** [@StBelkins](https://twitter.com/stbelkins)

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Star History

If this plugin helps you make money, consider giving it a star!

---

<p align="center">
  <strong>Built for developers who deserve to get paid for their work.</strong>
  <br><br>
  <a href="https://www.vladsnewsletter.com/">Subscribe to the newsletter</a> for more tools and insights.
</p>
