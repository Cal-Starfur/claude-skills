# Claude Skills — Audit Tracker & Reference

This repo tracks the Claude AI skill ecosystem for the Wigglers Room project and beyond.

## What's here

| Folder | Purpose |
|---|---|
| `audits/` | Skill audit snapshots — scored every session |
| `skills/` | Canonical SKILL.md source files (version controlled) |
| `SKILL_REFERENCE.md` | Master trigger guide — which skill to load and when |
| `CHANGELOG.md` | Running log of skill changes across sessions |

## Skill roster (as of June 2026)

| Skill | Score | Role |
|---|---|---|
| github-sync | 88 | GitHub read/write + approve-before-push |
| lead-dev | 85 | Passive senior dev — architecture guard |
| contractor | 82 | Surgical single-ticket game edits |
| devvit-pipeline | 79 | Deploy → build check → Reddit feedback |
| wigglers-architecture | 72 | Wigglers Room living system map |
| save-skill-workflow | 72 | Package skills with Save button |
| canvas-art-optimizer | 68 | SVG → HTML5 Canvas conversion |
| png-canvas-art-optimizer | 60 | PNG/JPG → HTML5 Canvas via vision |

## Audit methodology

Each skill is scored 0–100 across four dimensions:
- **Trigger** — does the description clearly tell Claude when to load it?
- **Content quality** — is the instruction body accurate and well-organized?
- **Completeness** — are edge cases, fallbacks, and hard rules covered?
- **Freshness** — how likely is the skill to drift out of sync with reality?

Audits are run individually per skill and documented in `audits/`.

## Quick links

- [Wigglers Room game repo](https://github.com/Cal-Starfur/Wigglers_Room)
- [Codespace Bridge repo](https://github.com/Cal-Starfur/codespace-bridge)
