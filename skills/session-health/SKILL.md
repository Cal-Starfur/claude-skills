---
name: session-health
description: Load this skill at the start of EVERY Wigglers Room session, before touching any code. Runs an automated health check that pulls live files from GitHub, cross-checks GAME_ARCHITECTURE.md against the actual code, reports any drift, and auto-fixes stale session numbers, Devvit versions, and line counts. Also runs a post-session update to keep all docs current after code changes ship. Triggers when the user says anything about Wigglers Room, game.js, PERF-1, the audit, or starting a new session. This is the agent that keeps all the docs honest so Claude never works from stale information.
---

# Session Health Agent — Wigglers Room

**Runs at the start of every session. No exceptions.**
Never touch code until this clears.

---

## What it does

- Pulls `GAME_ARCHITECTURE.md`, `WIGGLERS_AUDIT.md`, `main.tsx`, `game.js`, `devvit.yaml` fresh
- Checks 9 categories of drift against live code
- Auto-fixes: session number, Devvit version, line counts
- Flags: ghost messages, stale priority queue, closed issues still listed as open, missing globals
- After session: bumps session number, Devvit version, updates priority queue

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
- All-clear → proceed to code work
- Drift found → review flagged items, fix manually if needed, then proceed

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
Pulls live files from GitHub, cross-checks GAME_ARCHITECTURE.md against
actual code, reports drift, and auto-fixes what it can.

Usage:
    python3 health_check.py --token <pat> [--fix] [--post-session]
"""

import sys, re, json, base64, urllib.request, urllib.error, argparse
from pathlib import Path
from datetime import datetime

OWNER = 'Cal-Starfur'
REPO  = 'Wigglers_Room'

# ── GitHub helpers ────────────────────────────────────────────────────────────

def gh_headers(token):
    return {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json',
        'User-Agent': 'SessionHealthAgent/1.0',
    }

def gh_get(token, path):
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}'
    req = urllib.request.Request(url, headers=gh_headers(token))
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        content = base64.b64decode(data['content'].replace('\n', '')).decode('utf-8')
        return content, data['sha']

def gh_put(token, path, content, sha, message):
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}'
    data = {
        'message': message,
        'content': base64.b64encode(content.encode('utf-8')).decode(),
        'sha': sha,
    }
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(), headers=gh_headers(token), method='PUT'
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
        return result['commit']['sha'][:7]

def gh_get_raw(token, path):
    """Get file without decoding — for binary size check."""
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{path}'
    req = urllib.request.Request(url, headers=gh_headers(token))
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# ── Checks ────────────────────────────────────────────────────────────────────

def check_header(arch, audit):
    issues = []
    fixes  = []

    # Session number
    arch_s  = re.search(r'Session (\d+)', arch)
    audit_s = re.search(r'Current session.*?(\d+)', audit)
    if arch_s and audit_s:
        a, b = int(arch_s.group(1)), int(audit_s.group(1))
        if b > a:
            issues.append(f'Session number: arch says {a}, audit says {b}')
            fixes.append(('session', a, b))

    # Devvit version
    arch_v   = re.search(r'Devvit\s+([\d.]+)', arch)
    devvit_v = re.search(r'version:\s*([\d.]+)', open('/tmp/sh_devvit.yaml').read()) if Path('/tmp/sh_devvit.yaml').exists() else None
    if arch_v and devvit_v:
        av, dv = arch_v.group(1), devvit_v.group(1)
        if av != dv:
            issues.append(f'Devvit version: arch says {av}, devvit.yaml says {dv}')
            fixes.append(('devvit', av, dv))

    # Next P1 stale
    if 'START HERE: ISS-14' in arch:
        if 'ISS-14' in audit and ('✅' in audit or 'CLOSED' in audit or 'closed' in audit.lower()):
            issues.append('Priority queue: ISS-14 listed as P1 but marked closed in audit')
    if 'START HERE: ISS-13' in arch:
        issues.append('Priority queue: ISS-13 listed as P1 but bugs B+C closed in S20')

    return issues, fixes

def check_globals(arch, game_js):
    issues = []
    expected = [
        ('var pAcid',       'pAcid missing from global state'),
        ('var weekStartTs', 'weekStartTs missing from global state'),
        ('var camX',        'camX missing from coordinate section'),
        ('var centreOffsetX', 'centreOffsetX missing'),
        ('var WORLD_W',     'WORLD_W missing'),
    ]
    for pattern, msg in expected:
        if pattern in game_js and pattern not in arch:
            issues.append(msg)
    return issues

def check_messages(arch, main_tsx, game_js):
    issues = []
    arch_msgs = set(re.findall(r'MSG_\w+', arch))
    live_msgs = set(re.findall(r'MSG_\w+', main_tsx)) | set(re.findall(r'MSG_\w+', game_js))

    ghost = arch_msgs - live_msgs - {'MSG_SET_WEATHER'}  # MSG_SET_WEATHER intentionally noted as removed
    for m in ghost:
        issues.append(f'Ghost message: {m} in arch but not in code')

    # Check MSG_SET_WEATHER is noted as removed, not listed as active
    if 'MSG_SET_WEATHER' in arch:
        context = arch[max(0, arch.index('MSG_SET_WEATHER')-50):arch.index('MSG_SET_WEATHER')+80]
        if 'removed' not in context.lower() and 'gone' not in context.lower():
            issues.append('MSG_SET_WEATHER listed as active but was removed S20')

    return issues

def check_kv_keys(arch, main_tsx):
    issues = []
    # pooled should NOT be in KV_WORLD description as a synced field
    if 'KV_WORLD' in arch:
        kv_idx = arch.index('KV_WORLD')
        kv_ctx = arch[kv_idx:kv_idx+200]
        if 'pooled' in kv_ctx and 'runtime-only' not in kv_ctx and 'REMOVED' not in kv_ctx:
            issues.append('KV_WORLD still shows pooled as synced — should be marked runtime-only')

    # getEvapRate should be noted as removed
    if 'getEvapRate' in arch:
        idx = arch.index('getEvapRate')
        ctx = arch[max(0,idx-30):idx+80]
        if 'deleted' not in ctx and 'removed' not in ctx.lower():
            issues.append('getEvapRate in arch but not marked as deleted (removed S20)')

    return issues

def check_session_fields(arch, game_js):
    issues = []
    required_fields = ['pAcid', 'bornTs', 'emergencyKarmaPot', 'visibilitychange']
    for f in required_fields:
        if f in game_js and f not in arch:
            issues.append(f'Session field {f} in game.js but missing from arch')

    # pooled should NOT be in saveSession fields list
    if 'Fields:' in arch:
        fields_idx = arch.index('Fields:')
        fields_ctx = arch[fields_idx:fields_idx+300]
        if 'pooled' in fields_ctx and 'runtime' not in fields_ctx:
            issues.append('pooled still in saveSession fields — was removed S20')

    return issues

def check_open_issues(arch):
    """Check that closed issues aren't still listed as open P1."""
    issues = []
    closed_in_s20 = ['ISS-14', 'ISS-13 Bug B', 'ISS-13 Bug C']

    # Check open issues table
    if '## Known Issues' in arch:
        oi_idx = arch.index('## Known Issues')
        oi_section = arch[oi_idx:oi_idx+1000]
        for closed in closed_in_s20:
            if closed in oi_section and 'Closed' not in oi_section[:oi_section.find(closed)+50]:
                if f'| {closed} |' in oi_section or f'| {closed.split()[0]} |' in oi_section:
                    issues.append(f'{closed} still in open issues table — was closed S20')

    return issues

def check_priority_queue(arch):
    issues = []
    stale_p1 = [
        ('START HERE: ISS-14', 'ISS-14 fixed S20'),
        ('START HERE: ISS-13', 'ISS-13 Bugs B+C fixed S20 — only Bug A needs verify'),
    ]
    for marker, reason in stale_p1:
        if marker in arch:
            issues.append(f'Priority queue stale: {reason}')

    # PERF-1 should be P1
    if 'PERF-1' not in arch or 'P1' not in arch[arch.find('Priority Queue') if 'Priority Queue' in arch else 0:]:
        issues.append('PERF-1 not listed as P1 in priority queue')

    return issues

def check_line_counts(arch, main_tsx, game_js):
    issues = []
    actual_main = len(main_tsx.splitlines())
    actual_game = len(game_js.splitlines())

    m = re.search(r'main\.tsx.*?~?(\d+)\s*lines', arch)
    if m:
        claimed = int(m.group(1))
        if abs(claimed - actual_main) > 50:
            issues.append(f'main.tsx line count: arch claims ~{claimed}, actual {actual_main}')

    m = re.search(r'game\.js.*?~?(\d+)\s*lines', arch)
    if m:
        claimed = int(m.group(1))
        if abs(claimed - actual_game) > 100:
            issues.append(f'game.js line count: arch claims ~{claimed}, actual {actual_game}')

    return issues, actual_main, actual_game

def check_preview_card(arch, main_tsx):
    issues = []
    if 'buildBgDataUrl' in main_tsx:
        if 'Animated' not in arch and 'animated' not in arch:
            issues.append('Preview card described as static but buildBgDataUrl is in main.tsx — it\'s animated')
        if 'preview-bg.png" imageWidth' in arch and 'url={bgUrl}' not in arch:
            issues.append('Preview card shows static zstack — should show animated bgUrl version')
    return issues

# ── Auto-fix ──────────────────────────────────────────────────────────────────

def apply_fixes(arch, fixes, actual_main, actual_game):
    """Apply auto-fixable issues directly to the arch string."""
    changed = []

    for fix in fixes:
        if fix[0] == 'session':
            old_s, new_s = fix[1], fix[2]
            arch = re.sub(
                r'(Session\s+)' + str(old_s),
                r'\g<1>' + str(new_s),
                arch
            )
            changed.append(f'Session {old_s} → {new_s}')

        elif fix[0] == 'devvit':
            old_v, new_v = fix[1], fix[2]
            arch = arch.replace(f'Devvit {old_v}', f'Devvit {new_v}')
            changed.append(f'Devvit version {old_v} → {new_v}')

    # Always fix line counts if off
    m_main = re.search(r'(main\.tsx\s+.*?~?)(\d+)(\s*lines)', arch)
    if m_main:
        claimed = int(m_main.group(2))
        if abs(claimed - actual_main) > 50:
            arch = arch[:m_main.start(2)] + str(actual_main) + arch[m_main.end(2):]
            changed.append(f'main.tsx lines {claimed} → {actual_main}')

    m_game = re.search(r'(game\.js\s+.*?~?)(\d+)(\s*lines)', arch)
    if m_game:
        claimed = int(m_game.group(2))
        if abs(claimed - actual_game) > 100:
            arch = arch[:m_game.start(2)] + str(actual_game) + arch[m_game.end(2):]
            changed.append(f'game.js lines {claimed} → {actual_game}')

    return arch, changed

# ── Post-session update ───────────────────────────────────────────────────────

def post_session_update(arch, audit, session_num, devvit_version, what_shipped):
    """
    Called after a session to:
    1. Bump session number
    2. Update priority queue based on what shipped
    3. Update header
    Returns updated arch string.
    """
    # Bump session in header
    arch = re.sub(
        r'(> Last updated:.*?Session\s+)(\d+)',
        lambda m: m.group(1) + str(session_num),
        arch
    )
    # Update devvit version in header
    arch = re.sub(r'(Devvit\s+)[\d.]+', r'\g<1>' + devvit_version, arch)
    # Update date
    today = datetime.now().strftime('%Y-%m-%d')
    arch = re.sub(r'(> Last updated:\s*)[\d-]+', r'\g<1>' + today, arch)

    return arch

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Wigglers Room Session Health Check')
    parser.add_argument('--token', required=True, help='GitHub PAT')
    parser.add_argument('--fix', action='store_true', help='Auto-fix stale data and push')
    parser.add_argument('--post-session', action='store_true', help='Run end-of-session update')
    parser.add_argument('--session', type=int, help='New session number (for --post-session)')
    parser.add_argument('--devvit', help='Current Devvit version (for --post-session)')
    args = parser.parse_args()

    token = args.token

    print(f'\n{"="*60}')
    print(f'  WIGGLERS ROOM — SESSION HEALTH CHECK')
    print(f'  {datetime.now().strftime("%Y-%m-%d %H:%M")}')
    print(f'{"="*60}\n')

    # Pull files
    print('Pulling live files from GitHub...')
    try:
        arch,    arch_sha    = gh_get(token, 'GAME_ARCHITECTURE.md')
        audit,   audit_sha   = gh_get(token, 'WIGGLERS_AUDIT.md')
        main_tsx, _          = gh_get(token, 'src/main.tsx')
        game_js, _           = gh_get(token, 'webroot/game.js')
        devvit_yaml, _       = gh_get(token, 'devvit.yaml')
        Path('/tmp/sh_devvit.yaml').write_text(devvit_yaml)
        print(f'  ✓ GAME_ARCHITECTURE.md  ({len(arch.splitlines())} lines)')
        print(f'  ✓ WIGGLERS_AUDIT.md     ({len(audit.splitlines())} lines)')
        print(f'  ✓ src/main.tsx          ({len(main_tsx.splitlines())} lines)')
        print(f'  ✓ webroot/game.js       ({len(game_js.splitlines())} lines)')
        print(f'  ✓ devvit.yaml')
    except Exception as e:
        print(f'  ✗ Failed to pull files: {e}')
        sys.exit(1)

    # Run all checks
    all_issues = []

    h_issues, h_fixes = check_header(arch, audit)
    all_issues += h_issues

    g_issues = check_globals(arch, game_js)
    all_issues += g_issues

    msg_issues = check_messages(arch, main_tsx, game_js)
    all_issues += msg_issues

    kv_issues = check_kv_keys(arch, main_tsx)
    all_issues += kv_issues

    sf_issues = check_session_fields(arch, game_js)
    all_issues += sf_issues

    oi_issues = check_open_issues(arch)
    all_issues += oi_issues

    pq_issues = check_priority_queue(arch)
    all_issues += pq_issues

    lc_issues, actual_main, actual_game = check_line_counts(arch, main_tsx, game_js)
    all_issues += lc_issues

    pc_issues = check_preview_card(arch, main_tsx)
    all_issues += pc_issues

    # Report
    if not all_issues:
        print('\n✅ ALL CLEAR — GAME_ARCHITECTURE.md is current')
        print(f'   main.tsx: {actual_main} lines | game.js: {actual_game} lines')

        # Print current P1
        pq_match = re.search(r'START HERE.*?---', arch, re.DOTALL)
        if pq_match:
            p1_lines = pq_match.group(0).strip().split('\n')[:3]
            print(f'\n📋 Current P1:')
            for l in p1_lines:
                print(f'   {l.strip()}')
    else:
        print(f'\n⚠️  DRIFT FOUND — {len(all_issues)} issue(s):')
        for i, issue in enumerate(all_issues, 1):
            print(f'  {i}. {issue}')

        if args.fix:
            print('\n🔧 Auto-fixing...')
            updated_arch, fixed = apply_fixes(arch, h_fixes, actual_main, actual_game)
            if fixed:
                commit = gh_put(
                    token, 'GAME_ARCHITECTURE.md', updated_arch, arch_sha,
                    f'Health check auto-fix: {", ".join(fixed)}'
                )
                print(f'  ✓ Pushed fixes — commit {commit}')
                for f in fixed:
                    print(f'     → {f}')
                remaining = [i for i in all_issues if not any(
                    k in i for k in ['Session number', 'Devvit version', 'line count']
                )]
                if remaining:
                    print(f'\n  ⚠️  {len(remaining)} issue(s) need manual attention:')
                    for r in remaining:
                        print(f'     → {r}')
            else:
                print('  No auto-fixable issues found — all need manual attention')
        else:
            print('\nRun with --fix to auto-push fixes for stale session/version/line counts.')
            print('Other issues require manual review.')

    # Post-session mode
    if args.post_session and args.session and args.devvit:
        print(f'\n📝 POST-SESSION UPDATE — Session {args.session}, Devvit {args.devvit}')
        updated = post_session_update(arch, audit, args.session, args.devvit, [])
        commit = gh_put(
            token, 'GAME_ARCHITECTURE.md', updated, arch_sha,
            f'Post-session update: Session {args.session}, Devvit {args.devvit}'
        )
        print(f'  ✓ Pushed — commit {commit}')

    print(f'\n{"="*60}\n')

if __name__ == '__main__':
    main()
```

