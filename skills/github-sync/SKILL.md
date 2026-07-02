---
name: github-sync
description: Minimal local bootstrap — use this to reach GitHub before anything else is loaded. Contains: the bootstrap snippet to fetch push scripts, the token-set pattern, and the approve-before-push workflow. Full skill (troubleshooting, reading patterns, session-end offers) lives in the repo at skills/github-sync/SKILL.md — fetch that if you need it.
version: 2.1.0-local
---

# GitHub Sync — Local Bootstrap

This file exists locally so Claude can reach GitHub even before any repo skills are loaded.
**Do not expand this file.** Full skill lives in `Cal-Starfur/claude-skills/skills/github-sync/SKILL.md`.

---

## Step 1 — Read any file from any repo (no scripts needed)

```python
python3 << 'READ'
import urllib.request, json, base64
TOKEN = "your_pat_here"
OWNER = "Cal-Starfur"
REPO  = "Wigglers_Room"       # ← swap as needed: claude-skills, Vector-Studio, etc.
PATH  = "path/to/file.md"     # ← swap as needed
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GHSync/1.0"}
url = f"https://api.github.com/repos/{OWNER}/{REPO}/contents/{PATH}"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
print(base64.b64decode(data["content"]).decode("utf-8"))
READ
```

Same pattern works for any repo — swap OWNER, REPO, PATH.

---

## Step 2 — Fetch any skill from claude-skills (no scripts needed)

```python
python3 << 'FETCH'
import urllib.request, json, base64
TOKEN = "your_pat_here"
SKILL = "skills/user/lead-dev/SKILL.md"  # ← swap path as needed
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GHSync/1.0"}
url = f"https://api.github.com/repos/Cal-Starfur/claude-skills/contents/{SKILL}"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
print(base64.b64decode(data["content"]).decode("utf-8"))
FETCH
```

---

## Step 3 — Bootstrap push scripts (pre-push only, not at session start)

Only run this when ready to stage and push something:

```python
python3 << 'BOOTSTRAP'
import urllib.request, json, base64
from pathlib import Path
TOKEN = "your_pat_here"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GHSync/1.0"}
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
    print(f"✓ {local_path}")
print("Bootstrap complete.")
BOOTSTRAP
```

Then set token and target repo:

```python
python3 -c "
import json
from pathlib import Path
token = 'your_pat_here'
owner = 'Cal-Starfur'
repo  = 'Wigglers_Room'   # ← swap as needed: claude-skills, Vector-Studio, etc.
Path('/tmp/github-sync/memory').mkdir(parents=True, exist_ok=True)
Path('/tmp/github-sync/memory/github_config.json').write_text(json.dumps({
    'token': token,
    'owner': owner,
    'repo':  repo,
    'branch': 'main'
}, indent=2))
print(f'✓ Token set — {repo}')
"
```

Token lives only in `/tmp` — clears when session ends. Never commit it.

---

## Approve-Before-Push Workflow

```
STEP 1 — Stage
STEP 2 — Show status (paste in chat)
STEP 3 — Ask for approval. STOP.
STEP 4 — Push only after explicit approval.
```

```bash
python3 /tmp/github-sync/scripts/propose_commit.py stage \
  /path/to/local/file repo/path/to/file \
  --message "V25: what changed and why"

python3 /tmp/github-sync/scripts/propose_commit.py status

# After approval:
python3 /tmp/github-sync/scripts/propose_commit.py push --approved
```

**Approval:** "yes", "go", "push it", "do it", "approved", "looks good", "go ahead"
**Not approval:** silence, a question, a new request

---

## Hard Rules

1. 🚫 Never push without explicit approval in the current turn
2. Always show `status` before asking for approval
3. 🚫 Do not bootstrap scripts at session start — only when a push is imminent
4. Never store token in any committed file
5. Token lives in `/tmp` only — clears when session ends
6. After pushing a SKILL.md: write to `/mnt/user-data/outputs/SKILL.md` and call `present_files`

---

## Troubleshooting

- **401** → Token expired. Re-set it. Staged changes survive.
- **404** → Wrong path. List contents: `GET /repos/Owner/Repo/contents/`
- **422** → SHA mismatch. Fetch file fresh, clear staged, re-stage.

For anything else → fetch full skill from repo:
`Cal-Starfur/claude-skills/skills/github-sync/SKILL.md`
