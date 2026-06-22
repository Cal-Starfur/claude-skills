"""
build_calendar.py v4 — adds status header (CI, Devvit version, open P1s)
"""
import json, base64, urllib.request, urllib.error
from pathlib import Path
from datetime import date, timedelta

config = json.loads(Path('/tmp/project-calendar/config.json').read_text())
TOKEN = config['token']

def gh_api(path, owner='Cal-Starfur'):
    url = f'https://api.github.com/repos/{owner}/{path}'
    req = urllib.request.Request(url, headers={
        'Authorization': f'token {TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'CalendarBuild/1.0'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except:
        return None

def get_status():
    # CI status — latest run on Wigglers_Room
    runs = gh_api('Wigglers_Room/actions/runs?per_page=5')
    ci_status = '?'
    ci_color = '#6b6880'
    ci_commit = ''
    if runs:
        for run in runs['workflow_runs']:
            if run['name'] == 'CI':
                ci_status = run['conclusion'] or run['status']
                ci_color = '#4ade80' if ci_status == 'success' else '#f87171' if ci_status == 'failure' else '#fbbf24'
                ci_commit = run['head_sha'][:7]
                break

    # Last Devvit version from devvit.yaml
    devvit_ver = '?'
    try:
        data = gh_api('Wigglers_Room/contents/devvit.yaml')
        if data:
            content = base64.b64decode(data['content'].replace('\n','')).decode()
            m = re.search(r'version:\s*([\d.]+)', content)
            if m: devvit_ver = m.group(1)
    except: pass

    # Open P1s across all repos
    p1_count = 0
    try:
        tasks = json.loads((Path('/tmp/project-calendar') / 'tasks.json').read_text())
        p1_count = sum(1 for t in tasks if t['priority'] == 'P1' and not t['done'])
    except: pass

    return ci_status, ci_color, ci_commit, devvit_ver, p1_count

ci_status, ci_color, ci_commit, devvit_ver, p1_open_count = get_status()

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
.sync-info{{font-size:11px;font-family:var(--font);color:var(--muted);margin:8px 0 16px}}
.status-bar{{display:flex;gap:16px;flex-wrap:wrap;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:12px 16px;margin-bottom:12px;align-items:center}}
.status-item{{display:flex;align-items:center;gap:6px}}
.status-label{{font-size:10px;font-family:var(--font);color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.status-value{{font-size:13px;font-family:var(--font);font-weight:600;color:var(--text)}}
.status-meta{{font-size:10px;font-family:var(--font);color:var(--muted)}}
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
<div class="status-bar">
  <div class="status-item">
    <span class="status-label">CI</span>
    <span class="status-value" style="color:{ci_color}">{ci_status}</span>
    <span class="status-meta">{ci_commit}</span>
  </div>
  <div class="status-item">
    <span class="status-label">Devvit</span>
    <span class="status-value">{devvit_ver}</span>
  </div>
  <div class="status-item">
    <span class="status-label">P1 Open</span>
    <span class="status-value" style="color:#f87171">{p1_open_count}</span>
  </div>
  <div class="status-item">
    <span class="status-label">Synced</span>
    <span class="status-value">{TODAY.isoformat()}</span>
  </div>
</div>
<div class="sync-info">say "sync the calendar" to update · {total} tasks across {lane_count} lanes</div>
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
