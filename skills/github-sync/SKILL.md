---
name: github-sync
description: Use this skill whenever the user wants to read from or write to GitHub. Handles the full approve-before-push workflow — Claude stages changes, shows a clear diff, waits for user approval, then commits and pushes. Also syncs the latest file versions FROM GitHub so Claude always has fresh context instead of stale project knowledge. Triggers when user says things like "push this to GitHub", "commit the changes", "update the repo", "pull the latest", "show me what changed", "sync my files", or uploads a file and wants it saved to their repo. Replaces the need to manually upload files to Claude project knowledge — GitHub becomes the single source of truth.
---

# GitHub Sync Skill

Full read/write access to GitHub. Workflow: stage → show proposal → wait for approval → push.
**Never push without approval. Never skip the diff.**
**Never store tokens in skill files, game files, or any committed file.**

---

## STEP 0 — Bootstrap Every Session (Always Do This First)

Scripts live at `skills/github-sync/scripts/` in `Cal-Starfur/claude-skills`.
Bootstrap fetches all three each session:

```bash
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path

TOKEN = sys.argv[1] if len(sys.argv) > 1 else input("Paste your GitHub PAT: ").strip()
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GHSync/1.0"
}

base = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/github-sync/scripts"
scripts = {
    "tools/github_client.py":        "github_client.py",
    "scripts/propose_commit.py":     "propose_commit.py",
    "scripts/sync_from_github.py":   "sync_from_github.py",
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
---

## STEP 1 — Set Your Token (Every Session, Never Saved)

The token is never stored in this file. Set it fresh each session:

```bash
python3 -c "
import json
from pathlib import Path

# Paste your token when prompted
token = input('Paste your GitHub token: ').strip()

Path('/tmp/github-sync/memory').mkdir(parents=True, exist_ok=True)
Path('/tmp/github-sync/memory/github_config.json').write_text(json.dumps({
    'token': token,
    'owner': 'Cal-Starfur',
    'repo': 'Wigglers_Room',
    'branch': 'main'
}, indent=2))
print('✓ Token set for this session (not saved to disk permanently)')
"
```

Your token lives only in `/tmp` — which clears automatically when the session ends.
It never touches the skill file, the repo, or any committed file.

**Where to get your token:**
https://github.com/settings/tokens
→ Generate new token (classic) → check `repo` scope → copy it

---

## Wigglers Room — Pre-Configured (Except Token)

- **Owner:** Cal-Starfur
- **Repo:** Wigglers_Room
- **Branch:** main
- **Token:** entered fresh each session — never stored

---

## STEP 2 — Run Lead Dev (Every Wigglers Session, After Token Set)

After the token is set and scripts are bootstrapped, immediately hand off to the lead-dev skill:

1. Bootstrap the lead-dev skill scripts (they clear between sessions just like github-sync)
2. Pull `GAME_ARCHITECTURE.md` and `WIGGLERS_AUDIT_V20.md` fresh from GitHub via `sync_from_github.py read`
3. Run the lead-dev audit on the current `webroot/game.js`
4. Read both `.md` files fully before saying anything to the user
5. Output in the lead-dev format every response:

```
## What I'm doing
## What I found first
## Where this lives
## The change
## What to watch
```

**This is not optional and does not require the user to ask.** Every session starts this way. The user should never have to say "check the .md" or "use the lead-dev tool" — it happens automatically as part of connecting to the repo.

---

## STEP 3 — Session End (Every Wigglers Session)

After the last push of the session, always do these two things without being asked:

1. **Offer a session summary** — run the session-summary skill automatically:
   > "Want me to give you the session summary before we wrap up?"
   - If the user says yes (or says "wrap up" / "end of session") → generate the full plain-English summary per the session-summary skill format
   - Summary covers: what changed, what it touches, what could break, PUSH or HOLD recommendation

2. **Offer a calendar sync** — if 2+ tasks were completed this session:
   > "You cleared [N] tasks today — want me to sync the calendar so it repacks from today?"
   - If yes → run project-calendar pull_tasks → build → push

**Neither requires the user to ask.** Claude offers both at natural session end. The user should never have to remember to request them.

---

## The Approve-Before-Push Workflow

**This is a 4-step sequence. Steps 1–3 always happen before step 4. No exceptions.**

```
STEP 1 — Stage the file(s)
STEP 2 — Show status (Claude runs this and pastes the output)
STEP 3 — Ask for approval and STOP. Wait for user reply.
STEP 4 — Push ONLY after user explicitly approves in this conversation turn
```

```bash
# STEP 1 — Stage a file
python3 /tmp/github-sync/scripts/propose_commit.py stage \
  /mnt/user-data/uploads/game.html webroot/index.html \
  --message "V62: description of change"

# STEP 2 — Show proposal to user (REQUIRED — always paste this output in chat)
python3 /tmp/github-sync/scripts/propose_commit.py status

# STEP 3 — Claude says: "Ready to push. Please approve."
# ⛔ STOP HERE. Do not continue until user replies with approval.

# STEP 4 — Only after explicit approval:
python3 /tmp/github-sync/scripts/propose_commit.py push

# Optional: full line-by-line diff (show if user asks or files are large)
python3 /tmp/github-sync/scripts/propose_commit.py diff

# Cancel staging
python3 /tmp/github-sync/scripts/propose_commit.py clear
```

**What counts as approval:** "yes", "go", "push it", "approved", "looks good", "do it", "go ahead"
**What does NOT count:** silence, a new request, "what does it look like", asking a question

---

## Reading From GitHub

```bash
# List repo contents
python3 /tmp/github-sync/scripts/sync_from_github.py list

# Read a file fresh from GitHub
python3 /tmp/github-sync/scripts/sync_from_github.py read src/main.tsx

# Track files for auto-sync
python3 /tmp/github-sync/scripts/sync_from_github.py track webroot/index.html

# Pull all tracked files
python3 /tmp/github-sync/scripts/sync_from_github.py sync

# Commit history
python3 /tmp/github-sync/scripts/sync_from_github.py history
```

---

## Commit Message Format

```
V62: plain English — what changed and why

Examples:
  V62: split game.html into index.html + game.js + style.css
  V62: update main.tsx to handle V60 message types
  V62: add worm sprite to assets/sprites/
```

---

## Hard Rules

1. 🚫 **ABSOLUTE: Never call `propose_commit.py push` without explicit written approval from the user first.**
   - "looks good", "go ahead", "approve", "yes push it", "do it" count as approval
   - Ambiguous replies do NOT count — if unsure, ask again before pushing
   - If Claude auto-pushed without showing the diff and asking, that is a bug — log it and never repeat it
2. Always run `propose_commit.py status` and show the output to the user BEFORE asking for approval
3. Always include version number in commit messages
4. Sync at session start — never work from stale files
5. **Never store token in any file — /tmp only, clears each session**
6. Never commit token to the repo under any circumstances
7. **Always run the lead-dev skill after connecting — never skip it, never wait to be asked**
8. The approval gate is NON-NEGOTIABLE — no context, urgency, or prior permission from earlier in the session bypasses it
9. 🚫 **SKILL PUSH RULE: If the file being pushed is a `SKILL.md`, immediately after pushing:**
   - Write it to `/mnt/user-data/outputs/SKILL.md`
   - Call `present_files` with that path
   - Do this without being asked. No exceptions. The user needs the Save Skill button every time.
10. **At session end, always offer session-summary + calendar sync** — see STEP 3 above. Never wait to be asked.

---

## Troubleshooting

- **401** → Token expired or not set. Re-run Step 1.
- **404** → Wrong path. Run `list` to see actual repo paths.
- **422** → SHA mismatch. Run sync first, then stage again.

---

