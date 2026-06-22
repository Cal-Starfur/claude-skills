# Skill Refactor Plan — June 22, 2026

**Source:** skill-health-report.md (same date)
**Goal:** Right-size all skills to <500 lines, fix all broken wiring, establish stable load order
**Work order:** Priority × effort. Each phase is one session of focused work.

---

## Phase 1 — Fix the Wiring (Low effort, high impact)

*Estimated: 1 session. No rebuilds — just targeted doc patches.*

### 1a. Fix lead-dev load order conflict

**File:** `skills/lead-dev/SKILL.md`
**Change:** Add to description and top of body:

> "Do not issue architectural opinions or pull files until session-health has confirmed docs are current for this session. If session-health has not run, check: does `/tmp/sh_arch.md` exist? If not, session-health has not run — load it first before proceeding."

**Why:** Prevents lead-dev from running on stale docs before session-health has done its health check.
**Effort:** 1 paragraph added to description + 1 paragraph in body. ~30 min.

---

### 1b. Fix session-summary bootstrap guards

**File:** `skills/session-summary/SKILL.md`
**Change:** In the "After the Summary" section, add before the calendar sync offer:

> "Before offering calendar sync: check if `/tmp/project-calendar/pull_tasks.py` exists. If not, bootstrap the project-calendar skill first (run its bootstrap block), then offer. Before offering doc updates via github-sync: check if `/tmp/github-sync/scripts/propose_commit.py` exists. If not, bootstrap github-sync first."

**Why:** The session-summary offers are mandatory — but they fail silently if scripts aren't bootstrapped. This guard makes the offer reliable even in planning-only sessions.
**Effort:** 3–4 lines added to one section. ~20 min.

---

### 1c. Wire skill-audit into session flow

**File:** `skills/session-summary/SKILL.md`
**Change:** Add a third after-summary offer:

> "3. **Skill audit** — 'A skill was loaded/modified this session — want me to re-score it while we're here?' Offer only if: a skill was explicitly improved or created this session, OR any skill's score was noted as below 75."

**Also:** `skills/skill-audit/SKILL.md` — update description to include:
> "Also triggers automatically when session-summary is run and a skill was modified."

**Why:** skill-audit is currently orphaned. Wiring it to session-summary gives it a natural entry point without adding noise to every session.
**Effort:** One paragraph in session-summary + description update in skill-audit. ~20 min.

---

## Phase 2 — Right-Size the Big Skills (Medium effort, medium impact)

*Estimated: 2–3 sessions. Extract embedded scripts without changing any logic.*

**Rule for every right-sizing task:**
- Extract Python/JS embedded in SKILL.md to `skills/{name}/scripts/`
- SKILL.md bootstrap block changes from "write this code..." to "copy from `skills/{name}/scripts/`"
- All logic stays identical — this is a pure structural move
- After extraction: run audit and confirm score is maintained or improved

---

### 2a. Right-size session-health (682 → target ~200 lines)

**Embedded script to extract:** `health_check.py` (~480 lines)
→ Move to `skills/session-health/scripts/health_check.py`

SKILL.md bootstrap changes from embedding the full script to:
```
python3 -c "
import urllib.request, base64, json
# fetch skills/session-health/scripts/health_check.py from claude-skills repo
# write to /tmp/session-health/health_check.py
"
```

**Effort:** Extract script, update bootstrap block, test that health check still runs. ~1 hour.

---

### 2b. Right-size project-calendar (941 → target ~200 lines)

**Embedded scripts to extract:**
- `pull_tasks.py` (~274 lines) → `skills/project-calendar/scripts/pull_tasks.py`
- `build_calendar.py` (~224 lines) → `skills/project-calendar/scripts/build_calendar.py`
- `push_calendar.py` (~81 lines) → `skills/project-calendar/scripts/push_calendar.py`

SKILL.md bootstrap becomes a fetch-from-GitHub step instead of write-from-embedded-text.

**Effort:** 3 scripts to extract. ~1.5 hours.

---

### 2c. Right-size github-sync (1353 → target ~250 lines)

**Embedded scripts to extract:**
- `tools/github_client.py` (~300 lines) → `skills/github-sync/scripts/github_client.py`
- `scripts/propose_commit.py` (~400 lines) → `skills/github-sync/scripts/propose_commit.py`
- `scripts/sync_from_github.py` (~350 lines) → `skills/github-sync/scripts/sync_from_github.py`

**Note:** github-sync is the most-depended-on skill (7 skills call it). Test carefully — a broken github-sync breaks everything.

**Effort:** 3 scripts. Test that stage/push/read all still work after extraction. ~2 hours.

---

### 2d. Right-size devvit-pipeline (1868 → target ~200 lines)

**Embedded scripts to extract:**
- `pipeline.py` (~large) → `skills/devvit-pipeline/scripts/pipeline.py`
- Any other embedded helpers

**Effort:** ~1.5 hours. Test that `pipeline.py status` and deploy still work.

---

### 2e. Right-size contractor (925 → target ~300 lines)

**No embedded scripts** — contractor is large due to extensive inline reference material (two-worlds model, naming conventions, variable tables). These are reference docs, not scripts.

**Split approach:**
- Keep core instructions in SKILL.md (~300 lines)
- Move reference tables to `skills/contractor/references/wigglers-reference.md`
- SKILL.md references it: "For variable naming conventions and the two-worlds model, see `references/wigglers-reference.md`"

**Effort:** ~1 hour. Structural split, no logic changes.

---

### 2f. Right-size lead-dev (3060 → target ~300 lines)

**Largest skill in the library at 3060 lines — 6× the cap.**

lead-dev is large for two reasons:
1. Embedded scripts (analyze_patterns.py and others)
2. Extensive inline reference material baked into SKILL.md

**Split approach:**
- Core instructions: ~300 lines in SKILL.md
- Scripts → `skills/lead-dev/scripts/`
- Reference material → `skills/lead-dev/references/` (naming conventions, session log format, architecture patterns)
- SKILL.md references each: "For naming conventions, see `references/naming.md`. For session log format, see `references/session-log.md`."

**Effort:** Largest job. ~2–3 hours. Multiple reference docs. Test that lead-dev still functions correctly after split.

---

## Phase 3 — Improve Low-Scoring Skills (Medium effort, quality uplift)

*Estimated: 1–2 sessions. Run after Phase 1 + 2 are stable.*

### 3a. png-canvas-art-optimizer (60/100 → target 80+)

**Issues from baseline audit:**
- Promises iteration loop but none is documented
- Claude vision API approach relies on implicit knowledge — not written down
- No workaround for photorealistic images beyond "won't work well"

**Fix:** Document the actual iteration workflow step by step. Add a concrete example of the vision API prompt used to reverse-engineer shapes.

---

### 3b. canvas-art-optimizer (68/100 → target 80+)

**Issues from baseline audit:**
- No fallback when 95% convergence target can't be reached
- Skill goes silent on failure — no guidance

**Fix:** Add explicit fallback section: "If pixel diff hasn't converged after N iterations, present best result so far and ask user if they want to continue or accept."

---

### 3c. wigglers-architecture (72/100 → target 85+)

**Issues from baseline audit:**
- Version numbers and line counts baked in — drifts every session
- Says "fetch fresh files via github-sync" but doesn't enforce it procedurally

**Fix:** Remove all hardcoded versions/line counts. Add explicit: "At session start, always pull fresh GAME_ARCHITECTURE.md via github-sync before reading any game state from this skill."

---

### 3d. save-skill-workflow (72/100 → target 82+)

**Issues from baseline audit:**
- Copy-paste error in example template
- No guidance on multi-file skills with bundled assets

**Fix:** Fix the copy-paste error. Add one paragraph on multi-file skills (scripts/, references/ pattern).

---

## Phase 4 — Reduce Doc Coupling (Low effort, long-term maintenance)

*Estimated: 1 session. Do last, after all skills are stable.*

### 4a. Break the github-sync ↔ session-summary ↔ project-calendar triangle

**Current:** Each skill references the other two by name and specific script paths.
**Target:** One-directional only. session-summary says "offer calendar sync (see project-calendar skill)" — not "run pull_tasks.py → build_calendar.py → push_calendar.py".

This means session-summary doesn't break if project-calendar's script names change.

**Effort:** Trim 3–5 lines from session-summary's after-section. ~15 min.

---

## Work Order Summary

| Phase | What | Sessions | Priority |
|---|---|---|---|
| 1a | lead-dev load order fix | 0.5 | 🔴 Do first |
| 1b | session-summary bootstrap guards | 0.5 | 🔴 Do first |
| 1c | wire skill-audit into flow | 0.5 | 🟡 Do soon |
| 2a | right-size session-health | 1 | 🟡 Do soon |
| 2b | right-size project-calendar | 1 | 🟡 Do soon |
| 2c | right-size github-sync | 1 | 🟡 Critical path |
| 2d | right-size devvit-pipeline | 1 | 🟡 Do soon |
| 2e | right-size contractor | 0.5 | 🟢 When ready |
| 2f | right-size lead-dev | 1.5 | 🟢 Largest job |
| 3a–d | improve low-scoring skills | 1–2 | 🟢 When ready |
| 4a | break doc coupling triangle | 0.5 | 🟢 Last |

**Total estimated work:** ~10–12 hours across 4–5 sessions.

---

## Session Startup for This Work

Every session working on skill refactor:

1. Check this file first — pick the next unchecked item
2. Bootstrap github-sync → point at `Cal-Starfur/claude-skills`
3. Pull the skill being worked on fresh: `sync_from_github.py read skills/{name}/SKILL.md --fresh`
4. Make changes → stage → show diff → get approval → push
5. Run audit on the modified skill before ending session
6. Mark item done in this doc and push updated plan

---

## Definition of Done

A skill is "done" for this refactor when:
- SKILL.md is under 500 lines
- All embedded scripts are in `scripts/` subfolder
- Audit score is 80+ (or 85+ for core session skills)
- Load order is compatible with the layer model above
- No circular references to other skills by script path

---

*Created: 2026-06-22 | Owner: Cal-Starfur | Track in project-calendar under claude-skills (skills) lane*
