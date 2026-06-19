# Deep Audit — session-health (v2 live run)

**Date:** 2026-06-19
**Previous score:** 94/100 (static test)
**This score:** 97/100 (live execution)
**Auditor:** Claude Sonnet 4.6
**Method:** 6 live test cases executed against real GitHub repos and bridge relay

---

## Score

| Dimension | Static (v1) | Live (v2) | Change |
|---|---|---|---|
| Trigger | 95 | 95 | — |
| Content quality | 96 | 98 | ▲ +2 |
| Completeness | 97 | 98 | ▲ +1 |
| Freshness | 90 | 97 | ▲ +7 |
| **Overall** | **94** | **97** | **▲ +3** |

---

## Live Test Results — 6/6 Pass

| Test | What was tested | Result |
|---|---|---|
| T1 — Normal session start | Bridge online → all clear → clean P1 display | ✅ pass |
| T2 — Bridge offline | Warning only, session proceeds — not blocked | ✅ pass |
| T3 — Stale session number | Detected Session 19 vs 20, auto-fixed commit 1771fcc | ✅ pass |
| T4 — Post-session update | Bumped Session 21 / 0.0.182, pushed, reverted cleanly | ✅ pass |
| T5 — Stale Devvit version | Detected 0.0.179 vs 0.0.181, auto-fixed arch + devvit.yaml | ✅ pass |
| T6 — Critical doc drift | ISS-14 injected as P1 → 🔴 CRITICAL flagged correctly | ✅ pass |

---

## Bugs Found by Live Testing (Missed by Static)

All 5 bugs were caught by actually running the script — the static test couldn't see them.

| Bug | Impact | Fixed |
|---|---|---|
| Bridge reads `output` field — bridge3.js uses `stdout` | Version always returned None | ✅ |
| P1 displayed with raw markdown `**bold**` | Unreadable output | ✅ |
| P1 description printed twice | Duplicate lines in output | ✅ |
| `devvit.yaml` wrong version source (0.1.0 our value vs 0.0.181 Reddit's) | Architecture flaw — wrong source entirely | ✅ relay/version.json |
| bridge3.js crashed on 409 SHA conflict → process.exit(1) | Bridge died constantly during probe sessions | ✅ retry loop + catch-all |

---

## Architecture Changes Made During Testing

**Version tracking redesign:**
- Old: read `devvit.yaml` via bridge → wrong, that's our manual value
- Old: trigger `devvit upload` to get version → destructive, can't run every session
- New: `relay/version.json` stores version captured from upload stdout
- New: bridge offline = warning only, session never blocked
- New: version confirms itself naturally after first upload

**bridge3.js hardening:**
- Old: any error in loop → `Fatal:` → `process.exit(1)` → bridge dies
- New: 409 on write result → retry 3x with fresh SHA fetch
- New: any other loop error → `⚠ loop error (recovering)` → keep polling
- Only startup errors (missing token) exit the process

**Output classification:**
- 🔴 CRITICAL: wrong P1, ghost messages — would cause bad code edits
- ⚠ DOC DRIFT: stale session/version/line counts — auto-fixed
- Bridge offline: warning only — version unknown until next upload

---

## Key Lesson

Static tests check code structure. Live tests find real bugs.
For any skill with an embedded script, always run it against real infrastructure.
The 5 bugs caught here cost ~0 if found in live testing, significant if discovered mid-session.

---

## Current State

The skill is production-ready. It runs every session start, fixes what it can automatically,
warns about the rest, and never blocks work over version uncertainty.

*Audited: 2026-06-19 | v1 score: 94 | v2 score: 97 | Delta: +3*
