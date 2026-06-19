---
name: project-calendar
description: Maintains a live project calendar (tools/project-calendar.html) in the Cal-Starfur/claude-skills repo. Pulls open tasks from ALL registered repos, schedules them at max 1 task per repo per day so every project advances simultaneously. Load this skill whenever the user mentions the calendar, asks what's on the schedule, says "update the calendar", "sync the calendar", "what should I work on today", starts a new project repo, or finishes a session and wants to mark tasks done. Run a sync at the end of any session where new issues were opened or tasks were completed.
---

# Project Calendar Skill

Maintains `tools/project-calendar.html` in `Cal-Starfur/claude-skills`.
**Scheduling philosophy: 1 task per active repo per day. Every front advances. No burnout.**
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
| New repo added | Register it, full sync |
| "add X to the calendar" | Add manual task, rebuild, push |

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
Path('/tmp/project-calendar').mkdir(parents=True, exist_ok=True)
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

---

## Adding a New Repo

1. Append to `REGISTRY` in `pull_tasks.py`
2. Write a parser (use `parse_wigglers` as template)
3. Register in `PARSERS` dict
4. Run full sync, confirm tasks appear
5. Push

---

## EMBEDDED SCRIPT: pull_tasks.py
*Write this to `/tmp/project-calendar/pull_tasks.py`*

```python
"""
pull_tasks.py v3 — per-repo lanes, audit tasks, namespaced IDs, network fallback
"""
import json, base64, re
from pathlib import Path
import urllib.request, urllib.error

config = json.loads(Path('/tmp/project-calendar/config.json').read_text())
TOKEN = config['token']
OUT = Path('/tmp/project-calendar')

# ── Single source of truth for repo registry ───────────────────────────────
# Each entry: owner, repo, parser, ns (namespace), lane (display label)
REGISTRY = [
    {'owner': 'Cal-Starfur', 'repo': 'claude-skills',   'parser': 'parse_skills',   'ns': 'skills',   'lane': 'Skills'},
    {'owner': 'Cal-Starfur', 'repo': 'claude-skills',   'parser': 'parse_audits',   'ns': 'audits',   'lane': 'Audits'},
    {'owner': 'Cal-Starfur', 'repo': 'Wigglers_Room',   'parser': 'parse_wigglers', 'ns': 'wigglers', 'lane': 'Wigglers Room'},
]

def gh_get(path):
    url = f'https://api.github.com/repos/{path}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def gh_file(owner, repo, file_path):
    data = gh_get(f'{owner}/{repo}/contents/{file_path}')
    return base64.b64decode(data['content'].replace('\n', '')).decode('utf-8', errors='replace')

def effort_from_desc(desc, title=''):
    combined = (title + ' ' + desc).lower()
    if any(w in combined for w in ['verify', 'check', 'confirm', 'remove hardcoded', 'copy-paste', 'plaintext']):
        return 'S'
    if any(w in combined for w in ['cross-player', 'cross-device', 'long-press', 'design doc', 'multi-file', 'from scratch']):
        return 'L'
    return 'M'

def ns_id(namespace, raw_id):
    return f'{namespace}:{raw_id}'

# ── Parser: skill build/fix tasks ─────────────────────────────────────────
def parse_skills(owner, repo, ns):
    tasks = []
    print(f'  [{ns}] Parsing skill build/fix tasks...')

    try:
        plan = gh_file(owner, repo, 'planning/skill-buildout-plan.md')
        phase = None
        in_phase2 = False
        for line in plan.splitlines():
            if re.match(r'^##\s+Phase 2', line):
                in_phase2 = True
                phase = 'P2'
            elif re.match(r'^##\s+Phase 1', line):
                in_phase2 = False
                phase = 'P1'
            elif not in_phase2 and re.search(r'Phase 1', line) and phase is None:
                phase = 'P1'
            m = re.match(r'###\s+\d+\.\s+(.+?)\s+skill', line, re.I)
            if m and phase:
                name = m.group(1).strip().lower().replace(' ', '-')
                tasks.append({
                    'id': ns_id(ns, f'skill-{name}'),
                    'title': f'Build: {m.group(1).strip().lower()} skill',
                    'type': 'skill', 'priority': phase, 'effort': 'M',
                    'repo': repo, 'lane': 'Skills',
                    'desc': f'Phase {phase[-1]} skill from buildout plan.',
                    'done': False
                })
    except Exception as e:
        print(f'    Warning: buildout plan: {e}')

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
                        if len(parts) >= 3 and parts[0] not in ('Priority', '---', 'Skill', 'priority', 'Fix'):
                            pri_raw, skill_name = parts[0], (parts[1] if len(parts) > 1 else '')
                            fix_desc = parts[2] if len(parts) > 2 else ''
                            if '🔴' in pri_raw or 'High' in pri_raw: pri = 'P1'
                            elif '🟡' in pri_raw or 'Med' in pri_raw: pri = 'P2'
                            else: pri = 'P3'
                            raw_id = f'fix-{skill_name.lower().replace(" ", "-").replace("/", "-")[:30]}'
                            if skill_name and skill_name.lower() not in ('skill', 'priority', '---', 'fix'):
                                tasks.append({
                                    'id': ns_id(ns, raw_id),
                                    'title': f'Fix: {skill_name}',
                                    'type': 'fix', 'priority': pri,
                                    'effort': effort_from_desc(fix_desc),
                                    'repo': repo, 'lane': 'Skills',
                                    'desc': fix_desc, 'done': False
                                })
            except Exception as e:
                print(f'    Warning {af}: {e}')
    except Exception as e:
        print(f'    Warning audit files: {e}')

    seen = set()
    deduped = [t for t in tasks if not (t['id'] in seen or seen.add(t['id']))]
    print(f'    → {len(deduped)} tasks')
    return deduped

# ── Parser: skill audit tasks ──────────────────────────────────────────────
def parse_audits(owner, repo, ns):
    tasks = []
    print(f'  [{ns}] Parsing skill audit tasks...')

    # Known skill scores from baseline + subsequent audits
    # Format: skill_name → (score, last_audited)
    SKILL_SCORES = {
        'session-health':           (97, '2026-06-19'),
        'devvit-pipeline':          (92, '2026-06-19'),
        'github-sync':              (88, '2026-06-19'),
        'lead-dev':                 (85, '2026-06-19'),
        'contractor':               (82, '2026-06-19'),
        'project-calendar':         (69, '2026-06-19'),
        'wigglers-architecture':    (72, '2026-06-19'),
        'save-skill-workflow':      (72, '2026-06-19'),
        'canvas-art-optimizer':     (68, '2026-06-19'),
        'png-canvas-art-optimizer': (60, '2026-06-19'),
        'skill-audit':              (None, None),
        'skill-creator':            (None, None),
    }

    # Try to read README for current skill roster
    try:
        readme = gh_file(owner, repo, 'README.md')
        # Parse skill table rows: | skill-name | score | role |
        for line in readme.splitlines():
            if line.startswith('|') and '|' in line[1:]:
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:
                    name = parts[0].lower().replace(' ', '-')
                    score_str = parts[1] if len(parts) > 1 else ''
                    try:
                        score = int(score_str)
                        if name in SKILL_SCORES:
                            existing = SKILL_SCORES[name]
                            SKILL_SCORES[name] = (score, existing[1])
                    except ValueError:
                        pass
    except Exception as e:
        print(f'    Warning: README: {e}')

    for skill_name, (score, last_audited) in SKILL_SCORES.items():
        if score is None:
            pri = 'P2'
            desc = f'Never audited — run baseline audit to get a score.'
        elif score < 65:
            pri = 'P1'
            desc = f'Score {score}/100 — below 65, needs urgent attention.'
        elif score < 80:
            pri = 'P2'
            desc = f'Score {score}/100 — room for improvement, target 85+.'
        else:
            pri = 'P3'
            desc = f'Score {score}/100 — healthy, re-audit after major changes.'

        tasks.append({
            'id': ns_id(ns, f'audit-{skill_name}'),
            'title': f'Audit: {skill_name}' + (f' (score: {score})' if score else ' (unscored)'),
            'type': 'audit',
            'priority': pri,
            'effort': 'S',
            'repo': repo,
            'lane': 'Audits',
            'desc': desc,
            'done': False
        })

    print(f'    → {len(tasks)} audit tasks')
    return tasks

# ── Parser: Wigglers_Room ──────────────────────────────────────────────────
def parse_wigglers(owner, repo, ns):
    tasks = []
    print(f'  [{ns}] Parsing game tasks...')
    try:
        audit = gh_file(owner, repo, 'WIGGLERS_AUDIT.md')
        in_table = False
        for line in audit.splitlines():
            if '| ID' in line and 'Priority' in line:
                in_table = True; continue
            if in_table and line.startswith('|---'): continue
            if in_table and line.startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) < 3: continue
                task_id_raw = parts[0]
                pri_raw = parts[1] if len(parts) > 1 else ''
                desc = parts[3] if len(parts) > 3 else (parts[2] if len(parts) > 2 else '')
                raw_id = task_id_raw.lower().replace(' ', '-')
                if not raw_id or raw_id == 'id': continue
                if 'P1' in pri_raw or 'next session' in pri_raw or 'verify' in pri_raw.lower(): pri = 'P1'
                elif 'P2' in pri_raw: pri = 'P2'
                else: pri = 'P3'
                tasks.append({
                    'id': ns_id(ns, raw_id),
                    'title': f'{task_id_raw}: {desc[:55]}',
                    'type': 'game', 'priority': pri,
                    'effort': effort_from_desc(desc, task_id_raw),
                    'repo': repo, 'lane': 'Wigglers Room',
                    'desc': desc, 'done': False
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
    'parse_audits':   parse_audits,
    'parse_wigglers': parse_wigglers,
}

# Group tasks by lane so scheduler can pull 1 per lane per day
all_tasks = []
lane_tasks = {}   # lane_label → [tasks]
failed_repos = []

for entry in REGISTRY:
    lane = entry['lane']
    try:
        fn = PARSERS.get(entry['parser'])
        if fn:
            tasks = fn(entry['owner'], entry['repo'], entry['ns'])
            all_tasks.extend(tasks)
            if lane not in lane_tasks:
                lane_tasks[lane] = []
            lane_tasks[lane].extend(tasks)
            print(f'  ✓ {lane} — {len(tasks)} tasks')
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        failed_repos.append(entry['repo'])
        print(f'  ⚠ {lane} ({entry["repo"]}) — UNREACHABLE ({e})')
    except Exception as e:
        failed_repos.append(entry['repo'])
        print(f'  ⚠ {lane} ({entry["repo"]}) — ERROR ({e})')

(OUT / 'failed_repos.json').write_text(json.dumps(failed_repos))
(OUT / 'lane_names.json').write_text(json.dumps(list(lane_tasks.keys())))

if failed_repos:
    print(f'\n⚠ {len(failed_repos)} repo(s) failed — do NOT push until resolved.')

# Load done state
done_state = {}
try:
    done_data = gh_file('Cal-Starfur', 'claude-skills', 'tools/calendar-done.json')
    done_state = json.loads(done_data)
    print(f'\nLoaded done state: {sum(done_state.values())} tasks marked done')
except Exception:
    print('\nNo existing done state — starting fresh')

for t in all_tasks:
    t['done'] = bool(done_state.get(t['id'], False))

(OUT / 'tasks.json').write_text(json.dumps(all_tasks, indent=2))
print(f'\n✓ {len(all_tasks)} total tasks | {len(lane_tasks)} lanes')
for lane, tasks in lane_tasks.items():
    open_c = sum(1 for t in tasks if not done_state.get(t['id'], False))
    print(f'  {lane}: {open_c} open')
```

## EMBEDDED SCRIPT: build_calendar.py
*Write this to `/tmp/project-calendar/build_calendar.py`*

```python
"""
build_calendar.py v3 — 1 task per lane per day, cadence scheduling, audit lane included
"""
import json
from pathlib import Path
from datetime import date, timedelta

OUT = Path('/tmp/project-calendar')
tasks = json.loads((OUT / 'tasks.json').read_text())
lanes = json.loads((OUT / 'lane_names.json').read_text())
TODAY = date.today()

PRIORITY_ORDER = {'P1': 0, 'P2': 1, 'P3': 2}
TYPE_ORDER = {'skill': 0, 'audit': 1, 'game': 2, 'fix': 3}

# Build per-lane priority queues (open tasks only, sorted)
lane_queues = {}
for lane in lanes:
    lane_tasks = [t for t in tasks if t.get('lane') == lane and not t['done']]
    lane_tasks.sort(key=lambda t: (PRIORITY_ORDER.get(t['priority'], 9), TYPE_ORDER.get(t['type'], 9)))
    lane_queues[lane] = lane_tasks

# ── Scheduling: 1 per lane per day ────────────────────────────────────────
schedule = []
lane_indices = {lane: 0 for lane in lanes}

for i in range(28):
    d = TODAY + timedelta(days=i)
    dow = d.weekday()  # 0=Mon 6=Sun
    is_rest  = (dow == 6)
    is_light = (dow == 5)  # Saturday
    is_today = (i == 0)

    if is_rest:
        schedule.append({'date': d.isoformat(), 'tasks': [], 'is_today': is_today, 'is_rest': True})
        continue

    day_tasks = []
    l_count = 0

    for lane in lanes:
        q = lane_queues[lane]
        idx = lane_indices[lane]

        # Find next suitable task for this lane today
        found = False
        scan = idx
        while scan < len(q):
            t = q[scan]
            # Saturday: skip L-effort game tasks
            if is_light and t['effort'] == 'L' and t['type'] == 'game':
                scan += 1
                continue
            # Hard cap: no more than 2 L-effort tasks in one day
            if t['effort'] == 'L' and l_count >= 2:
                scan += 1
                continue
            # Good to schedule
            day_tasks.append(t)
            if t['effort'] == 'L':
                l_count += 1
            lane_queues[lane].pop(scan)  # remove from queue
            found = True
            break

    schedule.append({'date': d.isoformat(), 'tasks': day_tasks, 'is_today': is_today, 'is_rest': False})

done_tasks = [t for t in tasks if t['done']]
open_tasks = [t for t in tasks if not t['done']]

# ── HTML ──────────────────────────────────────────────────────────────────
DAY_NAMES   = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

LANE_COLORS = {
    'Skills':       {'bg': '#0d0d2a', 'border': '#1e1e4a', 'text': '#818cf8', 'badge': 'skill'},
    'Audits':       {'bg': '#0a1a0a', 'border': '#1a3a1a', 'text': '#86efac', 'badge': 'audit'},
    'Wigglers Room':{'bg': '#052010', 'border': '#1a4d2a', 'text': '#4ade80', 'badge': 'game'},
}

def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f'{MONTH_NAMES[d.month-1]} {d.day}'

def fmt_day(iso):
    d = date.fromisoformat(iso)
    return DAY_NAMES[d.weekday()]

def task_html(t):
    safe_id = t['id'].replace(':', '-')
    lc = LANE_COLORS.get(t.get('lane', ''), {'bg': '#1a1a1f', 'border': '#2e2e38', 'text': '#888', 'badge': 'fix'})
    pri_color = {'P1': '#f87171', 'P2': '#fbbf24', 'P3': '#6b6880'}.get(t['priority'], '#888')
    effort_color = {'S': '#4ade80', 'M': '#fbbf24', 'L': '#f87171'}.get(t['effort'], '#888')
    lane_label = t.get('lane', t['type'].upper())
    return f'''<div class="task" id="t-{safe_id}" style="background:{lc["bg"]};border:1px solid {lc["border"]}">
      <div class="lane-tag" style="color:{lc["text"]}">{lane_label}</div>
      <div class="task-title">{t["title"]}</div>
      <div class="task-meta">
        <span class="pill" style="color:{pri_color};border-color:{pri_color}22;background:{pri_color}11">{t["priority"]}</span>
        <span class="pill" style="color:{effort_color};border-color:{effort_color}22;background:{effort_color}11">{t["effort"]}</span>
      </div>
      <div class="task-desc">{t["desc"]}</div>
      <button class="check-btn" onclick="toggleDone('{safe_id}',event)">✓</button>
    </div>'''

weeks_html = ''
for wi in range(0, 28, 7):
    week = schedule[wi:wi+7]
    if not week: continue
    week_labels = ['This week','Next week','Week 3','Week 4']
    label = week_labels[wi//7] if wi//7 < 4 else f'Week {wi//7+1}'
    days_html = ''
    for day in week:
        classes = 'day-card' + (' today' if day['is_today'] else '') + (' rest' if day['is_rest'] else '')
        today_badge = '<span class="today-badge">today</span>' if day['is_today'] else ''
        task_count = len(day['tasks'])
        if day['is_rest']:
            body = '<div class="rest-label">Rest day 🌱</div>'
        elif not day['tasks']:
            body = '<div class="rest-label">All caught up ✓</div>'
        else:
            body = '<div class="tasks">' + ''.join(task_html(t) for t in day['tasks']) + '</div>'
        count_badge = f'<span class="count-badge">{task_count}</span>' if task_count > 0 else ''
        days_html += f'''<div class="{classes}">
        <div class="day-header">
          <span class="day-name">{fmt_day(day["date"])}{today_badge}</span>
          <span class="day-right"><span class="day-date">{fmt_date(day["date"])}</span>{count_badge}</span>
        </div>{body}</div>'''
    weeks_html += f'<div class="week-section"><div class="week-label">{label} · {fmt_date(week[0]["date"])} – {fmt_date(week[-1]["date"])}</div><div class="days-grid">{days_html}</div></div>'

total = len(tasks)
done_count = len(done_tasks)
p1_open = sum(1 for t in open_tasks if t['priority'] == 'P1')
lane_count = len(lanes)

# Lane summary for header
lane_summary = ''
for lane in lanes:
    open_c = sum(1 for t in tasks if t.get('lane') == lane and not t['done'])
    lc = LANE_COLORS.get(lane, {'text': '#888'})
    lane_summary += f'<div class="lane-pill" style="border-color:{lc["text"]}33;color:{lc["text"]}">{lane} · {open_c} open</div>'

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cal's Dev Calendar</title>
<style>
:root{{--bg:#0f0f11;--surface:#1a1a1f;--border:#2e2e38;--text:#e8e6f0;--muted:#6b6880;--done:#22c55e;--p1:#f87171;--p2:#fbbf24;--font:'SF Mono','Fira Code',monospace;--sans:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:var(--sans);padding:24px 16px 48px}}
header{{margin-bottom:24px}}
h1{{font-size:22px;font-weight:600;letter-spacing:-.5px}}
.subtitle{{font-size:13px;color:var(--muted);margin-top:4px}}
.sync-info{{font-size:11px;font-family:var(--font);color:var(--muted);margin:12px 0 20px}}
.stats-row{{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}}
.stat{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 18px;text-align:center}}
.stat-num{{font-size:22px;font-weight:700;font-family:var(--font);display:block}}
.stat-label{{font-size:11px;color:var(--muted);display:block;margin-top:2px}}
.lane-pills{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}}
.lane-pill{{font-size:11px;padding:4px 10px;border-radius:20px;border:1px solid;background:transparent}}
.weeks{{display:flex;flex-direction:column;gap:28px}}
.week-label{{font-size:11px;font-family:var(--font);color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:10px}}
.days-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px}}
.day-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px}}
.day-card.today{{border-color:#818cf8;box-shadow:0 0 0 1px #818cf8 inset}}
.day-card.rest{{opacity:.4}}
.day-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}}
.day-name{{font-size:13px;font-weight:600}}
.day-right{{display:flex;align-items:center;gap:6px}}
.day-date{{font-size:11px;font-family:var(--font);color:var(--muted)}}
.today-badge{{font-size:10px;background:#818cf8;color:#fff;padding:2px 7px;border-radius:20px;font-weight:600;margin-left:6px}}
.count-badge{{font-size:10px;background:var(--border);color:var(--muted);padding:2px 6px;border-radius:10px;font-family:var(--font)}}
.rest-label{{font-size:12px;color:var(--muted);font-style:italic}}
.tasks{{display:flex;flex-direction:column;gap:7px}}
.task{{border-radius:8px;padding:9px 11px;position:relative}}
.task.done{{opacity:.35}}
.task.done .task-title{{text-decoration:line-through}}
.lane-tag{{font-size:10px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;margin-bottom:4px;opacity:.8}}
.task-title{{font-size:12px;font-weight:500;line-height:1.35;padding-right:22px;margin-bottom:5px}}
.task-meta{{display:flex;gap:4px;margin-bottom:4px}}
.pill{{font-size:10px;font-family:var(--font);padding:1px 6px;border-radius:4px;border:1px solid;font-weight:600}}
.task-desc{{font-size:11px;color:var(--muted);line-height:1.45}}
.check-btn{{position:absolute;top:9px;right:9px;width:17px;height:17px;border-radius:50%;border:1.5px solid var(--border);background:transparent;cursor:pointer;font-size:9px;color:transparent;transition:all .15s}}
.check-btn:hover{{border-color:var(--done);color:var(--done)}}
.task.done .check-btn{{border-color:var(--done);background:var(--done);color:#fff}}
@media(max-width:600px){{.days-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header>
  <h1>🪱 Dev Calendar</h1>
  <div class="subtitle">1 task per repo per day · every front advances · no burnout</div>
</header>
<div class="sync-info">Last built: {TODAY.isoformat()} · {total} tasks across {lane_count} lanes · say "sync the calendar" to update</div>
<div class="stats-row">
  <div class="stat"><span class="stat-num">{total}</span><span class="stat-label">total</span></div>
  <div class="stat"><span class="stat-num" style="color:var(--done)">{done_count}</span><span class="stat-label">done</span></div>
  <div class="stat"><span class="stat-num" style="color:var(--p1)">{p1_open}</span><span class="stat-label">P1 open</span></div>
  <div class="stat"><span class="stat-num">{lane_count}</span><span class="stat-label">active lanes</span></div>
</div>
<div class="lane-pills">{lane_summary}</div>
<div class="weeks">{weeks_html}</div>
<script>
const K='cal_done_v3';
function getDone(){{try{{return JSON.parse(localStorage.getItem(K)||'{{}}')}}catch{{return {{}}}}}}
function toggleDone(id,e){{
  e.stopPropagation();
  const d=getDone();d[id]=!d[id];
  localStorage.setItem(K,JSON.stringify(d));
  const el=document.getElementById('t-'+id);
  if(el)el.classList.toggle('done',!!d[id]);
}}
(function(){{
  const d=getDone();
  Object.entries(d).forEach(([id,v])=>{{if(v){{const el=document.getElementById('t-'+id);if(el)el.classList.add('done');}}}});
}})();
</script>
</body></html>'''

(OUT / 'project-calendar.html').write_text(html)
print(f'✓ Calendar built — {len(schedule)} days')
print(f'  Lanes: {", ".join(lanes)}')
print(f'  Tasks scheduled: {sum(len(d["tasks"]) for d in schedule)}')
```

## EMBEDDED SCRIPT: push_calendar.py
*Write this to `/tmp/project-calendar/push_calendar.py`*

```python
"""
push_calendar.py v3 — blocks on failed repos, sanitizes token, updates CHANGELOG
"""
import json, base64, re
from pathlib import Path
from datetime import date
import urllib.request, urllib.error

config = json.loads(Path('/tmp/project-calendar/config.json').read_text())
TOKEN = config['token']
OWNER = 'Cal-Starfur'
REPO  = 'claude-skills'
HEADERS = {'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json', 'Accept': 'application/vnd.github.v3+json'}
OUT = Path('/tmp/project-calendar')

failed = json.loads((OUT / 'failed_repos.json').read_text()) if (OUT / 'failed_repos.json').exists() else []
if failed:
    print(f'⚠ PUSH BLOCKED — repos unreachable: {", ".join(failed)}')
    print('  Re-run pull_tasks.py after fixing the connection.')
    exit(1)

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

def push_file(file_path, content, message, do_sanitize=False):
    existing, status = gh_get(f'{OWNER}/{REPO}/contents/{file_path}')
    sha = existing.get('sha') if status == 200 else None
    safe = sanitize(content) if do_sanitize else content
    payload = {'message': message, 'content': base64.b64encode(safe.encode()).decode()}
    if sha: payload['sha'] = sha
    result, code = gh_put(f'{OWNER}/{REPO}/contents/{file_path}', payload)
    if code in (200, 201): print(f'✓ {file_path}')
    else: print(f'✗ {file_path} — {code}: {result.get("message")}')

tasks  = json.loads((OUT / 'tasks.json').read_text())
lanes  = json.loads((OUT / 'lane_names.json').read_text())
done_state = {t['id']: True for t in tasks if t['done']}
total  = len(tasks)
done_c = len(done_state)
open_c = total - done_c
p1_open = sum(1 for t in tasks if t['priority'] == 'P1' and not t['done'])
lane_summary = ', '.join(f'{l}: {sum(1 for t in tasks if t.get("lane")==l and not t["done"])} open' for l in lanes)

push_file('tools/project-calendar.html', (OUT / 'project-calendar.html').read_text(),
          f'Calendar sync {date.today().isoformat()}: {open_c} open across {len(lanes)} lanes', do_sanitize=True)

push_file('tools/calendar-done.json', json.dumps(done_state, indent=2),
          f'Calendar sync: done state ({done_c} tasks)')

existing_cl, status = gh_get(f'{OWNER}/{REPO}/contents/CHANGELOG.md')
if status == 200:
    current = base64.b64decode(existing_cl['content'].replace('\n','')).decode()
    entry = (f'## {date.today().isoformat()} — Calendar sync\n\n'
             f'- {total} tasks across {len(lanes)} lanes ({lane_summary})\n'
             f'- P1 open: {p1_open} | Done: {done_c} | Open: {open_c}\n\n---\n\n')
    updated = current.replace(
        '# Skill Changelog\n\nTracks all skill changes across sessions. Newest entries at the top.\n\n---\n\n',
        f'# Skill Changelog\n\nTracks all skill changes across sessions. Newest entries at the top.\n\n---\n\n{entry}'
    )
    push_file('CHANGELOG.md', updated, f'Calendar sync {date.today().isoformat()}: CHANGELOG updated')

print(f'\n✓ Pushed — {total} tasks | {len(lanes)} lanes | {p1_open} P1 open')
```
