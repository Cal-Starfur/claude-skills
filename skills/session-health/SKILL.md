---
name: session-health
description: Load this skill at the start of EVERY Wigglers Room session, before touching any code. Runs an automated health check that pulls live files from GitHub, cross-checks GAME_ARCHITECTURE.md against the actual code, reports any drift, and auto-fixes stale session numbers, Devvit versions, and line counts. If bridge3.js is offline, displays the start command and waits up to 5 minutes for it to come online — Claude never asks the user to re-run, it polls automatically. Also runs a post-session update to keep all docs current after code changes ship. Triggers when the user says anything about Wigglers Room, game.js, PERF-1, the audit, or starting a new session. This is the agent that keeps all the docs honest so Claude never works from stale information.
---

# Session Health Agent — Wigglers Room

**Runs at the start of every session. No exceptions.**
Never touch code until this clears.

---

## What it does

- Pulls `GAME_ARCHITECTURE.md`, `WIGGLERS_AUDIT.md`, `main.tsx`, `game.js`, `devvit.yaml` fresh
- Checks 9 categories of drift against live code
- Auto-fixes: session number, Devvit version, line counts
- If bridge offline: shows start command, **polls every 15s for up to 5 minutes** until it comes online
- Flags: ghost messages, stale priority queue, closed issues still listed as open, missing globals
- After session: bumps session number, Devvit version, updates priority queue
- **Never asks the user to re-run** — waits and detects automatically

---

## Step 0 — Bootstrap (Every Session)

```bash
python3 << 'BOOTSTRAP'
import re
from pathlib import Path

skill_path = '/mnt/skills/user/session-health/SKILL.md'
content = Path(skill_path).read_text()
sections = re.findall(
    r'## EMBEDDED SCRIPT: .+?\n\*Write this to `(.+?)`\*\n\n```python\n(.*?)```',
    content, re.DOTALL
)
for target_path, code in sections:
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code)
    print(f"✓ {target_path}")
print("Bootstrap complete.")
BOOTSTRAP
```

---

## Step 1 — Run Health Check

```bash
python3 /tmp/session-health/health_check.py --token <PAT> --fix
```

- `--fix` auto-pushes corrections for session number, Devvit version, line counts
- If bridge is offline: displays start command, then **waits up to 5 minutes polling every 15s**
- Claude never asks the user to re-run — it detects the bridge coming online automatically
- All-clear → proceed to code work
- Hard fail (bridge never came up) → version unconfirmed, doc fixes still applied

**Token:** use the same GitHub PAT as github-sync — never store it

---

## Step 2 — Read the Docs

After health check passes, read fresh:
```bash
# Already pulled by health check — cached at:
cat /tmp/sh_arch.md    # GAME_ARCHITECTURE.md
cat /tmp/sh_audit.md   # WIGGLERS_AUDIT.md
```

The health check caches both files to `/tmp/` — no second pull needed.

---

## Step 3 — Run Post-Session Update

After code ships and is pushed to GitHub:
```bash
python3 /tmp/session-health/health_check.py \
  --token <PAT> \
  --post-session \
  --session 21 \
  --devvit 0.0.180
```

This bumps the session number, Devvit version, and date in the header.
Bigger changes (moving closed issues, updating priority queue) do manually via github-sync.

---

## What Gets Checked

| Category | What it looks for |
|---|---|
| Header | Session number, Devvit version, next P1 — stale? |
| Line counts | main.tsx and game.js — off by >50/100 lines? |
| Preview card | Animated vs static description correct? |
| Message constants | Ghost MSG_* in arch but not in code? |
| KV keys | pooled still shown as synced? |
| Session fields | pAcid, bornTs, visibilitychange present? |
| Global state | weekStartTs, camX, centreOffsetX, WORLD_W all documented? |
| Open issues | Closed issues still listed as P1? |
| Priority queue | PERF-1 as P1? Stale ISS-14/ISS-13 entries? |

---

## Repo Config

- **Owner:** Cal-Starfur
- **Repo:** Wigglers_Room
- **Branch:** main
- **Files watched:** GAME_ARCHITECTURE.md, WIGGLERS_AUDIT.md, src/main.tsx, webroot/game.js, devvit.yaml

---

## Integration with Other Skills

This skill runs **before** lead-dev, contractor, or wigglers-architecture.
Order every Wigglers session:
```
1. session-health  → health check + auto-fix + read docs
2. github-sync     → set token, point at Wigglers_Room
3. wigglers-architecture → structural reference (already loaded)
4. contractor / lead-dev → code work
```

---

## EMBEDDED SCRIPT: health_check.py
*Write this to `/tmp/session-health/health_check.py`*

```python
#!/usr/bin/env python3
"""
session-health/scripts/health_check.py

Pulls live files, cross-checks GAME_ARCHITECTURE.md against code,
checks bridge liveness, confirms/updates Devvit version.

Usage:
    python3 health_check.py --token <pat> [--fix]
    python3 health_check.py --token <pat> --post-session --session 21

Version check logic:
    Bridge ONLINE  → ping devvit.yaml version to confirm → update arch if stale → PASS
    Bridge OFFLINE → FAIL (cannot confirm version — arch may be wrong)
    Bridge TIMEOUT → FAIL (same)
"""

import sys, re, json, base64, urllib.request, urllib.error, argparse, time
from pathlib import Path
from datetime import datetime

OWNER        = 'Cal-Starfur'
REPO         = 'Wigglers_Room'
BRIDGE_OWNER = 'Cal-Starfur'
BRIDGE_REPO  = 'codespace-bridge'

# ── GitHub helpers ─────────────────────────────────────────────────────────────

def gh_headers(token):
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'SessionHealthAgent/1.0',
    }

def gh_get(token, repo, path, owner=None):
    o = owner or OWNER
    url = f'https://api.github.com/repos/{o}/{repo}/contents/{path}'
    req = urllib.request.Request(url, headers=gh_headers(token))
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        content = base64.b64decode(data['content'].replace('\n', '')).decode('utf-8')
        return content, data['sha']

def gh_get_json(token, repo, path, owner=None):
    content, sha = gh_get(token, repo, path, owner)
    return json.loads(content), sha

def gh_put(token, repo, path, content, sha, message, owner=None):
    o = owner or OWNER
    url = f'https://api.github.com/repos/{o}/{repo}/contents/{path}'
    if isinstance(content, str):
        content = content.encode('utf-8')
    data = {
        'message': message,
        'content': base64.b64encode(content).decode(),
        'sha': sha,
    }
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(), headers=gh_headers(token), method='PUT'
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
        return result['commit']['sha'][:7]

# ── Bridge check + version confirmation ───────────────────────────────────────

def check_bridge_and_version(token):
    """
    The bridge is the ONLY reliable source of the real Devvit version.

    Returns:
        (status, version_or_none, message)
        status: 'online' | 'offline' | 'error'
        version_or_none: e.g. '0.0.180' if confirmed, None if not
        message: human-readable description
    """
    # Read current relay state
    try:
        outbox, outbox_sha = gh_get_json(token, BRIDGE_REPO, 'relay/outbox.json', BRIDGE_OWNER)
        inbox,  inbox_sha  = gh_get_json(token, BRIDGE_REPO, 'relay/inbox.json',  BRIDGE_OWNER)
    except Exception as e:
        return 'error', None, f'Cannot reach bridge relay: {e}'

    # Send ping to confirm bridge is alive
    ping_id  = f'health-ping-{int(time.time())}'
    ping_cmd = {
        'cmd': 'cat /workspaces/Wigglers_Room/devvit.yaml | grep "^version:"',
        'id':  ping_id,
        'cwd': '/workspaces/Wigglers_Room',
        'ts':  datetime.now().isoformat(),
    }

    try:
        gh_put(token, BRIDGE_REPO, 'relay/inbox.json',
               json.dumps(ping_cmd, indent=2).encode(),
               inbox_sha, f'Health check ping {ping_id}', BRIDGE_OWNER)
    except Exception as e:
        return 'error', None, f'Could not write ping to inbox: {e}'

    # Poll outbox for up to 20s
    deadline = time.time() + 20
    while time.time() < deadline:
        time.sleep(3)
        try:
            outbox2, _ = gh_get_json(token, BRIDGE_REPO, 'relay/outbox.json', BRIDGE_OWNER)
            if outbox2.get('id') == ping_id:
                if outbox2.get('ready') or outbox2.get('output') is not None:
                    output = outbox2.get('output', '').strip()
                    # Parse version from "version: 0.0.179"
                    m = re.search(r'version:\s*([\d.]+)', output)
                    if m:
                        version = m.group(1)
                        elapsed = int(20 - (deadline - time.time()))
                        return 'online', version, f'Bridge alive ({elapsed}s) — Devvit version confirmed: {version}'
                    elif output:
                        return 'online', None, f'Bridge alive but version parse failed: {output[:80]}'
                    else:
                        return 'online', None, 'Bridge alive but empty output from devvit.yaml'
        except:
            pass

    # No response
    return 'offline', None, 'Bridge did not respond within 20s — likely offline'

# ── Doc checks ────────────────────────────────────────────────────────────────

def check_header(arch, audit, confirmed_version=None):
    issues = []
    fixes  = []

    # Session number
    arch_s  = re.search(r'Session (\d+)', arch)
    audit_s = re.search(r'Current session[^\d]*(\d+)', audit)
    if arch_s and audit_s:
        a, b = int(arch_s.group(1)), int(audit_s.group(1))
        if b > a:
            issues.append(f'Session number stale: arch says {a}, audit says {b}')
            fixes.append(('session', a, b))

    # Devvit version — only check if bridge confirmed it
    if confirmed_version:
        arch_v = re.search(r'Devvit\s+([\d.]+)', arch)
        if arch_v and arch_v.group(1) != confirmed_version:
            issues.append(f'Devvit version stale: arch says {arch_v.group(1)}, confirmed {confirmed_version}')
            fixes.append(('devvit', arch_v.group(1), confirmed_version))
        elif not arch_v:
            issues.append('Devvit version missing from arch header')

    return issues, fixes

def check_line_counts(arch, main_tsx, game_js):
    issues = []
    actual_main = len(main_tsx.splitlines())
    actual_game = len(game_js.splitlines())

    m = re.search(r'main\.tsx.*?~?(\d+)\s*lines', arch)
    if m:
        claimed = int(m.group(1))
        if abs(claimed - actual_main) > 50:
            issues.append(f'main.tsx lines: arch ~{claimed}, actual {actual_main}')

    m = re.search(r'game\.js.*?~?(\d+)\s*lines', arch)
    if m:
        claimed = int(m.group(1))
        if abs(claimed - actual_game) > 100:
            issues.append(f'game.js lines: arch ~{claimed}, actual {actual_game}')

    return issues, actual_main, actual_game

def check_globals(arch, game_js):
    issues = []
    for pattern, msg in [
        ('var pAcid',         'pAcid missing from global state'),
        ('var weekStartTs',   'weekStartTs missing from global state'),
        ('var camX',          'camX missing from arch'),
        ('var centreOffsetX', 'centreOffsetX missing from arch'),
    ]:
        if pattern in game_js and pattern not in arch:
            issues.append(msg)
    return issues

def check_messages(arch, main_tsx, game_js):
    issues = []
    arch_msgs = set(re.findall(r'MSG_\w+', arch))
    live_msgs = set(re.findall(r'MSG_\w+', main_tsx)) | set(re.findall(r'MSG_\w+', game_js))
    for m in arch_msgs - live_msgs - {'MSG_SET_WEATHER'}:
        issues.append(f'Ghost message: {m} in arch but not in code')
    if 'MSG_SET_WEATHER' in arch:
        idx = arch.index('MSG_SET_WEATHER')
        ctx = arch[max(0, idx-50):idx+100]
        if 'removed' not in ctx.lower():
            issues.append('MSG_SET_WEATHER listed as active — was removed S20')
    return issues

def check_kv_and_fields(arch, game_js):
    issues = []
    # pooled should not be in KV_WORLD as synced
    if 'KV_WORLD' in arch:
        idx = arch.index('KV_WORLD')
        ctx = arch[idx:idx+200]
        if 'pooled' in ctx and 'REMOVED' not in ctx and 'runtime-only' not in ctx:
            issues.append('KV_WORLD still shows pooled as synced (removed S20)')
    # pAcid in session fields
    if 'Fields:' in arch:
        idx = arch.index('Fields:')
        ctx = arch[idx:idx+400]
        if 'pAcid' not in ctx:
            issues.append('pAcid missing from saveSession fields list')
        if 'pooled' in ctx and 'runtime' not in ctx:
            issues.append('pooled still in saveSession fields (removed S20)')
    return issues

def check_priority_queue(arch):
    issues = []
    if 'START HERE: ISS-14' in arch:
        issues.append('Priority queue: ISS-14 still listed as P1 (closed S20)')
    if 'PERF-1' not in arch:
        issues.append('Priority queue: PERF-1 not listed (should be P1)')
    return issues

def check_preview(arch, main_tsx):
    issues = []
    if 'buildBgDataUrl' in main_tsx:
        if 'Animated' not in arch and 'animated' not in arch:
            issues.append('Preview card: arch says static but code has animated buildBgDataUrl')
    return issues

# ── Auto-fix ──────────────────────────────────────────────────────────────────

def apply_fixes(token, arch, arch_sha, fixes, actual_main, actual_game):
    changed = []

    for fix in fixes:
        if fix[0] == 'session':
            arch = re.sub(r'(Session\s+)' + str(fix[1]), r'\g<1>' + str(fix[2]), arch)
            changed.append(f'Session {fix[1]} → {fix[2]}')
        elif fix[0] == 'devvit':
            arch = arch.replace(f'Devvit {fix[1]}', f'Devvit {fix[2]}')
            # Also update devvit.yaml
            try:
                yaml_content, yaml_sha = gh_get(token, REPO, 'devvit.yaml')
                new_yaml = re.sub(r'version:\s*[\d.]+', f'version: {fix[2]}', yaml_content)
                if new_yaml != yaml_content:
                    gh_put(token, REPO, 'devvit.yaml', new_yaml, yaml_sha,
                           f'Sync devvit.yaml version to {fix[2]} (confirmed by bridge)')
                    changed.append(f'devvit.yaml version → {fix[2]}')
            except Exception as e:
                changed.append(f'Devvit version in arch → {fix[2]} (devvit.yaml update failed: {e})')
            else:
                changed.append(f'Devvit version arch + devvit.yaml → {fix[2]}')

    # Line counts
    m = re.search(r'(main\.tsx.*?~?)(\d+)(\s*lines)', arch)
    if m and abs(int(m.group(2)) - actual_main) > 50:
        arch = arch[:m.start(2)] + str(actual_main) + arch[m.end(2):]
        changed.append(f'main.tsx lines → {actual_main}')

    m = re.search(r'(game\.js.*?~?)(\d+)(\s*lines)', arch)
    if m and abs(int(m.group(2)) - actual_game) > 100:
        arch = arch[:m.start(2)] + str(actual_game) + arch[m.end(2):]
        changed.append(f'game.js lines → {actual_game}')

    if changed:
        commit = gh_put(token, REPO, 'GAME_ARCHITECTURE.md', arch, arch_sha,
                        f'Health check auto-fix: {", ".join(changed)}')
        return changed, commit
    return [], None

# ── Post-session ──────────────────────────────────────────────────────────────

def post_session_update(token, session_num, devvit_version):
    arch, arch_sha = gh_get(token, REPO, 'GAME_ARCHITECTURE.md')
    today = datetime.now().strftime('%Y-%m-%d')
    arch = re.sub(r'(> Last updated:\s*)[\d-]+', r'\g<1>' + today, arch)
    arch = re.sub(r'(Session\s+)\d+', r'\g<1>' + str(session_num), arch)
    arch = re.sub(r'(Devvit\s+)[\d.]+', r'\g<1>' + devvit_version, arch)
    commit = gh_put(token, REPO, 'GAME_ARCHITECTURE.md', arch, arch_sha,
                    f'Post-session update: Session {session_num}, Devvit {devvit_version}')
    # Also update devvit.yaml
    try:
        yaml_content, yaml_sha = gh_get(token, REPO, 'devvit.yaml')
        new_yaml = re.sub(r'version:\s*[\d.]+', f'version: {devvit_version}', yaml_content)
        gh_put(token, REPO, 'devvit.yaml', new_yaml, yaml_sha,
               f'Post-session: sync version to {devvit_version}')
    except:
        pass
    return commit

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Wigglers Room Session Health Check')
    parser.add_argument('--token', required=True)
    parser.add_argument('--fix', action='store_true')
    parser.add_argument('--post-session', action='store_true')
    parser.add_argument('--session', type=int)
    parser.add_argument('--devvit', help='Devvit version (post-session only)')
    args = parser.parse_args()
    token = args.token

    print(f'\n{"="*60}')
    print(f'  WIGGLERS ROOM — SESSION HEALTH CHECK')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'{"="*60}\n')

    # ── Post-session shortcut ─────────────────────────────────────────────────
    if args.post_session:
        if not args.session or not args.devvit:
            print('Post-session requires --session N and --devvit X.X.X')
            sys.exit(1)
        print(f'Post-session update: Session {args.session}, Devvit {args.devvit}')
        commit = post_session_update(token, args.session, args.devvit)
        print(f'✓ Pushed — {commit}')
        return

    # ── Pull live files ───────────────────────────────────────────────────────
    print('Pulling live files...')
    try:
        arch,     arch_sha = gh_get(token, REPO, 'GAME_ARCHITECTURE.md')
        audit,    _        = gh_get(token, REPO, 'WIGGLERS_AUDIT.md')
        main_tsx, _        = gh_get(token, REPO, 'src/main.tsx')
        game_js,  _        = gh_get(token, REPO, 'webroot/game.js')
        # Cache for downstream skill reads
        Path('/tmp/sh_arch.md').write_text(arch)
        Path('/tmp/sh_audit.md').write_text(audit)
        print(f'  ✓ GAME_ARCHITECTURE.md ({len(arch.splitlines())} lines)')
        print(f'  ✓ WIGGLERS_AUDIT.md    ({len(audit.splitlines())} lines)')
        print(f'  ✓ main.tsx             ({len(main_tsx.splitlines())} lines)')
        print(f'  ✓ game.js              ({len(game_js.splitlines())} lines)')
    except Exception as e:
        print(f'  ✗ Failed: {e}')
        sys.exit(1)

    # ── Bridge check + version confirmation ───────────────────────────────────
    # Bridge is the ONLY source of confirmed Devvit version.
    # If offline: tell user to start it, then poll until it comes up.
    # Claude cannot start the bridge — it runs in the user's Codespace.
    # But Claude CAN wait for it without making the user re-run anything.

    print('\nChecking bridge3.js + confirming Devvit version...')
    bridge_status, confirmed_version, bridge_msg = check_bridge_and_version(token)

    if bridge_status == 'online':
        print(f'  ✓ {bridge_msg}')
    else:
        err_label = 'OFFLINE' if bridge_status == 'offline' else 'ERROR'
        print(f'  ✗ BRIDGE {err_label} — {bridge_msg}')
        print(f'')
        print(f'  Bridge must be running in your Codespace to confirm the Devvit version.')
        print(f'  Start it:')
        print(f'    export BRIDGE_TOKEN=<your-github-pat>')
        print(f'    node ~/bridge3.js')
        print(f'')
        print(f'  Waiting up to 5 minutes for bridge to come online...')
        print(f'  (start it now — Claude will detect it automatically)')

        # Poll every 15s for up to 5 minutes
        wait_deadline = time.time() + 300
        poll_count = 0
        while time.time() < wait_deadline:
            time.sleep(15)
            poll_count += 1
            remaining = int((wait_deadline - time.time()) / 60)
            print(f'  [{poll_count * 15}s] Still waiting... ({remaining}m left)', flush=True)
            bridge_status, confirmed_version, bridge_msg = check_bridge_and_version(token)
            if bridge_status == 'online':
                print(f'  ✓ Bridge came online! {bridge_msg}')
                break
        else:
            print(f'  ✗ Bridge did not come online within 5 minutes.')
            print(f'  ✗ DEVVIT VERSION UNCONFIRMED — proceeding with doc checks only.')

    # ── Run all checks ────────────────────────────────────────────────────────
    print('\nRunning checks...')
    all_issues = []
    all_fixes  = []

    h_issues, h_fixes = check_header(arch, audit, confirmed_version)
    lc_issues, actual_main, actual_game = check_line_counts(arch, main_tsx, game_js)
    g_issues  = check_globals(arch, game_js)
    m_issues  = check_messages(arch, main_tsx, game_js)
    kv_issues = check_kv_and_fields(arch, game_js)
    pq_issues = check_priority_queue(arch)
    pc_issues = check_preview(arch, main_tsx)

    all_issues = h_issues + lc_issues + g_issues + m_issues + kv_issues + pq_issues + pc_issues
    all_fixes  = h_fixes

    # Bridge offline is always a hard fail — append last so it stands out
    if bridge_status != 'online':
        all_issues.append(f'HARD FAIL: Bridge {bridge_status} — Devvit version unconfirmed')

    # ── Report ────────────────────────────────────────────────────────────────
    if not all_issues:
        print(f'\n✅ ALL CLEAR')
        print(f'   main.tsx: {actual_main} lines | game.js: {actual_game} lines')
        print(f'   Devvit: {confirmed_version} (bridge confirmed)')
        # Show P1
        pq = re.search(r'START HERE.*?(?=###|$)', arch, re.DOTALL)
        if pq:
            lines = [l.strip() for l in pq.group(0).strip().split('\n') if l.strip()][:2]
            print(f'\n📋 P1: {lines[0].replace("### ⚠ P1 — ", "").replace("START HERE: ", "")}')
            if len(lines) > 1:
                print(f'   {lines[1]}')
    else:
        doc_issues = [i for i in all_issues if 'HARD FAIL' not in i]
        hard_fails = [i for i in all_issues if 'HARD FAIL' in i]

        if doc_issues:
            print(f'\n⚠️  DOC DRIFT ({len(doc_issues)} issue(s)):')
            for i in doc_issues:
                print(f'  · {i}')

        if hard_fails:
            print(f'\n🔴 HARD FAIL:')
            for i in hard_fails:
                print(f'  · {i.replace("HARD FAIL: ", "")}')
            print(f'\n  Do NOT update version numbers without bridge confirmation.')
            print(f'  Start bridge: export BRIDGE_TOKEN=<pat> && node ~/bridge3.js')
            print(f'  Then re-run this check.')

        if args.fix and doc_issues:
            print(f'\n🔧 Auto-fixing doc drift...')
            changed, commit = apply_fixes(token, arch, arch_sha, all_fixes, actual_main, actual_game)
            if changed:
                print(f'  ✓ Pushed {commit}:')
                for c in changed:
                    print(f'    → {c}')
                if hard_fails:
                    print(f'  ⚠ Doc fixes applied but version NOT updated — bridge required')
            else:
                print(f'  No auto-fixable items (manual review needed)')

    print(f'\n{"="*60}\n')

if __name__ == '__main__':
    main()
```

