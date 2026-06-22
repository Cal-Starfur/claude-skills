---
name: project-calendar
description: Maintains a live project calendar (tools/project-calendar.html) in the Cal-Starfur/claude-skills repo. Pulls open tasks from ALL registered repos, schedules them at max 1 task per repo per day so every project advances simultaneously. Load this skill whenever the user mentions the calendar, asks what's on the schedule, says "update the calendar", "sync the calendar", "what should I work on today", starts a new project repo, or finishes a session and wants to mark tasks done. Run a sync at the end of any session where new issues were opened or tasks were completed. IMPORTANT: Cal sometimes clears multiple days of work in a single high-energy session — always offer a sync after any productive session so the calendar repacks from today. IMPORTANT: Calendar is locked to claude-skills and Wigglers_Room only until Wigglers Room launches — do not register any other repo (including Space-Cats-Game-2026) without checking FOCUS.md first.
---

# Project Calendar Skill

Maintains `tools/project-calendar.html` in `Cal-Starfur/claude-skills`.
**Scheduling philosophy: 1 task per active repo per day. Every front advances. No burnout.**
**Calendar is always rolling from today — never fixed dates. Sync after every productive session.**
Never push a token to the repo. Always sanitize before commit.

---

## Scheduling Rules

| Rule | Detail |
|---|---|
| 1 per repo per day | Each active repo contributes exactly 1 task per day |
| Priority order | P1 → P2 → P3 within each repo |
| Sunday | Rest day — 0 tasks |
| Saturday | Skills/fixes only — no L-effort game tasks |
| L-effort cap | Max 2 L-effort tasks across all repos in one day |
| Burnout guard | If a day would have 4+ repos, cap at 4 and defer lowest-priority extras |
| Cadence | Every repo always has a task — no repo goes dark for more than 1 day |

**As new repos are added, the daily task count grows naturally — one slot per repo.**

---

## When to Run

| Trigger | Action |
|---|---|
| "update/sync the calendar" | Full sync — pull all repos, rebuild, push |
| "what should I work on today" | Full sync, highlight today's tasks |
| End of session where issues opened or closed | Full sync |
| End of any session where 2+ tasks were completed | Offer a sync — Cal may have cleared multiple days |
| New repo added | Check FOCUS.md first, then register and full sync |
| "add X to the calendar" | Add manual task, rebuild, push |

**After every productive session** — always ask:
> "Want me to sync the calendar? Looks like you cleared [N] tasks today."

---

## Repo Registry

Single source of truth is the `REGISTRY` list inside `pull_tasks.py`.
The list below is documentation — always edit the Python list.

**Current registry:**
```
Cal-Starfur/claude-skills  (skills)   → parser: parse_skills
Cal-Starfur/claude-skills  (audits)   → parser: parse_audits
Cal-Starfur/Wigglers_Room  (game)     → parser: parse_wigglers
```

**Inactive — add when project becomes active:**
```
Cal-Starfur/Space-Cats-Game-2026 → parser: parse_game_audit
```

Note: claude-skills has two lanes — `skills` (build/fix tasks) and `audits` (skill audit tasks).
These are separate repo entries so both always get a daily slot.

---

## Focus Constraint (Pre-Launch)

**Read FOCUS.md in the repo before registering any new repo.**

Current status: **Pre-launch** — Wigglers Room not yet live.

| Lane | Status |
|---|---|
| claude-skills (skills) | ✅ Active |
| claude-skills (audits) | ✅ Active |
| Wigglers_Room | ✅ Active |
| Space-Cats-Game-2026 | 🔒 Locked — post-launch only |
| Any new repo | 🔒 Locked — post-launch only |

**Hard rule:** Do not add any new repo to the REGISTRY until Wigglers Room is live on Reddit
with real players. If the user asks to add one, acknowledge their intent but remind them of
this constraint and confirm they want to override it deliberately.

**Launch gate** — when Wigglers Room goes live:
1. Update FOCUS.md status to "Post-launch"
2. Register Space-Cats-Game-2026 in REGISTRY
3. Full sync
4. New repos can be added one at a time from that point

---

## Cal's Work Style — The Over-Achiever Pattern

Cal is sometimes a high-energy worker. When fixes are falling into place and momentum
is good, a single session can clear what the calendar had scheduled across 2–4 days.

**This is expected and good. The calendar adapts to it.**

Rules for handling this:

1. **The calendar is always rolling from today** — it repacks all remaining open tasks
   starting from the current date every time a sync runs. There are no fixed dates,
   no "missed" days, no backlog shame. Only tasks done and tasks still to do.

2. **After any session where 2+ tasks were completed**, always prompt:
   > "You cleared [N] tasks today — want me to sync the calendar so it reflects where you are?"

3. **Never assume the current schedule is still valid** after a productive session.
   A sync takes 30 seconds and keeps the schedule motivating rather than stale.

4. **Slow days and fast days use the same system:**
   - Slow day → 1 task per lane, keep the cadence
   - Fast day → as many as fall into place, then sync
   - The calendar never penalises momentum or rewards slowing down

5. **If the user says they're on a roll**, do not interrupt to suggest stopping.
   Help them finish what's in front of them, then sync at the end.

---

## Step 0 — Bootstrap Scripts

Scripts live at `skills/project-calendar/scripts/` in `Cal-Starfur/claude-skills`.
Bootstrap fetches all three each session:

```bash
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path

TOKEN = sys.argv[1] if len(sys.argv) > 1 else input("Paste your GitHub PAT: ").strip()
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "ProjectCalendar/1.0"
}

base = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/project-calendar/scripts"
scripts = ["pull_tasks.py", "build_calendar.py", "push_calendar.py"]

Path("/tmp/project-calendar").mkdir(parents=True, exist_ok=True)
for script in scripts:
    url = f"{base}/{script}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        code = base64.b64decode(data["content"]).decode("utf-8")
    Path(f"/tmp/project-calendar/{script}").write_text(code)
    print(f"✓ {script} ({len(code.splitlines())} lines)")

print("Bootstrap complete.")
BOOTSTRAP
```
---

## Step 1 — Set Token (Every Session)

```bash
python3 -c "
from pathlib import Path; import json
token = input('Paste GitHub token: ').strip()
Path('/tmp/project-calendar').mkdir(parents=True, exist_ok=True)
Path('/tmp/project-calendar/config.json').write_text(json.dumps({'token': token}))
print('✓ Token set (session only)')
"
```

---

## Step 2 — Pull Tasks

```bash
python3 /tmp/project-calendar/pull_tasks.py
```

Each repo prints a status line. If any show ⚠ UNREACHABLE — stop. Do not push.

---

## Step 3 — Build Calendar

```bash
python3 /tmp/project-calendar/build_calendar.py
```

---

## Step 4 — Push

```bash
python3 /tmp/project-calendar/push_calendar.py
```

Pushes: `tools/project-calendar.html`, `tools/calendar-done.json`, `CHANGELOG.md`.
Token is sanitized before commit. Push is blocked if any repo was unreachable.

---

## Parsers

### parse_skills — skill build/fix tasks from claude-skills

Reads `planning/skill-buildout-plan.md` and `audits/*.md` Priority Fix Lists.
- Phase 1 skills → `P1`, Phase 2 skills → `P2`
- 🔴 audit fix → `P1`, 🟡 → `P2`, 🟢 → `P3`
- IDs namespaced: `skills:{id}`

### parse_audits — skill audit tasks from claude-skills

Reads `README.md` skill roster for skills needing audit/re-audit.
Generates one audit task per skill that hasn't been audited recently or scored below 80.
- Skills scored < 65 → `P1` audit task
- Skills scored 65–79 → `P2` audit task
- Skills scored 80+ with no recent audit → `P3` audit task
- IDs namespaced: `audits:audit-{skill-name}`

### parse_wigglers — game tasks from Wigglers_Room

Reads `WIGGLERS_AUDIT.md` Section 2 priority table.
- P1/next session/verify → `P1`, P2 → `P2`, Future/P3/Low → `P3`
- IDs namespaced: `wigglers:{id}`

### parse_game_audit — generic new game repo

Reads `GAME_AUDIT.md` or `WIGGLERS_AUDIT.md`. Falls back to GitHub Issues.
IDs namespaced: `{repo-slug}:{id}`

---

## Output Format

```
## Calendar synced

Repos:
  ✓ skills       — 6 build tasks, 5 fix tasks (11 total)
  ✓ audits       — 4 audit tasks
  ✓ Wigglers_Room — 18 game tasks
  Total: 33 tasks | 0 done | 11 P1 open

Today's schedule (3 tasks — 1 per repo):
  [SKILL P1] Build: session-summary skill
  [AUDIT P1] Audit: png-canvas-art-optimizer (score: 60)
  [GAME  P1] PERF-1: Trash chunks pre-render

Pushed: tools/project-calendar.html ✓
Pushed: tools/calendar-done.json ✓
Pushed: CHANGELOG.md ✓
```

---

## Hard Rules

1. Never push a token — sanitize every commit
2. Never push if any repo was unreachable
3. Never schedule more than 1 task per repo per day
4. Never skip done-state sync — completed work must not reappear
5. Always update CHANGELOG on every push
6. Namespace all task IDs by repo — never bare IDs
7. When a new repo is added, run a full sync same session
8. **Never add a new repo without checking FOCUS.md first**
9. **Always offer a sync after any session where 2+ tasks were completed**
10. **The calendar always repacks from today — never leave stale schedules in place**

---

## Adding a New Repo

1. Append to `REGISTRY` in `pull_tasks.py`
2. Write a parser (use `parse_wigglers` as template)
3. Register in `PARSERS` dict
4. Run full sync, confirm tasks appear
5. Push

---

