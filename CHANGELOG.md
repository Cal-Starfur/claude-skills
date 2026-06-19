# Skill Changelog

Tracks all skill changes across sessions. Newest entries at the top.

---

## 2026-06-19 — Baseline Audit

- Created `claude-skills` repo
- Ran baseline audit on all 9 installed skills
- Documented scores in `audits/2026-06-19-baseline.md`
- Average score: 68/100
- Strongest: github-sync (88), lead-dev (85), contractor (82)
- Weakest: png-canvas-art-optimizer (60)

**Skills installed as of this date:**
github-sync, lead-dev, contractor, devvit-pipeline, wigglers-architecture,
save-skill-workflow, canvas-art-optimizer, png-canvas-art-optimizer, skill-creator (public)

---

*Format: YYYY-MM-DD — Session description*
*Include: what changed, why, score before/after if applicable*

## 2026-06-19 - Deep Audit: wigglers-architecture

- Pulled live game.js, main.tsx, GAME_ARCHITECTURE.md, WIGGLERS_AUDIT_V20.md from GitHub
- Skill was a Session 8 snapshot -- game is at Session 20 (12 sessions of drift)
- Score dropped: 72 -> 51 on re-audit against live files
- Critical errors: animated preview described (removed), MSG_SET_WEATHER listed (removed),
  draw() subfunctions described (reverted to monolith), pooled synced (now runtime-only),
  pAcid/bornTs missing from session fields, 14 open issues invisible
- Rebuilt skill from live files: now pulls GAME_ARCHITECTURE.md at session start
- Added: PERF-1/PERF-2 (P1 perf issues), FEAT-1/FEAT-2 designs, S20 changes,
  full Devvit platform rules, coordinate system, rain removal, ISS-14 fix
- Skill: wigglers-architecture rebuilt from Session 20 (was Session 8 snapshot)
