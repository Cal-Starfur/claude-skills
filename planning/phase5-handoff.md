# Phase 5 Handoff — Skill Completeness Push
**Date:** 2026-06-22 | **From:** Session 26 | **Repo:** Cal-Starfur/claude-skills

---

## What was completed this session

All four phases of the skill refactor plan are done:

| Phase | What | Result |
|---|---|---|
| 1 — Wiring | lead-dev guard, session-summary guards, skill-audit wired | 3 commits |
| 2 — Right-size | 6 skills, 20 scripts extracted to scripts/ | 28 commits |
| 3 — Quality | 4 low-scoring skills improved | 5 commits |
| 4 — Decoupling | session-summary triangle broken | 1 commit |

**Ecosystem state after this session:**
- 12 skills in claude-skills repo (was 8)
- Avg SKILL.md size: ~240 lines (was ~1,200)
- 20 scripts in scripts/ subfolders (was 0)
- Avg score: 84/100 (was 68/100)
- Zero skills below 80 (was 4)
- Zero circular skill references (was 3)

---

## What Phase 5 is

Phase 5 is not in the original refactor plan — it emerged from the final ecosystem audit.

**The weak dimension is Completeness (avg 78/100).** Every skill is well-structured and right-sized, but most are missing: explicit edge cases, error handling, and "what to do when things go wrong" sections.

**Goal:** Push Completeness from 78 → 85+ across all 12 skills. Target overall ecosystem avg: 88+.

---

## Skills to work on and exactly what to add

### Priority 1 — Core session skills (used every session, must be bulletproof)

**session-health (Complete: 75)**
- Add: what to do if the GitHub API returns 401 mid-session (token expired)
- Add: what to do if `health_check.py` fetch fails (claude-skills repo unreachable)
- Add: explicit guidance when bridge is offline AND version is unknown — which things are still safe to do

**github-sync (Complete: 80)**
- Add: explicit rollback procedure (how to revert a bad commit using the API)
- Add: what to do on 422 SHA conflict in more detail — current doc says "run sync first" but doesn't show the command
- Add: guidance for when the repo is temporarily locked or rate-limited

**session-summary (Complete: 75)**
- Add: what to do when the conversation is too long to reliably identify all commits
- Add: explicit guidance for multi-file sessions (when 10+ files changed)
- Add: example HOLD summary with a build failure commit

### Priority 2 — Work skills

**lead-dev (Complete: 75)**
- Add: what to do when `audit.py` crashes (malformed file, encoding issue)
- Add: explicit guidance when GAME_ARCHITECTURE.md doesn't exist yet on a new project
- Add: what happens if `generate_architecture.py` produces a doc that's obviously wrong

**contractor (Complete: 75)**
- Add: explicit handoff rule — when does contractor escalate to lead-dev? (currently vague)
- Add: what to do when a ticket touches more than one system (currently not covered)
- Add: fallback when `devvit_inspector.py` fails on an unknown file type

**devvit-pipeline (Complete: 80)**
- Add: what to do when `pipeline.py status` hangs (bridge timeout)
- Add: explicit guidance when GitHub Actions build passes but devvit upload fails

### Priority 3 — Utility skills

**project-calendar (Complete: 75)**
- Add: what to do when a repo is unreachable at sync time
- Add: what to do when all tasks in a lane are done (empty lane behaviour)

**skill-audit (Complete: 85)** — already best in class, minor additions only
- Add: guidance on what to do when a skill scores below 50 (currently only covers 65+)

**wigglers-architecture (Complete: 80)**
- Add: explicit "do not touch" list for tube physics / ISS-15 area with error message Claude should output

**canvas-art-optimizer + png-canvas-art-optimizer (Complete: 75 each)**
- Already got fallbacks added in Phase 3
- Add: explicit guidance when the uploaded image is corrupted or unreadable
- Add: size limit guidance (what to do for very large images >2MB)

**save-skill-workflow (Complete: 80)**
- Add: what to do when `present_files` fails silently
- Add: guidance for saving skills that are >500 lines (should they be right-sized first?)

---

## How to run Phase 5

Each skill is a standalone 15-30 min job. Suggested order:

1. `session-health` — most used, most critical
2. `github-sync` — rollback procedure is the most valuable missing piece
3. `session-summary` — long-conversation guidance is genuinely needed
4. `lead-dev` — audit.py crash handling
5. `contractor` — escalation rule clarity
6. `devvit-pipeline` — bridge timeout
7. `project-calendar` — empty lane + unreachable repo
8. remaining 4 — lower priority, batch in one pass

For each skill:
1. Pull fresh from claude-skills: `sync_from_github.py read skills/{name}/SKILL.md --fresh`
2. Add the completeness sections listed above
3. Push to claude-skills
4. Save Skill via present_files
5. Run stress audit: check all new sections are present and coherent

---

## Session startup for Phase 5

```
1. Paste PAT
2. Bootstrap github-sync → point at Cal-Starfur/claude-skills (not Wigglers_Room)
3. Pull this file: planning/phase5-handoff.md
4. Start with session-health — pull, add edge cases, push, save, audit
5. Work down the priority list
```

**Token:** Same PAT format as always — paste fresh, never stored.
**Repo to work in:** `Cal-Starfur/claude-skills` (not Wigglers_Room)
**Branch:** main

---

## Current scores for reference

| Skill | Overall | Completeness | Priority |
|---|---|---|---|
| devvit-pipeline | 86 | 80 | P2 |
| github-sync | 86 | 80 | P1 |
| lead-dev | 86 | 75 | P2 |
| skill-audit | 85 | 85 | P3 |
| project-calendar | 85 | 75 | P2 |
| wigglers-architecture | 84 | 80 | P3 |
| session-health | 84 | 75 | P1 |
| canvas-art-optimizer | 84 | 75 | P3 |
| png-canvas-art-optimizer | 84 | 75 | P3 |
| contractor | 84 | 75 | P2 |
| save-skill-workflow | 84 | 80 | P3 |
| session-summary | 82 | 75 | P1 |

**Ecosystem avg: 84 | Completeness avg: 78 | Target: 88 overall / 85 completeness**

---

*Created: 2026-06-22 | Owner: Cal-Starfur | Next session: Phase 5 — Completeness Push*
