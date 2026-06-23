---
name: session-health
description: Load for Wigglers Room CODE sessions only — when touching game.js, main.tsx, devvit.yaml, or GAME_ARCHITECTURE.md. Runs a targeted health check, pulls fresh docs, and auto-fixes stale session numbers/line counts. Do NOT load at session start for design, marketing, or doc-only work. Session start is always SESSION_MANIFEST.md first — see that file for what to load and when.
version: 2.0.0
---

# Session Health — Wigglers Room

**Load this only when the session involves code changes.**
For design / marketing / doc sessions — read SESSION_MANIFEST.md and stop there.

---

## Session Start (all session types)

One fetch. No scripts. No bootstrap.

```python
python3 << 'START'
import urllib.request, json, base64
TOKEN = "your_pat_here"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "WR/1.0"}
url = "https://api.github.com/repos/Cal-Starfur/Wigglers_Room/contents/SESSION_MANIFEST.md"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
print(base64.b64decode(data["content"]).decode("utf-8"))
START
```

Read the manifest. It tells you what context is active and what skills/files to load for this session's work.

---

## Code Session — Additional Steps (only if touching game.js / main.tsx)

After reading the manifest, if the work involves code:

**Step 1 — Fetch health_check.py**

```python
python3 << 'BOOTSTRAP'
import urllib.request, json, base64
from pathlib import Path
TOKEN = "your_pat_here"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "SessionHealth/1.0"}
url = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/session-health/scripts/health_check.py"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
script = base64.b64decode(data["content"]).decode("utf-8")
target = Path("/tmp/session-health/health_check.py")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(script)
print(f"✓ health_check.py ({len(script.splitlines())} lines)")
BOOTSTRAP
```

**Step 2 — Run health check**

```bash
python3 /tmp/session-health/health_check.py --token <PAT> --fix
```

- `--fix` auto-pushes corrections for session number, Devvit version, line counts
- Bridge offline = warning only, session proceeds
- All-clear → proceed to code work

**Step 3 — Docs are now cached**

```bash
cat /tmp/sh_arch.md    # GAME_ARCHITECTURE.md
cat /tmp/sh_audit.md   # WIGGLERS_AUDIT.md
```

---

## Post-Session Update (code sessions only)

After code ships:

```bash
python3 /tmp/session-health/health_check.py \
  --token <PAT> \
  --post-session \
  --session 25 \
  --devvit 0.0.180
```

Then update SESSION_MANIFEST.md to reflect the new session number and active context.

---

## What Gets Checked

| Category | What it looks for |
|---|---|
| Header | Session number, Devvit version, next P1 — stale? |
| Line counts | main.tsx and game.js — off by >50/100 lines? |
| Message constants | Ghost MSG_* in arch but not in code? |
| Global state | weekStartTs, camX, centreOffsetX, WORLD_W documented? |
| Open issues | Closed issues still listed as P1? |

---

## Repo Config

- **Owner:** Cal-Starfur  
- **Repo:** Wigglers_Room  
- **Branch:** main  
- **Files watched:** GAME_ARCHITECTURE.md, WIGGLERS_AUDIT.md, src/main.tsx, webroot/game.js, devvit.yaml

---

## Error Handling

**401 mid-session:** Stop all API calls. Ask user for fresh PAT. Staged changes in propose_commit.py survive token refresh.

**health_check.py unreachable:** Safe to read/discuss files. Not safe to push code changes or edit arch docs until resolved.

**Bridge offline:** Safe to read, stage, push doc-only changes. Not safe to run devvit upload or bump devvit.yaml version.

Bridge start command (show to user if needed):
```bash
nohup node /workspaces/Wigglers_Room/bridge3.js > /tmp/bridge.log 2>&1 &
```

---

## ⚠ After Modifying This Skill

Write to `/mnt/user-data/outputs/SKILL.md` and call `present_files` so the Save Skill button appears.
