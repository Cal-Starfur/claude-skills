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
