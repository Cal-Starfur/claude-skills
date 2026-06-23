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
    {'owner': 'Cal-Starfur', 'repo': 'claude-skills',   'parser': 'parse_skills',        'ns': 'skills',   'lane': 'Skills'},
    {'owner': 'Cal-Starfur', 'repo': 'claude-skills',   'parser': 'parse_audits',        'ns': 'audits',   'lane': 'Audits'},
    {'owner': 'Cal-Starfur', 'repo': 'Wigglers_Room',   'parser': 'parse_wigglers',      'ns': 'wigglers', 'lane': 'Wigglers Room'},
    {'owner': 'Cal-Starfur', 'repo': 'Wigglers_Room',   'parser': 'parse_monetization',  'ns': 'monetize', 'lane': 'Monetization'},
    {'owner': 'Cal-Starfur', 'repo': 'Wigglers_Room',   'parser': 'parse_video',         'ns': 'video',    'lane': 'Video & Marketing'},
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

# ── Task hold dates — entire lanes or specific tasks blocked until a date ──────
# LANE_HOLD: hold entire lane until date — no Wigglers tasks scheduled until then
# TASK_HOLD: hold specific task IDs
LANE_HOLD = {
    'Wigglers Room': '2026-07-01',  # can't deploy/test live until July 1
}
TASK_HOLD = {}  # add specific task overrides here if needed

def apply_not_before(tasks):
    from datetime import date
    today = date.today().isoformat()
    for t in tasks:
        lane_hold = LANE_HOLD.get(t.get('lane'))
        task_hold = TASK_HOLD.get(t['id'])
        hold = task_hold or lane_hold
        if hold and today < hold:
            t['priority'] = 'P3'
            if not t.get('desc','').startswith('[HELD'):
                t['desc'] = f"[HELD until {hold}] " + t.get('desc', '')
    return tasks

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
        'session-health':           (92, '2026-06-22'),
        'devvit-pipeline':          (90, '2026-06-22'),
        'github-sync':              (88, '2026-06-22'),
        'lead-dev':                 (88, '2026-06-22'),
        'contractor':               (87, '2026-06-22'),
        'project-calendar':         (88, '2026-06-22'),
        'wigglers-architecture':    (87, '2026-06-22'),
        'save-skill-workflow':      (87, '2026-06-22'),
        'canvas-art-optimizer':     (87, '2026-06-22'),
        'png-canvas-art-optimizer': (87, '2026-06-22'),
        'skill-audit':              (88, '2026-06-22'),
        'session-summary':          (88, '2026-06-22'),
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

# ── Parser: Monetization lane ─────────────────────────────────────────────
# Hardcoded task list — monetization tasks managed here, not in WIGGLERS_AUDIT
# Add new tasks by appending to MONETIZATION_TASKS below.
# ── Video / Marketing production tasks ────────────────────────────────────
VIDEO_TASKS = [
    {
        'id': 'VID-1',
        'title': 'VID-1: Build tunnel glow reveal animation (Remotion → MP4)',
        'desc': 'Load skills/user/video/remotion-official/SKILL.md. '
                'Describe: 10-second tunnel glow reveal — amber warmth builds from centre outward, '
                'worm silhouette emerges, Wigglers Room title fades in. '
                'Render to MP4. Use as hero asset for all Reddit launch posts. '
                'This is the #1 marketing asset for the game.',
        'priority': 'P1',
        'effort': 'M',
    },
    {
        'id': 'VID-2',
        'title': 'VID-2: Build 30-second gameplay trailer (Remotion → MP4)',
        'desc': 'Load skills/user/video/remotion-official/SKILL.md. '
                'Describe: worm eats scraps → digs tunnel → poops (casting enriches soil) → '
                'tea level fills → weekly drain → offspring. '
                'Voiceover optional (ElevenLabs skill). '
                'Target: Reddit video post for r/incremental_games launch day.',
        'priority': 'P1',
        'effort': 'L',
    },
    {
        'id': 'VID-3',
        'title': 'VID-3: Build worm life cycle loop GIF (canvas → GIF)',
        'desc': 'Animate the full worm life cycle as a seamless loop. '
                'Export as GIF for Reddit inline posts (MP4 autoplay not always supported). '
                'Use existing canvas art + Remotion GIF export rule: '
                'skills/user/video/remotion-official/rules/gifs.md',
        'priority': 'P2',
        'effort': 'M',
    },
    {
        'id': 'VID-4',
        'title': 'VID-4: Build tea drain countdown animation (Remotion)',
        'desc': 'Visualise the weekly tea drain mechanic — sump fills across 7 days, '
                'drains with a satisfying glug animation. '
                'Use as explainer asset for community posts about the shared economy mechanic.',
        'priority': 'P2',
        'effort': 'M',
    },
    {
        'id': 'VID-5',
        'title': 'VID-5: Record gameplay demo via Playwright (screen capture)',
        'desc': 'Load skills/user/video/playwright-recording/SKILL.md. '
                'Record a live gameplay session — open the Wigglers Room post, '
                'show worm movement, tunnelling, other players. '
                'Use as authentic gameplay footage for post-launch posts.',
        'priority': 'P3',
        'effort': 'M',
    },
    {
        'id': 'VID-6',
        'title': 'VID-6: Generate AI voiceover for gameplay trailer (ElevenLabs)',
        'desc': 'Load skills/user/video/elevenlabs/SKILL.md. '
                'Write and generate a 30-second voiceover script for VID-2 trailer. '
                'Tone: warm, curious, slightly nerdy. '
                'Use /generate-voiceover command from skills/user/video/commands/generate-voiceover.md',
        'priority': 'P3',
        'effort': 'S',
    },
]

MONETIZATION_TASKS = [
    {
        'id': 'MON-1',
        'title': 'MON-1: Add Tunnel Glow Pack — Gold purchasable item',
        'desc': 'Implement useProducts hook + fulfillOrder handler for Tunnel Glow Pack. '
                'Define product in devvit.json (sku: tunnel_glow_pack, price: 50 Gold). '
                'On purchase, store unlock in KV: user:{id}:unlocks tunnelGlow=true. '
                'Apply glow color in drawTunnel() based on unlock flag. '
                'Reference: skills/user/devvit-payments/src/server/index.ts',
        'priority': 'P1',
        'effort': 'L',
    },
    {
        'id': 'MON-2',
        'title': 'MON-2: Register for Reddit Developer Funds 2026',
        'desc': 'Message r/devvit modmail to register Wigglers Room for the Developer '
                'Funds program. Program ends July 31 2026. 500 DQE = $500 payout. '
                'Confirm subreddit has 200+ members (required for DQE to count).',
        'priority': 'P1',
        'effort': 'S',
    },
    {
        'id': 'MON-3',
        'title': 'MON-3: Run /ros first-dollar — fastest path to first Gold sale',
        'desc': 'Load revenue-os skill, run /ros first-dollar to identify the single '
                'highest-leverage action for Wigglers Room first revenue. '
                'Reference: skills/user/revenue-os/commands/ros-first-dollar.md',
        'priority': 'P1',
        'effort': 'S',
    },
    {
        'id': 'MON-4',
        'title': 'MON-4: Run /ros icp — identify ideal paying player profile',
        'desc': 'Who in r/incremental_games or r/compost would spend Gold on Wigglers Room? '
                'Run /ros icp to define the ideal customer before launch day.',
        'priority': 'P2',
        'effort': 'S',
    },
    {
        'id': 'MON-5',
        'title': 'MON-5: Add Worm Speed Boost — second Gold purchasable item',
        'desc': '2x worm movement speed for 24 hours. Price: 25 Gold. '
                'Time-limited boost stored in KV with expiry timestamp. '
                'Add after MON-1 Tunnel Glow Pack ships.',
        'priority': 'P2',
        'effort': 'M',
    },
    {
        'id': 'MON-6',
        'title': 'MON-6: Run /ros pricing — validate Gold prices against psychology',
        'desc': 'Check Tunnel Glow Pack (50 Gold) and Worm Speed Boost (25 Gold) against '
                'pricing psychology frameworks. Adjust before launch if needed.',
        'priority': 'P2',
        'effort': 'S',
    },
    {
        'id': 'MON-7',
        'title': 'MON-7: Add Premium Worm Skin — cosmetic Gold item',
        'desc': 'Rare worm appearance (glowing, golden, spotted). Price: 75 Gold. '
                'Pure cosmetic — no gameplay effect. Best for post-launch when '
                'players are attached to their worms.',
        'priority': 'P3',
        'effort': 'M',
    },
    {
        'id': 'MON-8',
        'title': 'MON-8: Run /ros audit — full monetization readiness score',
        'desc': 'Score Wigglers Room monetization readiness across all dimensions. '
                'Run after MON-1 and MON-2 are complete, before launch day.',
        'priority': 'P3',
        'effort': 'S',
    },
]

def parse_monetization(owner, repo, ns):
    tasks = []
    print(f'  [{ns}] Loading monetization tasks...')
    for t in MONETIZATION_TASKS:
        tasks.append({
            'id': ns_id(ns, t['id'].lower()),
            'title': t['title'],
            'type': 'monetize',
            'priority': t['priority'],
            'effort': t['effort'],
            'repo': repo,
            'lane': 'Monetization',
            'desc': t['desc'],
            'done': False,
        })
    print(f'    → {len(tasks)} monetization tasks')
    return tasks

def parse_video(owner, repo, ns):
    tasks = []
    print(f'  [{ns}] Loading video/marketing production tasks...')
    for t in VIDEO_TASKS:
        tasks.append({
            'id': ns_id(ns, t['id'].lower()),
            'title': t['title'],
            'type': 'video',
            'priority': t['priority'],
            'effort': t['effort'],
            'repo': repo,
            'lane': 'Video & Marketing',
            'desc': t['desc'],
            'done': False,
        })
    print(f'    → {len(tasks)} video tasks')
    return tasks

# ── Main ───────────────────────────────────────────────────────────────────
PARSERS = {
    'parse_skills':        parse_skills,
    'parse_audits':        parse_audits,
    'parse_wigglers':      parse_wigglers,
    'parse_monetization':  parse_monetization,
    'parse_video':         parse_video,
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

# Apply hold dates — demote blocked P1s to P3 until their date
all_tasks = apply_not_before(all_tasks)
for lane in lane_tasks:
    lane_tasks[lane] = apply_not_before(lane_tasks[lane])
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
