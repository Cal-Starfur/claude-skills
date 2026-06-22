---
name: session-health
description: Load this skill at the start of EVERY Wigglers Room session, before touching any code. Runs an automated health check that pulls live files from GitHub, cross-checks GAME_ARCHITECTURE.md against the actual code, reports any drift, and auto-fixes stale session numbers, Devvit versions, and line counts. If bridge3.js is offline, displays the start command and waits up to 5 minutes for it to come online — Claude never asks the user to re-run, it polls automatically. Also runs a post-session update to keep all docs current after code changes ship. Triggers when the user says anything about Wigglers Room, game.js, PERF-1, the audit, or starting a new session. This is the agent that keeps all the docs honest so Claude never works from stale information.
---

## ⚠ MANDATORY — After ANY Change to This Skill

**Every time this skill's health_check.py or SKILL.md is modified:**
1. Write the updated skill to `/mnt/user-data/outputs/SKILL.md`
2. Call `present_files` immediately — no exceptions, no waiting to be asked

```bash
# Always run this after patching:
python3 -c "
from pathlib import Path
skill = Path('/mnt/skills/user/session-health/SKILL.md').read_text()
Path('/mnt/user-data/outputs/SKILL.md').write_text(skill)
print('✓ Skill ready for Save Skill button')
"
```

This is not optional. If you pushed a patch and did not present_files, you broke the workflow.

---

# Session Health Agent — Wigglers Room

**Runs at the start of every session. No exceptions.**
Never touch code until this clears.

---

## What it does

- Pulls `GAME_ARCHITECTURE.md`, `WIGGLERS_AUDIT.md`, `main.tsx`, `game.js`, `devvit.yaml` fresh
- Checks 9 categories of drift against live code
- Auto-fixes: session number, Devvit version, line counts
- Bridge offline = **warning only**, session proceeds — version confirms after first upload
- Flags critical drift (would cause bad edits) separately from informational warnings
- Auto-fixes: session number, Devvit version from relay/version.json, line counts
- Version captured automatically from `devvit upload` stdout → stored in relay/version.json
- After session: bumps session number, Devvit version, updates priority queue

---

## EMBEDDED SCRIPT LOCATION

The health check script lives at:
**`skills/session-health/scripts/health_check.py`** in the `Cal-Starfur/claude-skills` repo.

Bootstrap fetches it from GitHub each session (pass your PAT as TOKEN):

```bash
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path

TOKEN = sys.argv[1] if len(sys.argv) > 1 else input("Paste your GitHub PAT: ").strip()
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "SessionHealth/1.0"
}

url = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/session-health/scripts/health_check.py"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())
    script = base64.b64decode(data["content"]).decode("utf-8")

target = Path("/tmp/session-health/health_check.py")
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(script)
print(f"✓ health_check.py ({len(script.splitlines())} lines)")
print("Bootstrap complete.")
BOOTSTRAP
```

---

```bash
python3 /tmp/session-health/health_check.py --token <PAT> --fix
```

- `--fix` auto-pushes corrections for session number, Devvit version, line counts
- If bridge is offline: displays start command, then **waits up to 5 minutes polling every 15s**
- Claude never asks the user to re-run — it detects the bridge coming online automatically
- All-clear → proceed to code work
- Hard fail (bridge never came up) → version unconfirmed, doc fixes still applied

**Token:** use the same GitHub PAT as github-sync — never store it

**After every `devvit upload`:** the version is captured from stdout and stored in
`relay/version.json` in the codespace-bridge repo. The health check reads it from
there — no manual version tracking needed. Pattern it watches for:
`Automatically bumped app version to: X.X.X`

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

