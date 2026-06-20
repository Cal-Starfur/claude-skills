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
