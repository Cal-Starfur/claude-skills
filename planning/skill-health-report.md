# Skill Health Report — June 22, 2026

**Produced by:** Claude Sonnet 4.6
**Method:** Full dependency map + integration audit across all 12 skills
**Status:** 5 structural problems identified. None are session-blockers today, but all compound over time.

---

## The Skill Library

| Skill | Lines | Layer | Score | Status |
|---|---|---|---|---|
| lead-dev | 3060 | 0 — always on | 85 | 🔴 Critically oversized |
| wigglers-architecture | 451 | 0 — always on | 72 | ✅ OK |
| session-health | 682 | 1 — session start | — | 🔴 Oversized |
| github-sync | 1353 | 1 — session start | 88 | 🔴 Oversized |
| contractor | 925 | 2 — during session | 82 | 🔴 Oversized |
| devvit-pipeline | 1868 | 2 — during session | 79 | 🔴 Oversized |
| session-summary | 168 | 3 — session end | 90 | ✅ Healthy |
| project-calendar | 941 | 3 — session end | — | 🔴 Oversized |
| skill-audit | 161 | 4 — meta/admin | — | ⚠ Orphaned |
| save-skill-workflow | 108 | 4 — meta/admin | 72 | ✅ OK |
| canvas-art-optimizer | 222 | 4 — meta/admin | 68 | ⚠ Needs work |
| png-canvas-art-optimizer | 291 | 4 — meta/admin | 60 | 🔴 Needs work |

**skill-creator spec:** SKILL.md should be under 500 lines. 6 of 12 skills exceed this.

---

## The Layer Model (What It Should Be)

Skills have a natural execution order every Wigglers session. This is the intended model:

```
Layer 0 — ALWAYS ON (passive, no explicit load needed)
  lead-dev              silent architect, always watching
  wigglers-architecture structural reference, loaded by session-health

Layer 1 — SESSION START (run once, in order, before any code work)
  session-health        health check + doc pull + bridge status
  github-sync           token set, scripts bootstrapped

Layer 2 — DURING SESSION (on demand)
  contractor            surgical code changes
  devvit-pipeline       deploy to Reddit

Layer 3 — SESSION END (always offered after last push)
  session-summary       plain-English summary + push recommendation
  project-calendar      task sync if work was completed

Layer 4 — META / ADMIN (outside normal session flow)
  skill-audit           ad-hoc skill improvement sessions
  save-skill-workflow   Save Skill button workflow
  canvas-art-optimizer  SVG-to-canvas conversion
  png-canvas-art-optimizer  PNG-to-canvas conversion
```

---

## Problem 1 — Six Skills Are Critically Oversized 🔴

**What:** The skill-creator spec says SKILL.md should stay under 500 lines. Six skills blow past this:

| Skill | Lines | Ratio |
|---|---|---|
| lead-dev | 3060 | 6.1× |
| devvit-pipeline | 1868 | 3.7× |
| github-sync | 1353 | 2.7× |
| project-calendar | 941 | 1.9× |
| contractor | 925 | 1.9× |
| session-health | 682 | 1.4× |

**Why it matters:** Every skill that triggers gets loaded fully into Claude's context window. A 3060-line SKILL.md consumes roughly the same context as reading the entire `game.js` twice. When multiple oversized skills load in the same session, Claude is working from a severely compressed context — architectural decisions, commit history, and conversation get pushed out to make room for skill boilerplate.

**Root cause:** These skills were built correctly using embedded scripts (Python code stored inside SKILL.md so it auto-deploys). The scripts are essential, but they belong in a separate `scripts/` subfolder and loaded on demand — not baked into the SKILL.md body.

**Fix:** Extract all embedded Python scripts from SKILL.md into `skills/{name}/scripts/` files. SKILL.md keeps only the instructions and a reference pointer. This is a pure restructure — no logic changes needed.

---

## Problem 2 — Load Order Conflict: lead-dev vs session-health 🔴

**What:** `session-health` is supposed to run first, before any code work. But `lead-dev`'s description says:

> "Load this for ANY game project or codebase... Triggers automatically whenever a game file, HTML file, JavaScript file, or project codebase is present in the conversation."

If any game file is present in the context at session start (an upload, a paste, a reference), lead-dev auto-loads immediately — before session-health has run its health check or pulled fresh docs. This means lead-dev may read stale cached files or start issuing architectural opinions based on outdated state.

**The documented order (from session-health):**
```
1. session-health  → health check + auto-fix + read docs
2. github-sync     → set token, point at Wigglers_Room
3. wigglers-architecture → structural reference
4. contractor / lead-dev → code work
```

**The actual order (from trigger descriptions):**
```
lead-dev fires on: "any game file present"  ← before session-health
session-health fires on: "any Wigglers mention"  ← potentially after lead-dev
```

**Why it matters:** lead-dev running before session-health means it may work from stale GAME_ARCHITECTURE.md or outdated line counts. This is the exact problem session-health was built to prevent.

**Fix:** Add an explicit gate to lead-dev's description and body: "Do not issue architectural opinions until session-health has confirmed docs are current. If session-health has not run this session, run it first." This is a description + one-paragraph addition — not a rebuild.

---

## Problem 3 — skill-audit Is Orphaned ⚠

**What:** skill-audit has no entry point in the normal session flow. Nothing tells Claude to load it. It only runs when explicitly asked ("run an audit", "score this skill"). As a result, skills drift without anyone noticing — the baseline audit from June 19 is the only score on record for most skills.

**Evidence:** skill-audit is called by `project-calendar` and `skill-audit` itself (in its own docs), but not referenced in the session flow skills (session-health, github-sync, session-summary).

**Why it matters:** The whole point of skill-audit is to catch drift before it becomes a real problem. An orphaned audit skill is an audit that never runs.

**Fix:** Wire skill-audit into two places:
1. `session-summary` — after generating a summary, if any skill was loaded or modified this session, offer: "Want me to re-score [skill] while we're here?"
2. `project-calendar` pull_tasks — skill audit tasks should surface in the calendar as scheduled work (they already parse from the audit dir, but the entry point is missing)

---

## Problem 4 — Broken Wires from session-summary ⚠

**What:** The improved session-summary (v2) now correctly offers to run `project-calendar pull_tasks` and `github-sync` at session end. But if this is a planning-only session where github-sync was never bootstrapped, those scripts don't exist in `/tmp` and the offers fail silently.

**Broken paths:**
- `session-summary` → `project-calendar`: says "run pull_tasks" but doesn't check if pull_tasks.py is bootstrapped
- `session-summary` → `github-sync`: says "run github-sync to update docs" but github-sync bootstrap may not have run

**Why it matters:** The session-summary offers are now mandatory (that was the whole point of the v2 improvement). If they fail silently, Cal gets a broken experience at exactly the moment he should be able to trust the workflow.

**Fix:** Add a "Before offering calendar sync, check if /tmp/project-calendar/pull_tasks.py exists. If not, bootstrap it first." guard to session-summary's after-section. Same for github-sync.

---

## Problem 5 — Circular Doc Coupling ⚠

**What:** Three skills form a documentation triangle where each mentions the others:

```
github-sync ←→ session-summary ←→ project-calendar ←→ github-sync
```

At runtime this is fine — there's no infinite loop. But it means:
- If github-sync's session-end workflow changes, session-summary may reference a stale version
- If project-calendar's script names change, session-summary's instructions break
- Updating any one of these three requires cross-checking the other two

**Why it matters:** This is documentation debt. It's low-urgency but compounds: every time one skill is improved, there's a hidden maintenance cost to check and update the other two.

**Fix (long-term):** session-summary should not reference specific script paths from other skills. Instead, it should say "offer to sync calendar (see project-calendar skill)" and let the project-calendar skill handle its own bootstrap. One-directional references only.

---

## What's Working Well

- **Layer 1 → Layer 2 handoff** is solid: session-health → github-sync → lead-dev → contractor chain is correctly documented and Claude follows it reliably
- **github-sync STEP 3** correctly wires to both session-summary and project-calendar
- **session-summary v2** (just shipped, 90/100) is the healthiest skill in the library
- **Small skills are clean**: skill-audit (161), save-skill-workflow (108), session-summary (168) are all under 200 lines and read clearly
- **devvit-pipeline → session-health** integration is explicitly documented in the description

---

## Dependency Map (Text)

```
Who calls whom (→ = depends on / hands off to):

github-sync      → lead-dev, session-summary, project-calendar
devvit-pipeline  → session-health, github-sync
session-health   → wigglers-architecture, lead-dev, contractor
session-summary  → project-calendar, github-sync  [⚠ broken if not bootstrapped]
project-calendar → github-sync
wigglers-arch    → github-sync
lead-dev         → devvit-pipeline
skill-audit      → github-sync  [⚠ orphaned — no entry point]
save-skill-workflow → github-sync
contractor       → (no outgoing deps)
canvas-art-*     → (no outgoing deps)

Most-depended-on (called by the most skills):
  github-sync      ← 7 skills depend on it  [single point of failure]
  lead-dev         ← 4 skills
  session-health   ← 4 skills
  wigglers-arch    ← 3 skills
```

---

*Generated: 2026-06-22 | Next review: after refactor Phase 1 complete*
