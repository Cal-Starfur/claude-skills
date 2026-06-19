# Skill Audit — project-calendar (Baseline)

**Date:** 2026-06-19
**Auditor:** Claude Sonnet 4.6
**Method:** Full SKILL.md review + live end-to-end sync test
**Baseline run:** Yes — first audit of this skill, built same session

---

## Summary

| Dimension | Score | Grade |
|---|---|---|
| Trigger | 72 | 🟢 Good |
| Content quality | 74 | 🟢 Good |
| Completeness | 63 | 🟡 OK |
| Freshness | 68 | 🟢 Good |
| **Overall** | **69** | **🟢 Good** |

**Live test result:** Passed — "sync the calendar" triggered correctly, pulled 31 tasks from 2 repos, scheduled over 4 weeks, pushed to GitHub cleanly.

---

## Dimension 1 — Trigger (72/100)

### Strengths
- Explicit trigger table with 5 clear scenarios covers the main use cases
- Description mentions calendar, schedule, update, new repo, mark done — good keyword coverage
- "sync the calendar" worked in live test on first try with no coaching
- End-of-session auto-trigger is documented and the intent is right

### Issues
- ⚠️ **CRITICAL:** Description says "triggers automatically at end of any game or skill session" — this is aspirational, not enforced. No other skill calls this one. It will never fire automatically unless Claude happens to read this skill in the same session. Needs to either be removed from the description or enforced via the other skills.
- 🔧 Phase 2 skills were misclassified as P1 in the live run — parser bug makes output wrong. Owner saw incorrect priority on screen.
- 🔧 `sync_done.py` referenced in Step 4 but no such embedded script exists — creates confusion mid-workflow
- 🔧 "What should I work on today?" is the most natural query but isn't listed as a trigger phrase

---

## Dimension 2 — Content Quality (74/100)

### Strengths
- Step-by-step workflow (Steps 0–5) is clear, sequential, and copy-pasteable
- Scheduling rules are explicit and specific — max 2/day, Sunday rest, Saturday light
- Parser documentation is detailed with extraction rules and effort heuristics
- Token sanitization rule has a concrete regex — no ambiguity
- Output format section shows exactly what a successful sync looks like
- Hard rules section covers the key safety and process constraints

### Issues
- ⚠️ Step 4 references `sync_done.py` — script that doesn't exist in embedded scripts. Only 3 scripts are embedded (pull, build, push). Done state sync is actually handled inside `pull_tasks.py`, not a separate script. The step creates false expectations.
- 🔧 Repo registry in SKILL.md body is static markdown — no instruction to keep it updated when repos change. Will quietly drift.
- 🔧 `parse_skills` Phase 1/2 detection is fragile — matches literal "Phase 1" / "Phase 2" in headers. If the planning doc format changes, all skills get misprioritized.
- 🔧 `build_calendar.py` uses `date.today()` — no way to preview a future week's schedule or test the scheduler against a different date
- 🔧 L-task spread rule ("never two L tasks in same week") is in the scheduling rules section but NOT implemented in `build_calendar.py`. It's documented fiction.

---

## Dimension 3 — Completeness (63/100)

### Strengths
- Token sanitization on push is a hard rule with implementation — covered
- Done state persistence via `calendar-done.json` in the repo is solid cross-device solution
- Adding a new repo procedure is documented step-by-step
- Output format after sync is specified so Claude knows what to report

### Issues
- ⚠️ **CRITICAL:** No fallback if a repo is unreachable (network error, private repo, GitHub rate limit). `pull_tasks.py` catches per-repo errors with a print but continues — which means the calendar can be rebuilt and pushed with missing repos silently. Owner sees no warning.
- ⚠️ No approval gate before push — `github-sync` skill requires approve-before-push but this skill pushes directly without showing a diff. Inconsistent with the rest of the ecosystem.
- 🔧 No task ID namespacing — if two repos both have a task called `iss-1`, done state bleeds between them (marking one done marks both done in localStorage)
- 🔧 No CHANGELOG update step — every other skill in the ecosystem updates `CHANGELOG.md` after changes, this one doesn't
- 🔧 No instruction for what to do when `tasks.json` is empty (total parse failure)
- 🔧 No guidance on manually adding a one-off task that doesn't come from any repo file
- 🔧 `sync_done.py` step is documented but the script doesn't exist — broken workflow step

---

## Dimension 4 — Freshness (68/100)

### Strengths
- Pulls live from GitHub every sync — no baked-in static task data
- `calendar-done.json` in the repo means done state survives session resets and device switches
- `parse_wigglers` reads `WIGGLERS_AUDIT.md` directly — task list will stay current as the audit is updated
- Repo registry is in the skill body, not hardcoded somewhere inaccessible

### Issues
- ⚠️ Repo registry is duplicated: once in the SKILL.md body and once hardcoded in `pull_tasks.py` REGISTRY list. These two will silently diverge. The SKILL.md version is documentation; the Python list is what actually runs.
- 🔧 `parse_skills` Phase detection depends on literal "Phase 1" / "Phase 2" text in planning doc — brittle to doc restructuring
- 🔧 No version or last-synced timestamp written back to the skill itself after a run
- 🔧 Space-Cats-Game-2026 listed as "when active" — no definition of what "active" means or who decides
- 🔧 Calendar HTML shows "Last built: {date}" but no reference to which skill version or repo commit built it — makes it hard to debug stale calendars

---

## Priority Fix List

| Priority | Fix | Impact |
|---|---|---|
| 🔴 High | Remove "auto-triggers" claim from description OR enforce it in other skills | Trigger honesty — currently a false promise |
| 🔴 High | Add network error fallback in pull_tasks.py with visible warning | Prevents silent partial calendar |
| 🔴 High | Remove Step 4 sync_done.py reference OR write the script | Broken workflow step |
| 🟡 Med | Namespace task IDs by repo (e.g. `wigglers:perf-1`) | Prevents done-state bleed |
| 🟡 Med | Add approve-before-push gate consistent with github-sync | Ecosystem consistency |
| 🟡 Med | Fix parse_skills Phase 1/2 priority assignment | Phase 2 skills showing as P1 |
| 🟡 Med | Implement L-task spread rule in build_calendar.py | Currently documented but ignored |
| 🟡 Med | Add CHANGELOG update step to sync workflow | Consistency with ecosystem |
| 🟡 Med | Single source of truth for repo registry (Python only, not duplicated in markdown) | Prevents drift |
| 🟢 Low | Add "what should I work on today" as trigger phrase | More natural entry point |
| 🟢 Low | Add manual task injection support | Useful edge case |
| 🟢 Low | Add last-synced commit reference to calendar HTML footer | Debuggability |

---

## What Worked Well (Keep)

- The **4-step pipeline** (pull → build → push) is clean and worked first try
- **Token sanitization** before push is solid — GitHub secret scan confirmed it blocks raw tokens
- **calendar-done.json** as cross-device done state is the right architecture
- **Per-repo parser pattern** is the right extensibility model — adding Space Cats will be one function
- **Scheduling rules** (max 2/day, rest Sunday, light Saturday) are exactly right for the use case

---

## Baseline Score: 69/100 🟢 Good

This is a strong first version that works end-to-end. The gaps are real but not fatal — the core loop (pull → build → push) is solid. The biggest risks are the silent failure modes: repos going unreachable without warning, and the broken sync_done.py reference confusing a future session.

**Target score after fixes: 85+**
**Next audit: after fixing the 3 High priority issues**

*Generated: 2026-06-19 | Auditor: Claude Sonnet 4.6*
