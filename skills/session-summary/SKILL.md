---
name: session-summary
description: Generate a plain-English session summary when the user asks or signals session end. Tells the owner what changed, what it touched, what could break, and gives a PUSH or HOLD recommendation. Triggers on: "what changed", "give me the summary", "should I push", "wrap up", "end of session", "I'm done", "that's it for today", "ok thanks", "good session". Offer it after the last push of a code session — but do not force it for design or doc-only sessions unless asked.
---

# Session Summary Skill

**One job: tell the owner what happened in plain English.**
No code. No jargon. Every file named. Every risk flagged. End with a clear push recommendation.

**Offer after code sessions** — after the last commit, ask if the user wants a summary. Skip the offer for design or doc-only sessions unless they ask.

---

## When to Run

| Trigger | Action |
|---|---|
| "what changed this session" | Full summary |
| "give me the summary" | Full summary |
| "should I push" | Full summary + push recommendation |
| "wrap up" / "end of session" | Full summary + calendar sync offer |
| "I'm done" / "that's it" / "ok thanks" / "good session" | Offer the summary, then generate if user agrees |
| After any code session with 3+ commits | Offer after last push (code sessions only) |
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
   - If user says yes → load the `project-calendar` skill and run a full sync

2. **Doc updates** — "Should I update the architecture docs or audit log to reflect what shipped?"
   - Offer this if any game files changed
   - If user says yes → load the `github-sync` skill and update GAME_ARCHITECTURE.md or WIGGLERS_AUDIT.md as needed

Both offers are **mandatory** — make them in the same message as the summary. The user should never have to remember to ask.

3. **Skill audit** — "A skill was loaded or modified this session — want me to re-score it while we're here?"
   - Offer this only if: a skill was explicitly improved or created this session, OR any skill's score was noted as below 75
   - If user says yes → load the `skill-audit` skill and run a deep audit on the modified skill

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

## Example — HOLD Summary (Build Failure)

**SESSION SUMMARY — 2026-06-20 | Devvit 0.0.183**

**What changed:**
game.js was updated to split the main draw function into smaller sub-functions. The change touched around 400 lines across the rendering path. The build failed on the first attempt (TypeScript type error in the draw loop refactor) and was not resolved before the session ended.

**What this touches:**
Rendering — the entire draw loop and how each layer is called.

**What could break:**
The draw loop split is a large structural change. Any call order mistake between sub-functions could cause layers to render in the wrong order. The TypeScript build is currently failing — the game cannot be deployed in this state.

**Push recommendation:**
HOLD — build is failing. Do not push until the TypeScript error in the draw loop refactor is resolved and a clean build is confirmed.

---

Should I update the architecture docs to reflect the draw function restructure once the build is fixed?

---

## Edge Cases

### Long Conversation — Can't Reliably Identify All Commits

If the conversation is very long (200+ messages, or multiple hours of work) and commit history in the chat is fragmented or hard to follow:

1. **Do not guess.** A summary with a missing commit is worse than a summary that flags uncertainty.
2. Scan for all `propose_commit.py push` output blocks in the conversation — each one has a confirmed SHA and message. List only those.
3. If you find gaps (e.g. session started mid-conversation, or early messages are cut off), say explicitly:
   > "I can see [N] confirmed commits this session: [list]. There may be earlier commits I can't see — want to check GitHub history to confirm the full list?"
4. Offer to run `sync_from_github.py history` to pull the actual commit log and cross-reference:
   ```bash
   python3 /tmp/github-sync/scripts/sync_from_github.py history
   ```
5. Never present a partial commit list as if it were complete. Always flag when you're uncertain.

---

### Multi-File Sessions (10+ Files Changed)

When 10 or more files were modified in a session, a flat list becomes hard to read. Group by system instead:

**What changed (grouped):**
- **Game logic (3 files):** game.js, main.tsx, devvit.yaml — [what changed across these]
- **Skills (6 files):** session-health, github-sync, session-summary, lead-dev, contractor, devvit-pipeline — [what changed]
- **Documentation (2 files):** GAME_ARCHITECTURE.md, WIGGLERS_AUDIT.md — [what changed]

Rules for grouping:
- Game files (game.js, main.tsx, webroot/, src/) → "Game logic"
- Skill files (skills/*/SKILL.md) → "Skills"
- Docs (*.md, planning/) → "Documentation"
- Scripts (scripts/, tools/) → "Scripts/tooling"
- Config (devvit.yaml, package.json, .github/) → "Config"

Still name every file within each group. Grouping is for readability — nothing gets omitted.

The push recommendation still applies to the session as a whole. If any single file warrants a HOLD, the whole session is HOLD.

