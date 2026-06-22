---
name: session-summary
description: Generates a plain-English session summary after any coding session. Tells the owner what changed, what system it touched, what could break, and gives an explicit push Y/N recommendation. No code in the output — owner-readable only. Load this skill and offer a summary proactively at session end — do not wait to be asked. Triggers on: "what changed", "give me the summary", "should I push", "wrap up", "end of session", "I'm done", "that's it for today", "ok thanks", "good session", or any signal the user is finishing up. Also triggers automatically after any session with 3 or more commits.
---

# Session Summary Skill

**One job: tell the owner what happened in plain English.**
No code. No jargon. Every file named. Every risk flagged. End with a clear push recommendation.

**Offer this proactively** — do not wait for the user to ask. After the last commit of a session, say:
> "Want me to give you the session summary before we wrap up?"

---

## When to Run

| Trigger | Action |
|---|---|
| "what changed this session" | Full summary |
| "give me the summary" | Full summary |
| "should I push" | Full summary + push recommendation |
| "wrap up" / "end of session" | Full summary + calendar sync offer |
| "I'm done" / "that's it" / "ok thanks" / "good session" | Offer the summary, then generate if user agrees |
| After any session with 3+ commits | Offer automatically after last push |
| Zero commits this session | Summary still runs — say what was discussed/planned, recommend PUSH (nothing to break) |

---

## Scope: What to Include

Before writing, scan the conversation for commits. Use only **this session's** commits — not old ones from prior conversations.

**Commit signals to look for in the conversation:**
- Output from `propose_commit.py push` — the commit SHA and message confirm what shipped
- Files staged via `propose_commit.py stage` — named in the staging output
- Build pass/fail from `pipeline.py status` — look for ✓ or ✗ in chat output

If the conversation is long (100+ messages) and it's unclear which commits belong to this session, ask:
> "Which commits should I include — everything since [earliest commit visible], or just the most recent batch?"

**Do not re-fetch GitHub to write the summary.** Everything needed is in the conversation.

---

## Output Format

Always exactly this structure. No deviations. No code blocks. No function names.

---

**SESSION SUMMARY — [Date] | [Devvit version if applicable]**

**What changed:**
One paragraph. Name every file touched. Say what each change does in plain English. If no code changed, say so explicitly: "No code was changed this session — the work was [planning / doc updates / debugging investigation]."

**What this touches:**
One sentence per system affected. If no code changed, write: "No systems touched — documentation only."

**What could break:**
Be specific. Name the exact feature at risk and why. If nothing is fragile, say: "No new logic was introduced — risk is low." Never write vague phrases like "may cause issues" or "could affect performance."

**For Wigglers Room sessions — always check these systems specifically:**
- Tube physics / worm tea liquid flow — any change near pPath, world-Y, or tube direction logic is high risk
- KV store reads/writes — pooled sync, cocoon state, weekly drain cycle
- Drain cinematic — triggers on sump fill; easy to break silently
- Preview / loading screen — Devvit-specific, breaks differently than in-browser

**Push recommendation:**
PUSH or HOLD — then one sentence why.

---

## Rules

1. **No code in the summary.** Not even a function name in backticks. Pure English.
2. **Name every file touched.** Even doc-only changes.
3. **Be specific about risk.** "Could break" means naming the exact feature at risk, not "may cause issues."
4. **Push recommendation is mandatory.** Never end without PUSH or HOLD.
5. **Zero-code sessions get a summary too.** Say what was discussed or planned. Recommend PUSH (nothing was changed that could break).
6. **Doc-only sessions** — name the docs changed and what was updated. Recommend PUSH unless the docs contain known errors.
7. **If a build failed this session** — always HOLD, name the failing commit.
8. **Keep it short.** The owner should be able to read the full summary in 60 seconds.
9. **Offer proactively.** Never wait to be asked. After the last push, offer the summary without being prompted.

---

## After the Summary — Always Offer Both

After every summary, always offer these two follow-ups:

1. **Calendar sync** — "You cleared [N] tasks today — want me to sync the calendar so it repacks from today?"
   - Offer this if 1 or more tasks were completed
   - Before running: check if `/tmp/project-calendar/pull_tasks.py` exists. If not, bootstrap the project-calendar skill first (run its bootstrap block), then proceed.
   - If user says yes → run project-calendar pull_tasks → build → push

2. **Doc updates** — "Should I update the architecture docs or audit log to reflect what shipped?"
   - Offer this if any game files changed
   - Before running: check if `/tmp/github-sync/scripts/propose_commit.py` exists. If not, bootstrap github-sync first (run its bootstrap block), then proceed.
   - If user says yes → run github-sync to update GAME_ARCHITECTURE.md or WIGGLERS_AUDIT.md as needed

Both offers are **mandatory** — make them in the same message as the summary. The user should never have to remember to ask.

Exception: if the user is clearly in a hurry and just said "thanks, bye" — skip the offers and let them go.

---

## Example — Good Summary (Code Changes)

**SESSION SUMMARY — 2026-06-20 | Devvit 0.0.186**

**What changed:**
Three files were updated. game.js received four performance improvements: drop routing now uses a spatial bucketing system to scan far fewer tunnel points per frame, the grass blade horizon strip is now pre-drawn once at startup instead of rebuilt every frame, the nibble particle limit was lowered from 300 to 80, and settled compost fragments no longer trigger unnecessary rotation calculations. WIGGLERS_AUDIT.md was updated to mark two performance tasks as complete, log a new physics bug, and close a long-standing verification item about liquid saturation.

**What this touches:**
Drop physics — how liquid finds and routes through tunnels. Rendering — grass horizon, debris particles, and compost fragment drawing. Documentation — the audit log and session history.

**What could break:**
The tunnel drop scan is new logic. If drops stop attaching to tunnels or behave oddly after heavy digging, the spatial bucket index is the first place to check — specifically whether tunnel points are being inserted and cleaned up correctly when tunnels are pruned. The grass blade pre-render is built once at startup — if the horizon looks wrong after a screen resize, the blade canvas may need to be rebuilt on resize. Lowering the debris cap to 80 means heavy eating sessions will see fewer lingering nibble particles; this is intentional but worth watching if it feels visually sparse.

**Push recommendation:**
PUSH — all four changes are performance optimisations with no new gameplay logic, the build passed on every commit, and playtesting showed correct behaviour throughout.

---

Want me to sync the calendar? You cleared 2 tasks today (PERF-3 and PERF-4). And should I update the audit log to reflect what shipped?

---

## Example — Doc-Only Summary

**SESSION SUMMARY — 2026-06-22**

**What changed:**
No code was changed this session. WIGGLERS_AUDIT.md was updated to log ISS-19 and mark ISS-13 as closed. GAME_ARCHITECTURE.md had the session number bumped and the P1 queue updated.

**What this touches:**
Documentation only — no game systems were modified.

**What could break:**
Nothing. No code was introduced or changed.

**Push recommendation:**
PUSH — documentation updates only, no risk.

---

Want me to sync the calendar? You cleared 1 task today (the audit log update).

---

## Example — HOLD Summary

**SESSION SUMMARY — 2026-06-20 | Devvit 0.0.183**

**What changed:**
game.js was updated to split the main draw function into smaller sub-functions. The change touched around 400 lines across the rendering path.

**What this touches:**
Rendering — the entire draw loop and how each layer is called.

**What could break:**
The draw loop split is a large structural change. Any call order mistake between sub-functions could cause layers to render in the wrong order — for example the HUD drawing over game elements, or the background not clearing correctly. This type of regression is hard to spot without testing every game state (dead screen, drain cinematic, flood mode, multiplayer).

**Push recommendation:**
HOLD — the build passed but the change is large and was not fully playtested. Recommend creating a new Reddit post and testing at minimum: normal play, death screen, drain cinematic, and flood event before pushing.

---

Should I update the architecture docs to reflect the draw function restructure?
