# Deep Audit — wigglers-architecture

**Date:** 2026-06-19
**Baseline score:** 72/100
**Auditor:** Claude Sonnet 4.6
**Method:** Full SKILL.md review cross-referenced against live GAME_ARCHITECTURE.md (commit 66f1230)

---

## Score

| Dimension | Baseline | This audit | Change |
|---|---|---|---|
| Trigger | 88 | 88 | — |
| Content quality | 75 | 45 | ▼ -30 |
| Completeness | 70 | 40 | ▼ -30 |
| Freshness | 55 | 30 | ▼ -25 |
| **Overall** | **72** | **51** | **▼ -21** |

**Verdict: 🔴 Urgent — skill is significantly stale. Will cause bad edits if loaded as-is.**

---

## What's Wrong — Specific Drift Findings

### 🔴 CRITICAL — Version / Session number wrong
- **Skill says:** V21, Session 8, ~8,579 lines (game.js), ~910 lines (main.tsx)
- **Reality:** Session 19, ~8,645 lines (game.js), ~500 lines (main.tsx)
- **Risk:** Claude will have wrong mental model of how far the codebase has evolved. 11 sessions of changes are invisible.

### 🔴 CRITICAL — Preview screen architecture is wrong
- **Skill says:** preview uses animated SVG with 33 falling trash items via `buildBgDataUrl(tick)` and `useInterval`
- **Reality:** Preview is now a **static** `<zstack>` with `preview-bg.png` + `icon.png`. The entire animated preview was replaced with a static image. The `buildBgDataUrl` function, the `useInterval`, and all the trash-item animation logic described in the skill **no longer exist in main.tsx**.
- **Risk:** If Claude tries to edit the preview using the skill's instructions, it will look for functions that don't exist and potentially break the working static implementation.

### 🔴 CRITICAL — MSG_SET_WEATHER removed
- **Skill says:** `MSG_SET_WEATHER` is in the Host→Webview message list
- **Reality:** `MSG_SET_WEATHER` was removed — weather is now a fully self-contained simulation in game.js with no external data. GAME_ARCHITECTURE.md explicitly flags this.
- **Risk:** Any session that adds weather-related features using the skill will wire up a dead message type.

### 🔴 CRITICAL — draw/updatePhysics/updatePlayer split was REVERTED
- **Skill says:** `draw()` calls 8 named subfunctions, `updatePhysics()` calls 4, `updatePlayer()` calls 6
- **Reality:** All three are back to monoliths (S5 refactor reverted). `draw()` ~2,022 lines, `updatePhysics()` ~815 lines, `updatePlayer()` ~646 lines. Re-splitting is flagged as P2.
- **Risk:** Claude will look for subfunctions that don't exist, try to edit the wrong place.

### 🔴 CRITICAL — MSG_* constants not in game.js
- **Skill says:** "All MSG_* constants are defined in both game.js and main.tsx. Never use raw strings."
- **Reality:** GAME_ARCHITECTURE.md explicitly flags: "⚠️ game.js uses raw strings — MSG_* constants not yet applied (S2 work reverted). Re-applying is P2."
- **Risk:** Claude will write code using MSG_* constants in game.js that won't match the raw strings actually in the file, silently breaking message routing.

### 🟡 MEDIUM — KV Store key names are wrong
- **Skill says:** `worm:{username}`, `world:{postId}`, `cocoons:{postId}`, `week:{postId}`, `queue:{postId}`
- **Reality:** `KV_WORM_SESSION(username)`, `KV_WORLD(postId)`, `KV_COCOONS(postId)`, `KV_WEEK(postId)`, `KV_QUEUE(postId)` — named constants, not raw strings
- **Risk:** Wrong key format in any Redis call will silently write/read from wrong namespace.

### 🟡 MEDIUM — Session fields incomplete
- **Skill says:** session fields include `ts, karma, pEaten, pSR, pSEG, pHP, pGut, pX, pY, pSleeping, pSleepX, pSleepY, cocoons, lastCocoonLaid, weekStartTs, weeklyContrib, tLvl, pooled, castingEnrichment, drops`
- **Reality:** Also includes `bornTs`, `generation`, `emergencyKarmaPot`, `emergencyRequested`, `diedTs`, `deathCause` — all added across sessions 9–19
- **Risk:** Missing fields will be dropped in saves, causing data loss bugs.

### 🟡 MEDIUM — Audit priority table is stale
- **Skill says:** Only item 4 (DEBUG_PASSWORD) remains open
- **Reality:** ISS-13 and ISS-14 are open. ISS-14 (session restore bug — pHP hardcoded to 1.0 on load, no save-on-exit) is the current P1. Several S2/S4/S5 items listed as DONE were reverted.
- **Risk:** Claude won't know the actual P1 task or that previously "done" items need re-doing.

### 🟡 MEDIUM — _underscore functions listed as done
- **Skill says:** "Rename _underscore functions (11) ✅ DONE Session 4"
- **Reality:** GAME_ARCHITECTURE.md: "⚠️ 17 _underscore functions still present (S4 rename reverted — P2)"
- **Risk:** Claude may create new `_underscore` functions thinking it's OK or avoid them unnecessarily.

### 🟢 LOW — `weekStartTs` not in global state section
- **Skill** doesn't mention `weekStartTs` as a global var
- **Reality:** It's a critical shared var — the weekly drain cycle depends on it, shipped S16

### 🟢 LOW — `scrapsLevel` listed as world/shared var but labeled wrong
- Skill lists `scrapsLevel` as `var scrapsLevel = 1.0` — correct value but it's now `window._hostScrapsLevel` during setup; naming has nuance

---

## What's Still Good

- Trigger description: excellent — very specific, loads reliably ✅
- Two-process split diagram: still accurate ✅
- World layout / tier geometry: Y-coordinate system unchanged ✅
- Drain system (down drain / up drain logic): still accurate ✅
- `pPath` point properties table: still accurate ✅
- Mobile bridge `postToHost` implementation: still accurate ✅
- Safe editing protocol (8 rules): still accurate ✅
- Core player vars (pHP, pGut, pSEG, karma, pPath, pSegs): still accurate ✅
- Multiplayer `otherPlayers` shape: still accurate ✅

---

## Required Fixes Before Next Session

1. **Update version/session** → Session 19, game.js ~8,645 lines, main.tsx ~500 lines
2. **Replace entire preview screen section** → static `<zstack>` with preview-bg.png + icon.png. Remove all `buildBgDataUrl`, `useInterval`, animation description.
3. **Remove MSG_SET_WEATHER** from message constants. Add note: weather is self-contained in game.js.
4. **Fix draw/updatePhysics/updatePlayer** → mark as monoliths (refactor reverted, P2 to re-do)
5. **Fix MSG_* constants note** → game.js uses raw strings, not constants (reverted, P2)
6. **Update KV key names** → use `KV_WORM_SESSION`, `KV_WORLD`, etc.
7. **Add missing session fields** → bornTs, generation, emergencyKarmaPot, emergencyRequested
8. **Update audit priority table** → ISS-14 is current P1; mark reverted items as reverted
9. **Add weekStartTs** to global state section
10. **Add enforcement step** → skill must require github-sync pull of GAME_ARCHITECTURE.md at session start before any code edits

---

## Root Cause

The skill was written from a snapshot after Session 8. It has not been updated across 11 subsequent sessions. The skill should not be a snapshot — it should be a pointer to the live `GAME_ARCHITECTURE.md` on GitHub, with only stable/rarely-changing knowledge baked in directly.

**The fix:** Restructure the skill so that session-specific data (version, line counts, function registry, audit queue) is fetched live from GitHub. Only stable structural knowledge (world layout, drain mechanics, mobile bridge pattern, editing protocol) lives in the skill body.

---

*Audited: 2026-06-19 | Previous score: 72 | This audit score: 51 | Delta: -21*
