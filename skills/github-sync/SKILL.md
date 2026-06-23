---
name: github-sync
description: Use when ready to push to GitHub — stage changes, show diff, get approval, push. Also use to read fresh files from GitHub on demand. Bootstrap scripts ONLY when a push is imminent, not at session start. Session start is SESSION_MANIFEST.md only.
version: 2.0.0
---

# GitHub Sync Skill

Full read/write access to GitHub. Workflow: stage → show proposal → wait for approval → push.
**Never push without approval. Never skip the diff.**
**Never store tokens in skill files, game files, or any committed file.**
**Do not bootstrap at session start. Bootstrap only when ready to push.**

---

## When to Bootstrap (pre-push only)

Bootstrap the three scripts only when you're about to stage and push something:

```python
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path

TOKEN = "your_pat_here"
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GHSync/1.0"
}

base = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/github-sync/scripts"
scripts = {
    "tools/github_client.py":      "github_client.py",
    "scripts/propose_commit.py":   "propose_commit.py",
    "scripts/sync_from_github.py": "sync_from_github.py",
}

for local_path, remote_name in scripts.items():
    url = f"{base}/{remote_name}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        code = base64.b64decode(data["content"]).decode("utf-8")
    target = Path(f"/tmp/github-sync/{local_path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(code)
    print(f"✓ {local_path} ({len(code.splitlines())} lines)")

print("Bootstrap complete.")
BOOTSTRAP
```

Then configure token and repo:

```python
python3 -c "
import json
from pathlib import Path
token = 'your_pat_here'
Path('/tmp/github-sync/memory').mkdir(parents=True, exist_ok=True)
Path('/tmp/github-sync/memory/github_config.json').write_text(json.dumps({
    'token': token,
    'owner': 'Cal-Starfur',
    'repo': 'Wigglers_Room',
    'branch': 'main'
}, indent=2))
print('✓ Token set')
"
```

Token lives only in `/tmp` — clears when session ends. Never commit it.

---

## Wigglers Room Config

- **Owner:** Cal-Starfur
- **Repo:** Wigglers_Room
- **Branch:** main

---

## The Approve-Before-Push Workflow

**4 steps. Always in this order. No exceptions.**

```
STEP 1 — Stage the file(s)
STEP 2 — Show status (paste output in chat)
STEP 3 — Ask for approval. STOP. Wait for user reply.
STEP 4 — Push ONLY after explicit approval
```

```bash
# Stage
python3 /tmp/github-sync/scripts/propose_commit.py stage \
  /path/to/local/file repo/path/to/file \
  --message "V25: description of change"

# Show proposal (always show this before asking for approval)
python3 /tmp/github-sync/scripts/propose_commit.py status

# Push (only after user says yes/go/approve/do it)
python3 /tmp/github-sync/scripts/propose_commit.py push --approved

# Full diff (show if user asks or files are large)
python3 /tmp/github-sync/scripts/propose_commit.py diff

# Cancel
python3 /tmp/github-sync/scripts/propose_commit.py clear
```

**Approval words:** "yes", "go", "push it", "approved", "looks good", "do it", "go ahead"  
**Not approval:** silence, a new request, a question

---

## Reading from GitHub (no bootstrap needed)

Single-file reads can be done with raw Python — no scripts required:

```python
python3 << 'READ'
import urllib.request, json, base64
TOKEN = "your_pat_here"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GHSync/1.0"}
url = "https://api.github.com/repos/Cal-Starfur/Wigglers_Room/contents/PATH/TO/FILE"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
print(base64.b64decode(data["content"]).decode("utf-8"))
READ
```

If you need `sync_from_github.py` for multi-file syncing, bootstrap first.

---

## Session End — Offer (not mandatory, not automatic)

After the last push of a code session, offer (do not force):
- "Want a session summary before we wrap up?"
- If 2+ tasks completed: "Want me to sync the calendar?"

These are offers. The user decides. Do not inject them if the session was design/doc-only.

---

## Commit Message Format

```
V25: plain English — what changed and why

Examples:
  V25: fix mobile touch targets on btn-s (min 44px)
  V25: update SESSION_MANIFEST.md active context to Session 25
```

---

## Hard Rules

1. 🚫 Never call `push --approved` without explicit written approval in the current turn
2. Always show `status` output before asking for approval
3. Always include session number in commit messages
4. Never store token in any committed file
5. 🚫 Do not bootstrap at session start — only when a push is imminent
6. If pushing a SKILL.md: write to `/mnt/user-data/outputs/SKILL.md` and call `present_files` after

---

## Troubleshooting

- **401** → Token expired. Re-set it. Staged changes survive.
- **404** → Wrong path. Use raw Python to list: `GET /repos/Owner/Repo/contents/`
- **422** → SHA mismatch. Fetch the file fresh with `--fresh`, clear staged, re-stage.
