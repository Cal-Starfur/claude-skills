# Project Focus — Active Constraint

**Status:** Pre-launch · Wigglers Room not yet live

---

## Current Focus (until Wigglers Room launches)

**Active lanes on the calendar:**
- `claude-skills` — skills and audits lanes
- `Wigglers_Room` — game tasks lane

**Locked out until after launch:**
- `Space-Cats-Game-2026` — do not add to calendar
- Any new repos created during this period — do not add to calendar

---

## Why This Constraint Exists

Wigglers Room is the primary shipping goal. Skills work directly supports it.
Adding new projects before launch splits focus, slows the cadence, and risks
shipping nothing instead of something.

**The rule:** If it's not Wigglers Room or claude-skills, it waits.

---

## Cal's Work Style — The Over-Achiever Pattern

Cal sometimes has high-energy sessions where fixes fall into place easily and
multiple days worth of work gets done in a single sitting. This is normal and
should be celebrated, not penalized.

**How the calendar handles this:**

- The calendar is always a *rolling schedule from today forward* — never fixed dates
- After any session where multiple tasks were completed, run a full sync
- The sync will repack all remaining tasks from today, filling empty slots naturally
- There are no "missed days" — only tasks done and tasks still to do
- If 3 days of work gets done on Monday, Tuesday starts fresh with the next tasks

**For Claude — after any productive session:**
Always ask: "Want me to sync the calendar to reflect what we got done today?"
If the user closed out multiple tasks, sync before ending the session so the
schedule stays accurate and motivating rather than showing stale done tasks.

**The cadence holds regardless of pace:**
- Slow day → 1 task per lane, keep moving
- Fast day → as many as fall into place, then sync
- The calendar never punishes momentum

---

## Launch Gate

When Wigglers Room is live on Reddit with real players:
1. Update this file — change status to "Post-launch"
2. Register Space-Cats-Game-2026 in `pull_tasks.py` REGISTRY
3. Run a full calendar sync
4. New repos can be added one at a time from that point forward

---

## For Claude (every session)

Before adding any new repo to the calendar registry, check this file.
If status is "Pre-launch" — do not register the repo, regardless of what
the user asks in the moment. If the user wants to add a repo, remind them
of this constraint and ask if they want to override it intentionally.

After any session where tasks were completed — prompt for a calendar sync.
The schedule should always reflect current reality, not a plan made days ago.

*Set: 2026-06-19 | Owner: Cal-Starfur*
