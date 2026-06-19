# Claude Skills — Audit Tracker & Reference

This repo tracks the Claude AI skill ecosystem for the Wigglers Room project and beyond.

## What's here

| Folder | Purpose |
|---|---|
| `audits/` | Skill audit snapshots — scored every session |
| `skills/` | Canonical SKILL.md source files (version controlled) |
| `planning/` | Buildout plans, gap analyses, roadmaps |
| `CHANGELOG.md` | Running log of skill changes across sessions |

## Skill roster (as of June 2026)

| Skill | Score | Role |
|---|---|---|
| session-health | 97 | Session drift detection + auto-fix |
| github-sync | 88 | GitHub read/write + approve-before-push |
| devvit-pipeline | 92 | Deploy → build check → Reddit feedback |
| lead-dev | 85 | Passive senior dev — architecture guard |
| contractor | 82 | Surgical single-ticket game edits |
| wigglers-architecture | 72 | Wigglers Room living system map |
| save-skill-workflow | 72 | Package skills with Save button |
| canvas-art-optimizer | 68 | SVG → HTML5 Canvas conversion |
| png-canvas-art-optimizer | 60 | PNG/JPG → HTML5 Canvas via vision |

## Gap Analysis (June 2026)

Full analysis in [`audits/2026-06-19-gap-analysis.md`](audits/2026-06-19-gap-analysis.md)
Buildout plan in [`planning/skill-buildout-plan.md`](planning/skill-buildout-plan.md)

### Phase 1 — Owner Control (building now)
- [ ] `session-summary` — plain-English what-changed after every session
- [ ] `preflight-checklist` — gate before any code change starts
- [ ] `rollback` — safe revert to last known-good state

### Phase 2 — Process Quality (after Phase 1 stable)
- [ ] `feature-spec` — idea → ticket before touching code
- [ ] `test-scenario` — human-readable verify checklist per feature
- [ ] `tech-debt-tracker` — log shortcuts, surface them later

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
