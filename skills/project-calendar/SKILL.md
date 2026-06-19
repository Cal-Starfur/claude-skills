---
name: project-calendar
description: Maintains a live project calendar (tools/project-calendar.html) in the Cal-Starfur/claude-skills repo. Pulls open tasks from ALL registered repos, schedules them at max 2 per day by priority, and pushes the updated calendar to GitHub. Load this skill whenever the user mentions the calendar, asks what's on the schedule, says "update the calendar", starts a new project repo, or finishes a session and wants to mark tasks done. Also triggers automatically at the end of any game or skill session to sync completed work. Never let the calendar go stale — if a session changed something, update the calendar before closing.
---

# Project Calendar Skill

Maintains `tools/project-calendar.html` in `Cal-Starfur/claude-skills`.
Pulls tasks from all registered repos. Schedules at max 2/day. Pushes to GitHub.
**Never push a token to the repo. Always sanitize before commit.**

---

## When to Run

| Trigger | Action |
|---|---|
| "update the calendar" / "what's on the schedule" | Full sync — pull all repos, rebuild, push |
| End of any game or skill session | Mark completed tasks done, push |
| New repo added to the project | Register it, full sync |
| New issues/features opened in any repo | Pull and reschedule |
| "add X to the calendar" | Add manual task, rebuild, push |

---

## Repo Registry

Add new repos here as the project grows. Each entry needs:
- `owner/repo` — GitHub path
- `label` — display name
- `type` — `game` | `skill` | `tool`
- `parser` — which extraction function to use (see parsers below)

**Current registry:**
```
Cal-Starfur/claude-skills    → label: claude-skills    → parser: parse_skills
Cal-Starfur/Wigglers_Room    → label: Wigglers_Room    → parser: parse_wigglers
Cal-Starfur/Space-Cats-Game-2026 → label: Space-Cats → parser: parse_game_audit (when active)
```

To add a new repo: append to registry, write a parser for it, run full sync.

---

## Step 0 — Bootstrap Scripts

```bash
python3 << 'BOOTSTRAP'
import re
from pathlib import Path

skill_path = '/mnt/skills/user/project-calendar/SKILL.md'
content = Path(skill_path).read_text()
sections = re.findall(
    r'## EMBEDDED SCRIPT: (.+?)\n\*Write this to `(.+?)`\*\n\n```python\n(.*?)```',
    content, re.DOTALL
)
for name, target_path, code in sections:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code)
    print(f"✓ {target_path} ({len(code.splitlines())} lines)")
print("Bootstrap complete.")
BOOTSTRAP
```

---

## Step 1 — Set Token (Every Session)

```bash
python3 -c "
from pathlib import Path
import json
token = input('Paste GitHub token: ').strip()
Path('/tmp/project-calendar').mkdir(parents=True, exist_ok=True)
Path('/tmp/project-calendar/config.json').write_text(json.dumps({'token': token}))
print('✓ Token set (session only)')
"
```

Token lives in `/tmp` only. Never saved. Never committed.

---

## Step 2 — Pull Tasks From All Repos

```bash
python3 /tmp/project-calendar/pull_tasks.py
```

Outputs `/tmp/project-calendar/tasks.json` — list of task objects:
```json
{
  "id": "perf-1",
  "title": "PERF-1: Trash chunks pre-render",
  "type": "game",
  "priority": "P1",
  "effort": "S|M|L",
  "repo": "Wigglers_Room",
  "desc": "Plain English description",
  "source_file": "WIGGLERS_AUDIT.md",
  "done": false
}
```

---

## Step 3 — Build Calendar HTML

```bash
python3 /tmp/project-calendar/build_calendar.py
```

Outputs `/tmp/project-calendar/project-calendar.html`

**Scheduling rules (hard — never break these):**
- Max 2 tasks per day
- Sunday = rest day (0 tasks)
- Saturday = max 1 task, no L-effort tasks
- Sort order: P1 → P2 → P3, then skill > game > fix within same priority
- Spread L-effort tasks — never two L tasks in the same week
- If all P1s are done, pull P2s forward
- 4-week rolling window from today

---

## Step 4 — Sync Done State

Before rebuilding, read the current calendar from GitHub to extract which tasks
are marked done (stored in the HTML's localStorage seed or a companion `done.json`).
Merge with new task list so completed work doesn't reappear.

```bash
python3 /tmp/project-calendar/sync_done.py
```

Done state is stored in `tools/calendar-done.json` in the repo — a simple
`{"task-id": true}` map. This is the source of truth across devices.

---

## Step 5 — Push to GitHub

```bash
python3 /tmp/project-calendar/push_calendar.py
```

Pushes two files:
1. `tools/project-calendar.html` — sanitized (no token)
2. `tools/calendar-done.json` — done state

**Sanitization rule:** Replace any string matching `github_pat_[A-Za-z0-9_]+`
with `PASTE_YOUR_GITHUB_TOKEN_HERE` before committing. Hard rule, no exceptions.

---

## Parsers

### parse_skills — claude-skills repo

Reads from:
- `planning/skill-buildout-plan.md` → Phase 1 and Phase 2 skill build tasks
- `audits/*.md` → skill fix tasks from Priority Fix List sections
- Any `## GAPS` section in gap analysis files

Extraction rules:
- Phase 1 skill → `type: skill`, `priority: P1`
- Phase 2 skill → `type: skill`, `priority: P2`
- Audit fix marked 🔴 High → `type: fix`, `priority: P1`
- Audit fix marked 🟡 Med → `type: fix`, `priority: P2`
- Audit fix marked 🟢 Low → `type: fix`, `priority: P3`

Effort heuristic:
- "document X" / "fix copy-paste" / "remove hardcoded" → `S`
- "build X skill" / "clarify boundary" → `M`
- "rebuild X from scratch" → `L`

### parse_wigglers — Wigglers_Room repo

Reads from:
- `WIGGLERS_AUDIT.md` → Section 2 (Open Issues priority table)

Extraction rules:
- `P1 — next session` → `priority: P1`
- `P1 — verify` → `priority: P1`, effort: `S`
- `P2` → `priority: P2`
- `P3` / `Low` → `priority: P3`
- `Future` → `priority: P3`, effort: `L`

Effort heuristic from description:
- "verify", "check", "confirm" → `S`
- "offscreen pre-render", "index", single-function fix → `M`
- Multi-file feature, design doc required → `L`

### parse_game_audit — generic game repo parser

For any new game repo that follows the same WIGGLERS_AUDIT.md format.
Reads `{REPO_ROOT}/GAME_AUDIT.md` or `{REPO_ROOT}/WIGGLERS_AUDIT.md`.
Falls back to reading open GitHub Issues if no audit file found.

---

## Output Format (after every sync)

```
## Calendar synced

Repos pulled: claude-skills, Wigglers_Room
Tasks found: 23 total (8 done, 15 open)
P1 open: 5 | P2 open: 7 | P3 open: 3

Schedule preview (next 7 days):
  Fri Jun 20 → PERF-1 (game/P1/M), session-summary skill (skill/P1/M)
  Sat Jun 21 → ISS-13A verify (game/P1/S)
  Sun Jun 22 → rest
  Mon Jun 23 → PERF-2 (game/P1/M), preflight-checklist skill (skill/P1/M)
  Tue Jun 24 → rollback skill (skill/P2/M), fix: png-canvas (fix/P1/S)
  Wed Jun 25 → PERF-3 (game/P2/S), fix: save-skill-workflow (fix/P2/S)
  Thu Jun 26 → feature-spec skill (skill/P2/S), FEAT-2 (game/P2/L)

Pushed: tools/project-calendar.html ✓
Pushed: tools/calendar-done.json ✓
```

---

## Hard Rules

1. Never push a token to GitHub — sanitize before every commit
2. Never reschedule done tasks — preserve done state across rebuilds
3. Never exceed 2 tasks/day — the whole point is preventing overwhelm
4. Never skip the done-state sync — completed work must not reappear
5. Always update CHANGELOG.md when tasks are added or completed
6. When a new repo is registered, run a full sync same session
7. After any game or skill session ends, check if tasks were completed and sync

---

## Adding a New Repo

1. Add entry to Repo Registry (above)
2. Write a parser function in `pull_tasks.py` (follow existing parser pattern)
3. Register parser in the `PARSERS` dict in `pull_tasks.py`
4. Run full sync
5. Confirm new tasks appear in schedule preview
6. Push

---

## EMBEDDED SCRIPT: pull_tasks.py
*Write this to `/tmp/project-calendar/pull_tasks.py`*

```python
"""
pull_tasks.py — Pull tasks from all registered repos and write tasks.json
"""
import json, base64, re
from pathlib import Path
import urllib.request, urllib.error

config = json.loads(Path('/tmp/project-calendar/config.json').read_text())
TOKEN = config['token']
OUT = Path('/tmp/project-calendar')

REGISTRY = [
    {'owner': 'Cal-Starfur', 'repo': 'claude-skills',       'parser': 'parse_skills'},
    {'owner': 'Cal-Starfur', 'repo': 'Wigglers_Room',       'parser': 'parse_wigglers'},
]

def gh_get(path):
    url = f'https://api.github.com/repos/{path}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def gh_file(owner, repo, file_path):
    data = gh_get(f'{owner}/{repo}/contents/{file_path}')
    return base64.b64decode(data['content'].replace('\n', '')).decode('utf-8', errors='replace')

def effort_from_desc(desc, title=''):
    combined = (title + ' ' + desc).lower()
    if any(w in combined for w in ['verify', 'check', 'confirm', 'remove hardcoded', 'copy-paste', 'fix copy', 'plaintext']):
        return 'S'
    if any(w in combined for w in ['cross-player', 'cross-device', 'long-press', 'design doc', 'multi-file', 'from scratch']):
        return 'L'
    return 'M'

# ── Parser: claude-skills ──────────────────────────────────────────────────
def parse_skills(owner, repo):
    tasks = []
    print(f'  Parsing {owner}/{repo}...')

    # Buildout plan
    try:
        plan = gh_file(owner, repo, 'planning/skill-buildout-plan.md')
        phase = None
        for line in plan.splitlines():
            if 'Phase 1' in line: phase = 'P1'
            elif 'Phase 2' in line: phase = 'P2'
            m = re.match(r'###\s+\d+\.\s+(.+?)\s+skill', line, re.I)
            if m and phase:
                name = m.group(1).strip().lower().replace(' ', '-')
                title = f'Build: {m.group(1).strip().lower()} skill'
                tasks.append({
                    'id': f'skill-{name}',
                    'title': title,
                    'type': 'skill',
                    'priority': phase,
                    'effort': 'M',
                    'repo': repo,
                    'desc': f'Phase {phase[-1]} skill from buildout plan.',
                    'done': False
                })
    except Exception as e:
        print(f'    Warning: could not read buildout plan: {e}')

    # Audit fix lists
    try:
        tree = gh_get(f'{owner}/{repo}/git/trees/main?recursive=1')
        audit_files = [i['path'] for i in tree['tree'] if i['path'].startswith('audits/') and i['path'].endswith('.md')]
        for af in audit_files:
            try:
                content = gh_file(owner, repo, af)
                in_priority = False
                for line in content.splitlines():
                    if 'Priority Fix List' in line or '## Priority' in line:
                        in_priority = True
                    if in_priority and line.startswith('|') and '|' in line[1:]:
                        parts = [p.strip() for p in line.split('|') if p.strip()]
                        if len(parts) >= 3 and parts[0] not in ('Priority', '---', 'Skill', 'priority'):
                            pri_raw = parts[0]
                            skill_name = parts[1] if len(parts) > 1 else ''
                            fix_desc = parts[2] if len(parts) > 2 else ''
                            if '🔴' in pri_raw or 'High' in pri_raw: pri = 'P1'
                            elif '🟡' in pri_raw or 'Med' in pri_raw: pri = 'P2'
                            else: pri = 'P3'
                            task_id = f'fix-{skill_name.lower().replace(" ", "-").replace("/", "-")[:30]}'
                            if skill_name and skill_name.lower() not in ('skill', 'priority', '---'):
                                tasks.append({
                                    'id': task_id,
                                    'title': f'Fix: {skill_name}',
                                    'type': 'fix',
                                    'priority': pri,
                                    'effort': effort_from_desc(fix_desc),
                                    'repo': repo,
                                    'desc': fix_desc,
                                    'done': False
                                })
            except Exception as e:
                print(f'    Warning: {af}: {e}')
    except Exception as e:
        print(f'    Warning: could not read audit files: {e}')

    # Deduplicate by id
    seen = set()
    deduped = []
    for t in tasks:
        if t['id'] not in seen:
            seen.add(t['id'])
            deduped.append(t)
    print(f'    → {len(deduped)} tasks')
    return deduped

# ── Parser: Wigglers_Room ──────────────────────────────────────────────────
def parse_wigglers(owner, repo):
    tasks = []
    print(f'  Parsing {owner}/{repo}...')
    try:
        audit = gh_file(owner, repo, 'WIGGLERS_AUDIT.md')
        in_table = False
        for line in audit.splitlines():
            if '| ID' in line and 'Priority' in line:
                in_table = True
                continue
            if in_table and line.startswith('|---'):
                continue
            if in_table and line.startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) < 3: continue
                task_id_raw = parts[0]
                pri_raw = parts[1] if len(parts) > 1 else ''
                desc = parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else '')
                task_id = task_id_raw.lower().replace(' ', '-')
                if not task_id or task_id == 'id': continue

                if 'P1' in pri_raw or 'next session' in pri_raw or 'verify' in pri_raw.lower():
                    pri = 'P1'
                elif 'P2' in pri_raw:
                    pri = 'P2'
                elif 'Future' in pri_raw or 'future' in pri_raw:
                    pri = 'P3'
                else:
                    pri = 'P3'

                task_type = 'game'
                if task_id_raw.startswith('FEAT'): task_type = 'game'
                elif task_id_raw.startswith('PERF'): task_type = 'game'

                tasks.append({
                    'id': task_id,
                    'title': f'{task_id_raw}: {desc[:60]}',
                    'type': task_type,
                    'priority': pri,
                    'effort': effort_from_desc(desc, task_id_raw),
                    'repo': repo,
                    'desc': desc,
                    'done': False
                })
            elif in_table and not line.startswith('|'):
                in_table = False
    except Exception as e:
        print(f'    Error: {e}')
    print(f'    → {len(tasks)} tasks')
    return tasks

# ── Main ───────────────────────────────────────────────────────────────────
PARSERS = {
    'parse_skills':   parse_skills,
    'parse_wigglers': parse_wigglers,
}

all_tasks = []
for entry in REGISTRY:
    try:
        fn = PARSERS.get(entry['parser'])
        if fn:
            tasks = fn(entry['owner'], entry['repo'])
            all_tasks.extend(tasks)
    except Exception as e:
        print(f'  ERROR {entry["repo"]}: {e}')

# Load done state from repo if available
done_state = {}
try:
    done_data = gh_file('Cal-Starfur', 'claude-skills', 'tools/calendar-done.json')
    done_state = json.loads(done_data)
    print(f'\nLoaded done state: {sum(done_state.values())} tasks marked done')
except Exception:
    print('\nNo existing done state found — starting fresh')

# Apply done state
for t in all_tasks:
    t['done'] = bool(done_state.get(t['id'], False))

(OUT / 'tasks.json').write_text(json.dumps(all_tasks, indent=2))
print(f'\n✓ {len(all_tasks)} tasks written to tasks.json')
print(f'  Done: {sum(1 for t in all_tasks if t["done"])} | Open: {sum(1 for t in all_tasks if not t["done"])}')
```

## EMBEDDED SCRIPT: build_calendar.py
*Write this to `/tmp/project-calendar/build_calendar.py`*

```python
"""
build_calendar.py — Build the calendar HTML from tasks.json
"""
import json
from pathlib import Path
from datetime import date, timedelta

OUT = Path('/tmp/project-calendar')
tasks = json.loads((OUT / 'tasks.json').read_text())
TODAY = date.today()

# ── Scheduling ────────────────────────────────────────────────────────────
PRIORITY_ORDER = {'P1': 0, 'P2': 1, 'P3': 2}
TYPE_ORDER = {'skill': 0, 'game': 1, 'fix': 2}

open_tasks = [t for t in tasks if not t['done']]
open_tasks.sort(key=lambda t: (
    PRIORITY_ORDER.get(t['priority'], 9),
    TYPE_ORDER.get(t['type'], 9)
))

schedule = []
task_idx = 0
for i in range(28):
    d = TODAY + timedelta(days=i)
    dow = d.weekday()  # 0=Mon, 6=Sun
    is_rest = (dow == 6)
    is_light = (dow == 5)
    is_today = (i == 0)
    max_tasks = 0 if is_rest else (1 if (is_light or is_today) else 2)

    day_tasks = []
    j = task_idx
    added = 0
    while added < max_tasks and j < len(open_tasks):
        t = open_tasks[j]
        if is_light and t['effort'] == 'L':
            j += 1
            continue
        day_tasks.append(t)
        j += 1
        added += 1
    task_idx = j
    schedule.append({'date': d.isoformat(), 'tasks': day_tasks, 'is_today': is_today, 'is_rest': is_rest})

done_tasks = [t for t in tasks if t['done']]

# ── HTML ──────────────────────────────────────────────────────────────────
DAY_NAMES = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f'{MONTH_NAMES[d.month-1]} {d.day}'

def fmt_day(iso):
    d = date.fromisoformat(iso)
    return DAY_NAMES[d.weekday()]

def task_html(t):
    type_color = {'game': '#4ade80', 'skill': '#818cf8', 'fix': '#fb923c'}.get(t['type'], '#888')
    pri_color = {'P1': '#f87171', 'P2': '#fbbf24', 'P3': '#6b6880'}.get(t['priority'], '#888')
    return f'''<div class="task {t["type"]}" id="t-{t["id"]}">
      <div class="task-top">
        <div class="task-title">{t["title"]}</div>
        <div class="task-badges">
          <span class="badge {t["type"]}">{t["type"].upper()}</span>
          <span class="badge {t["priority"]}">{t["priority"]}</span>
          <span class="badge effort-{t["effort"]}">{t["effort"]}</span>
        </div>
      </div>
      <div class="task-desc">{t["desc"]}</div>
      <div class="task-repo">📁 {t["repo"]}</div>
      <button class="check-btn" onclick="toggleDone('{t["id"]}',event)" title="Mark done">✓</button>
    </div>'''

weeks_html = ''
for wi in range(0, 28, 7):
    week = schedule[wi:wi+7]
    if not week: continue
    week_labels = ['This week', 'Next week', 'Week 3', 'Week 4']
    label = week_labels[wi // 7] if wi // 7 < 4 else f'Week {wi // 7 + 1}'
    start_fmt = fmt_date(week[0]['date'])
    end_fmt = fmt_date(week[-1]['date'])
    days_html = ''
    for day in week:
        classes = 'day-card'
        if day['is_today']: classes += ' today'
        if day['is_rest']: classes += ' rest'
        today_badge = '<span class="today-badge">today</span>' if day['is_today'] else ''
        if day['is_rest']:
            body = '<div class="rest-label">Rest day 🌱</div>'
        elif not day['tasks']:
            body = '<div class="empty-day">All caught up ✓</div>'
        else:
            body = '<div class="tasks">' + ''.join(task_html(t) for t in day['tasks']) + '</div>'
        days_html += f'''<div class="{classes}">
        <div class="day-header">
          <span class="day-name">{fmt_day(day["date"])}{today_badge}</span>
          <span class="day-date">{fmt_date(day["date"])}</span>
        </div>
        {body}
      </div>'''
    weeks_html += f'''<div class="week-section">
    <div class="week-label">{label} · {start_fmt} – {end_fmt}</div>
    <div class="days-grid">{days_html}</div>
  </div>'''

total = len(tasks)
done_count = len(done_tasks)
p1_open = sum(1 for t in open_tasks if t['priority'] == 'P1')
skill_left = sum(1 for t in open_tasks if t['type'] in ('skill', 'fix'))
built_date = TODAY.isoformat()

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cal's Dev Calendar</title>
<style>
:root{{--bg:#0f0f11;--surface:#1a1a1f;--surface2:#222228;--border:#2e2e38;--text:#e8e6f0;--muted:#6b6880;--game:#4ade80;--game-bg:#052010;--game-border:#1a4d2a;--skill:#818cf8;--skill-bg:#0d0d2a;--skill-border:#1e1e4a;--fix:#fb923c;--fix-bg:#1a0d00;--fix-border:#3d2000;--p1:#f87171;--p2:#fbbf24;--p3:#6b6880;--done:#22c55e;--font:'SF Mono','Fira Code',monospace;--sans:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);min-height:100vh;padding:24px 16px 48px}}
header{{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:28px;flex-wrap:wrap;gap:12px}}
.header-left h1{{font-size:22px;font-weight:600;letter-spacing:-0.5px}}
.header-left p{{font-size:13px;color:var(--muted);margin-top:4px}}
.sync-info{{font-size:11px;font-family:var(--font);color:var(--muted);margin-bottom:20px}}
.stats-row{{display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 20px;text-align:center}}
.stat-num{{font-size:24px;font-weight:700;font-family:var(--font);display:block}}
.stat-label{{font-size:11px;color:var(--muted);margin-top:2px;display:block}}
.legend{{display:flex;gap:16px;margin-bottom:24px;flex-wrap:wrap}}
.legend-item{{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted)}}
.legend-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0}}
.weeks{{display:flex;flex-direction:column;gap:32px}}
.week-section{{}}
.week-label{{font-size:11px;font-family:var(--font);color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px}}
.days-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
.day-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px;min-height:100px}}
.day-card.today{{border-color:var(--skill);box-shadow:0 0 0 1px var(--skill) inset}}
.day-card.rest{{opacity:.5}}
.day-header{{display:flex;align-items:baseline;justify-content:space-between;margin-bottom:12px}}
.day-name{{font-size:13px;font-weight:600}}
.day-date{{font-size:11px;font-family:var(--font);color:var(--muted)}}
.today-badge{{font-size:10px;background:var(--skill);color:#fff;padding:2px 7px;border-radius:20px;font-weight:600;margin-left:8px}}
.rest-label{{font-size:12px;color:var(--muted);font-style:italic}}
.tasks{{display:flex;flex-direction:column;gap:8px}}
.task{{border-radius:8px;padding:10px 12px;position:relative;transition:opacity .15s}}
.task.game{{background:var(--game-bg);border:1px solid var(--game-border)}}
.task.skill{{background:var(--skill-bg);border:1px solid var(--skill-border)}}
.task.fix{{background:var(--fix-bg);border:1px solid var(--fix-border)}}
.task.done{{opacity:.4}}
.task.done .task-title{{text-decoration:line-through}}
.task-top{{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:4px}}
.task-title{{font-size:13px;font-weight:500;flex:1;line-height:1.3;padding-right:24px}}
.task-badges{{display:flex;gap:4px;flex-shrink:0;align-items:center}}
.badge{{font-size:10px;font-family:var(--font);padding:2px 6px;border-radius:4px;font-weight:600;white-space:nowrap}}
.badge.game{{background:#052010;color:var(--game);border:1px solid var(--game-border)}}
.badge.skill{{background:#0d0d2a;color:var(--skill);border:1px solid var(--skill-border)}}
.badge.fix{{background:#1a0d00;color:var(--fix);border:1px solid var(--fix-border)}}
.badge.P1{{background:#2a0505;color:var(--p1);border:1px solid #4d0f0f}}
.badge.P2{{background:#1a1000;color:var(--p2);border:1px solid #3d2800}}
.badge.P3{{background:#1a1a1f;color:var(--muted);border:1px solid var(--border)}}
.badge.effort-S{{background:#051a05;color:#4ade80;border:1px solid #1a4d1a}}
.badge.effort-M{{background:#1a1000;color:#fbbf24;border:1px solid #3d2800}}
.badge.effort-L{{background:#2a0505;color:#f87171;border:1px solid #4d0f0f}}
.task-desc{{font-size:11px;color:var(--muted);line-height:1.5}}
.task-repo{{font-size:10px;font-family:var(--font);color:var(--muted);margin-top:5px;opacity:.7}}
.check-btn{{position:absolute;top:10px;right:10px;width:18px;height:18px;border-radius:50%;border:1.5px solid var(--border);background:transparent;cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:10px;color:transparent;transition:all .15s}}
.check-btn:hover{{border-color:var(--done);color:var(--done)}}
.task.done .check-btn{{border-color:var(--done);background:var(--done);color:#fff}}
.empty-day{{font-size:12px;color:var(--muted);font-style:italic}}
@media(max-width:600px){{.days-grid{{grid-template-columns:1fr}}.stats-row{{gap:10px}}.stat{{min-width:80px;padding:10px 14px}}}}
</style>
</head>
<body>
<header>
  <div class="header-left">
    <h1>🪱 Dev Calendar</h1>
    <p>Max 2 tasks/day · pulled from GitHub · don't get overwhelmed</p>
  </div>
</header>
<div class="sync-info">Last built: {built_date} · {total} tasks total · Ask Claude to sync when repos update</div>
<div class="stats-row">
  <div class="stat"><span class="stat-num">{total}</span><span class="stat-label">total tasks</span></div>
  <div class="stat"><span class="stat-num" style="color:var(--done)">{done_count}</span><span class="stat-label">done</span></div>
  <div class="stat"><span class="stat-num" style="color:var(--p1)">{p1_open}</span><span class="stat-label">P1 open</span></div>
  <div class="stat"><span class="stat-num" style="color:var(--skill)">{skill_left}</span><span class="stat-label">skills left</span></div>
</div>
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:var(--game)"></div>Game task</div>
  <div class="legend-item"><div class="legend-dot" style="background:var(--skill)"></div>Skill build</div>
  <div class="legend-item"><div class="legend-dot" style="background:var(--fix)"></div>Skill fix</div>
  <div class="legend-item"><div class="legend-dot" style="background:var(--p1)"></div>P1 urgent</div>
  <div class="legend-item"><div class="legend-dot" style="background:var(--p2)"></div>P2 soon</div>
  <div class="legend-item">S=small · M=medium · L=large effort</div>
</div>
<div class="weeks">{weeks_html}</div>
<script>
const DONE_KEY='cal_done_v2';
function getDone(){{try{{return JSON.parse(localStorage.getItem(DONE_KEY)||'{{}}')}}catch{{return {{}}}}}}
function toggleDone(id,e){{
  e.stopPropagation();
  const d=getDone();d[id]=!d[id];
  localStorage.setItem(DONE_KEY,JSON.stringify(d));
  const el=document.getElementById('t-'+id);
  if(el)el.classList.toggle('done',!!d[id]);
}}
(function applyDone(){{
  const d=getDone();
  Object.entries(d).forEach(([id,v])=>{{
    if(v){{const el=document.getElementById('t-'+id);if(el)el.classList.add('done');}}
  }});
}})();
</script>
</body>
</html>'''

(OUT / 'project-calendar.html').write_text(html)
print(f'✓ Calendar built: {len(schedule)} days scheduled')
print(f'  Open tasks scheduled: {sum(len(d["tasks"]) for d in schedule)}')
```

## EMBEDDED SCRIPT: push_calendar.py
*Write this to `/tmp/project-calendar/push_calendar.py`*

```python
"""
push_calendar.py — Push calendar HTML and done state to claude-skills repo
"""
import json, base64, re
from pathlib import Path
import urllib.request

config = json.loads(Path('/tmp/project-calendar/config.json').read_text())
TOKEN = config['token']
OWNER = 'Cal-Starfur'
REPO = 'claude-skills'
HEADERS = {'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github.v3+json'}

def gh_get(path):
    url = f'https://api.github.com/repos/{path}'
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def gh_put(path, payload):
    url = f'https://api.github.com/repos/{path}'
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=HEADERS, method='PUT')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def sanitize(content):
    return re.sub(r'github_pat_[A-Za-z0-9_]+', 'PASTE_YOUR_GITHUB_TOKEN_HERE', content)

def push_file(file_path, content, message):
    existing, status = gh_get(f'{OWNER}/{REPO}/contents/{file_path}')
    sha = existing.get('sha') if status == 200 else None
    safe_content = sanitize(content) if file_path.endswith('.html') else content
    payload = {'message': message, 'content': base64.b64encode(safe_content.encode()).decode()}
    if sha: payload['sha'] = sha
    result, code = gh_put(f'{OWNER}/{REPO}/contents/{file_path}', payload)
    if code in (200, 201):
        print(f'✓ {file_path}')
    else:
        print(f'✗ {file_path} — {code}: {result.get("message")}')

OUT = Path('/tmp/project-calendar')

# Push calendar HTML
html = (OUT / 'project-calendar.html').read_text()
push_file('tools/project-calendar.html', html, 'Calendar sync: updated schedule from all repos')

# Push done state
tasks = json.loads((OUT / 'tasks.json').read_text())
done_state = {t['id']: t['done'] for t in tasks if t['done']}
push_file('tools/calendar-done.json', json.dumps(done_state, indent=2), 'Calendar sync: update done state')

print('\n✓ Calendar pushed to github.com/Cal-Starfur/claude-skills/tools/')
```
