# Skill Gap Analysis — June 19, 2026

Identified during a meta-session reviewing the full skill ecosystem against the
risks of AI-assisted development for a non-fluent owner (Cal-Starfur).

## Context

The post that prompted this: a viral thread pointing out that vibe-coders
confuse a working prototype with a production system. The parallel for AI-assisted
game dev: Claude making confident changes the owner can't read or verify.

## Coverage Map

### COVERED ✅

| Skill | What it protects |
|---|---|
| lead-dev | Architecture drift, naming consistency, dead code |
| contractor | Scope creep on single fixes |
| github-sync | Approve-before-push gate |
| session-health | State drift, version sync |
| devvit-pipeline | Build verification |
| skill-audit | Skill performance tracking |
| wigglers-architecture | Game-specific system knowledge |

### GAPS — HIGH PRIORITY 🔴

| Gap | Risk if missing |
|---|---|
| Plain-English session summary | Owner can't tell what changed without reading code |
| Pre-flight checklist | Claude starts session with stale/wrong context |
| Rollback / undo skill | No safe path back when something breaks |

### GAPS — MEDIUM PRIORITY 🟡

| Gap | Risk if missing |
|---|---|
| Feature spec skill | Ideas go straight to code without a human-readable ticket |
| Test scenario skill | No checklist to verify a feature works before pushing |
| Tech debt tracker | Shortcuts accumulate invisibly |

### RISK ZONES (existing vulnerabilities, not missing skills) 🔴

| Risk | Current mitigation | Gap |
|---|---|---|
| Silent scope creep | contractor skill mindset rules | No automated diff check |
| Stale context | session-health + github-sync | No gate that blocks if context is stale |
| No human verify step | github-sync approve gate | Approve step easy to skip under time pressure |

## The Biggest Missing Thing

A **human-readable session summary** — after every session, two paragraphs in plain
English: what changed, why, what could break, yes or no to push.
So the owner can make a real decision without reading a diff.
