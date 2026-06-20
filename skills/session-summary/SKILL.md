---
name: session-summary
description: Generates a plain-English session summary after any coding session. Tells the owner what changed, what system it touched, what could break, and gives an explicit push Y/N recommendation. No code in the output — owner-readable only. Triggers when the user says "what changed", "give me the summary", "should I push", "wrap up", "end of session", or asks what happened this session.
---

# Session Summary Skill

**One job: tell the owner what happened in plain English.**
No code. No jargon. Every file named. Every risk flagged. End with a clear push recommendation.

---

## When to Run

| Trigger | Action |
|---|---|
| "what changed this session" | Full summary |
| "give me the summary" | Full summary |
| "should I push" | Full summary + push recommendation |
| "wrap up" / "end of session" | Full summary + calendar sync offer |
| After any session with 3+ commits | Offer automatically |

---

## Output Format

Always exactly this structure. No deviations. No code blocks.

---

**SESSION SUMMARY — [Date] | [Devvit version if applicable]**

**What changed:**
[One paragraph. Name every file touched. Say what each change does in plain English. Example: "game.js was updated in three places: the drop attachment scan now uses a spatial index to find nearby tunnel points faster, the grass blades are now drawn from a pre-built image instead of thousands of individual triangles, and the debris particle limit was lowered from 300 to 80."]

**What this touches:**
[One sentence per system affected. Example: "Drop physics — how liquid finds and follows tunnels. Rendering — how the grass horizon and debris fragments are drawn each frame."]

**What could break:**
[Honest list of risks. If nothing is fragile, say so. Example: "The tunnel drop scan is new logic — if drops stop attaching to tunnels, this is the first place to check. The grass blades are pre-rendered at startup — if the horizon line looks wrong after a resize, the blade canvas may need rebuilding on resize too."]

**Push recommendation:**
[PUSH or HOLD, then one sentence why. Example: "PUSH — all changes are performance improvements with no new logic paths, build passed, and the game played correctly in playtesting."]

---

## Rules

1. **No code in the summary.** Not even a function name in backticks. Pure English.
2. **Name every file touched.** Even doc-only changes.
3. **Be specific about risk.** "Could break" means naming the exact feature at risk, not "may cause issues."
4. **Push recommendation is mandatory.** Never end without PUSH or HOLD.
5. **If the session had no code changes** (docs only, planning only) — say so explicitly and recommend PUSH unless the docs are wrong.
6. **If a build failed this session** — always HOLD, name the failing commit.
7. **Keep it short.** The owner should be able to read the full summary in 60 seconds.

---

## Reading Session Context

To write an accurate summary, Claude reads:

- The conversation history — what files were staged, what commits were pushed
- Commit messages from this session (from `propose_commit.py` output visible in chat)
- Any test results or playtest feedback mentioned in the conversation
- The build status (passed/failed) from `pipeline.py status` output if visible

Claude does NOT need to re-fetch GitHub for a summary — the session conversation contains everything needed.

If the conversation is long and context is unclear, Claude can ask:
> "Which commits should I include in the summary — everything since [first commit], or just the most recent batch?"

---

## Example — Good Summary

**SESSION SUMMARY — 2026-06-20 | Devvit 0.0.186**

**What changed:**
Three files were updated. game.js received four performance improvements: drop routing now uses a spatial bucketing system to scan far fewer tunnel points per frame, the grass blade horizon strip is now pre-drawn once at startup instead of rebuilt every frame, the nibble particle limit was lowered from 300 to 80, and settled compost fragments no longer trigger unnecessary rotation calculations. WIGGLERS_AUDIT.md was updated to mark two performance tasks as complete, log a new physics bug, and close a long-standing verification item about liquid saturation.

**What this touches:**
Drop physics — how liquid finds and routes through tunnels. Rendering — grass horizon, debris particles, and compost fragment drawing. Documentation — the audit log and session history.

**What could break:**
The tunnel drop scan is new logic. If drops stop attaching to tunnels or behave oddly after heavy digging, the Y-bucket index is the first place to check — specifically whether points are being inserted and cleaned up correctly when tunnels are pruned. The grass blade pre-render is built once at startup — if the horizon ever looks wrong after a screen resize, the blade canvas may need to be rebuilt on resize as well. Lowering the debris cap to 80 means heavy eating sessions will see fewer lingering nibble particles; this is intentional but worth watching if it feels visually sparse.

**Push recommendation:**
PUSH — all four changes are performance optimisations with no new gameplay logic, the build passed on every commit, and playtesting showed correct behaviour throughout.

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
HOLD — the build passed but the change is large and was not fully playtested. Recommend creating a new Reddit post and testing at minimum: normal play, death screen, drain cinematic, and flood event before pushing to production.

---

## After the Summary

Always offer:
1. **Calendar sync** — "Want me to sync the calendar? You cleared [N] tasks today."
2. **Doc updates** — "Should I update the architecture docs to reflect what shipped?"

Do not push these if the user just wants the summary and is clearly wrapping up. Read the room.
