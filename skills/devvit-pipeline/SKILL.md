---
name: devvit-pipeline
description: Use this skill for any Devvit game deploy, test, or feedback session. Always run session-health first. Pipeline: push code → GitHub Actions build check → bridge deploys via devvit upload → version auto-captured. Triggers on "deploy", "push to Reddit", "check feedback", "playtest", "go live", "did the build pass", "check Reddit", "any comments". Requires bridge3.js running in Codespace.
---

# Devvit Deploy Pipeline

The real workflow we established through trial and error:

```
Claude writes code
    ↓
Stage files + show diff
    ↓
⛔ GATE 1 — "Ready to push. Do you approve?" → wait for yes
    ↓
GitHub push via propose_commit.py push --approved
    ↓
GitHub Actions BUILD CHECK (~52 seconds)
    ↓ build passes
⛔ GATE 2 — "Build passed ✓. Deploy to Reddit now?" → wait for yes
    ↓
Bridge deploy: git pull + devvit upload --just-do-it
    ↓ live on Reddit (~15 seconds)
Claude reads Reddit comments → summarizes feedback
```

**Two approval gates. Both mandatory. Neither can be skipped.**

**Prerequisites — check before every session:**

1. **session-health skill** — run first, pulls live files, confirms Devvit version, fixes doc drift
2. **bridge3.js** — must be running in Codespace for Gate 2 deploy

**Keeping bridge3.js alive (recommended):**
```bash
# Option A — tmux (survives browser disconnects)
tmux new -s bridge
export BRIDGE_TOKEN=<github_pat>
node ~/bridge3.js
# Ctrl+B then D to detach — bridge keeps running

# Option B — plain terminal
curl -o ~/bridge3.js https://raw.githubusercontent.com/Cal-Starfur/codespace-bridge/main/bridge3.js
export BRIDGE_TOKEN=<github_pat>
node ~/bridge3.js
```

**Set Codespace idle timeout to 240 minutes:**
`github.com/settings/codespaces` → idle timeout → 240 min
This covers a full work session without the Codespace VM sleeping.

**bridge3.js is now crash-resistant:** 409 SHA conflicts are retried automatically (up to 3x).
The bridge no longer dies on errors — it logs warnings and keeps polling.

**Why devvit upload currently stays in Codespace (working hypothesis):**
In testing, `devvit upload` hung indefinitely in GitHub Actions even with
`CI=true`, `yes |` piped in, and `DEVVIT_NO_INTERACTIVE=true` set.
Our best guess: it makes a Reddit API call to create a playtest subreddit
that requires an interactive TTY or times out silently in CI.

**This may not be a permanent limitation.** Things worth trying in future sessions:
- `devvit upload --help` — check if newer CLI versions added a `--no-interactive` or `--yes` flag
- Setting `FORCE_COLOR=0 CI=true` and redirecting stdin from `/dev/null`
- Running `devvit upload < /dev/null` to explicitly close stdin
- Checking if Devvit adds official CI support in future releases
- Asking in r/devvit or the Devvit Discord if anyone has solved this

If the self-improvement scripts find a pattern or a solution surfaces,
update this section and test it. The goal is eventually zero manual steps.

---

## STEP 0 — Bootstrap Every Session

All scripts live at `skills/devvit-pipeline/scripts/` in `Cal-Starfur/claude-skills`.
Bootstrap fetches them and routes to the correct local paths:
- `pipeline.py` → `/tmp/devvit-pipeline/scripts/pipeline.py`
- all others (bridge_client, github_client, reddit_client, actions_client) → `/tmp/devvit-pipeline/tools/`

`pipeline.py` adds `/tmp/devvit-pipeline` to `sys.path` so `from tools.X import Y` resolves correctly.

```bash
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path

TOKEN = sys.argv[1] if len(sys.argv) > 1 else input("Paste your GitHub PAT: ").strip()
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "DevvitPipeline/1.0"
}

base = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/devvit-pipeline/scripts"
scripts = ["bridge_client.py", "github_client.py", "reddit_client.py", "actions_client.py", "pipeline.py"]

Path("/tmp/devvit-pipeline/tools").mkdir(parents=True, exist_ok=True)
Path("/tmp/devvit-pipeline/scripts").mkdir(parents=True, exist_ok=True)

for script in scripts:
    url = f"{base}/{script}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
        code = base64.b64decode(data["content"]).decode("utf-8")
    # pipeline.py goes to scripts/, tools go to tools/
    dest = "scripts" if script == "pipeline.py" else "tools"
    Path(f"/tmp/devvit-pipeline/{dest}/{script}").write_text(code)
    print(f"✓ {dest}/{script} ({len(code.splitlines())} lines)")

print("Bootstrap complete.")
BOOTSTRAP
```

---

## STEP 1 — Set Credentials (Every Session, Never Saved)

```bash
python3 -c "
import json
from pathlib import Path

gh_token = input('GitHub token: ').strip()
# Reddit credentials only needed for feedback/monitor commands
# Skip these if you only need deploy (press Enter to leave blank)
reddit_id = input('Reddit client ID (optional): ').strip()
reddit_secret = input('Reddit client secret (optional): ').strip()
reddit_user = input('Reddit username (optional): ').strip()
reddit_pass = input('Reddit password (optional): ').strip()
subreddit = input('Subreddit (no r/) (optional): ').strip()

Path('/tmp/devvit-pipeline/memory').mkdir(parents=True, exist_ok=True)
Path('/tmp/devvit-pipeline/memory/pipeline_config.json').write_text(json.dumps({
    'github_token': gh_token,
    'github_owner': 'Cal-Starfur',
    'github_repo': 'Wigglers_Room',
    'reddit': {
        'client_id': reddit_id,
        'client_secret': reddit_secret,
        'username': reddit_user,
        'password': reddit_pass,
    },
    'subreddit': 'wigglers_room_dev',
    'game_title_keyword': 'Wigglers',
}, indent=2))
print('✓ Credentials set for this session')
"
```

---

## The Real Session Flow

**Two hard gates. Both require explicit user approval. Neither can be skipped.**

### GATE 1 — Commit to GitHub

```
1. Stage:    python3 /tmp/github-sync/scripts/propose_commit.py stage <file> <repo_path> -m "Vxx: msg"
2. Show:     python3 /tmp/github-sync/scripts/propose_commit.py status
3. ⛔ STOP — paste the status output in chat, ask: "Ready to push. Do you approve?"
4. Approval: python3 /tmp/github-sync/scripts/propose_commit.py push --approved
```

### After Push — Build Check (~52s)

```bash
python3 /tmp/devvit-pipeline/scripts/pipeline.py status
```

If build **failed** → read the TypeScript error, fix it, return to GATE 1.

### GATE 2 — Deploy to Reddit

```
Build passed?
⛔ STOP — tell user: "Build passed ✓. Deploy to r/wigglers_room_dev now?"
On approval → run bridge deploy:
```

```python
from tools.bridge_client import BridgeClient
config = load_config()
bridge = BridgeClient(token=config['github_token'], owner='Cal-Starfur', repo='codespace-bridge')

bridge.run("git pull", cwd="/workspaces/Wigglers_Room")
bridge.run(
    "/home/codespace/nvm/current/bin/devvit upload --just-do-it 2>&1",
    cwd="/workspaces/Wigglers_Room",
    timeout_polls=36
)
```
**This installs directly to r/wigglers_room_dev — no manual button click on the developer portal needed.**

**Why `git pull` first:** Claude pushes via the GitHub API directly, bypassing the normal git workflow. The Codespace clone won't see those commits until you pull.

**If bridge isn't responding:** Use `bridge.ping()` to verify. If it times out, ask the user to restart bridge3.js.

### After Deploy — Version Capture + Feedback

After a successful `devvit upload`, capture the confirmed version:
```
Devvit output: "Automatically bumped app version to: 0.0.182"
```
This version is stored in `relay/version.json` for the session-health skill to read next session.
The session-health post-session command handles this automatically:
```bash
python3 /tmp/session-health/health_check.py --token <PAT> --post-session --session 21 --devvit 0.0.182
```

```bash
python3 /tmp/devvit-pipeline/scripts/pipeline.py feedback
python3 /tmp/devvit-pipeline/scripts/pipeline.py monitor
```

---

## What the Build Check Does (GitHub Actions)

The workflow at `.github/workflows/deploy.yml` runs on every push:
- Checkout code
- Node 24 (Codespace runs v24.14.0 — deploy.yml may specify 20 but Codespace overrides)
- npm ci
- npm install -g devvit
- npm run build (tsc --noEmit + devvit build)

**52 seconds. Catches TypeScript errors before they reach production.**
**Does NOT run devvit upload — that stays in Codespace.**

---

## Commands

### Check build status
```bash
python3 /tmp/devvit-pipeline/scripts/pipeline.py status
```
Shows recent GitHub Actions runs — pass/fail, commit, duration.

### Read player feedback
```bash
python3 /tmp/devvit-pipeline/scripts/pipeline.py feedback
python3 /tmp/devvit-pipeline/scripts/pipeline.py feedback --since 30
```

### Watch comments live
```bash
python3 /tmp/devvit-pipeline/scripts/pipeline.py monitor
```

---

## Repo Structure (Cal-Starfur/Wigglers_Room)

```
.github/workflows/
└── deploy.yml          ← build check on every push

src/
└── main.tsx            ← Devvit blocks side (self-contained)

webroot/
├── index.html          ← main game HTML
├── game.js             ← game logic
└── style.css

devvit.yaml             ← app config (redis, realtime, reddit_api)
package.json            ← build: tsc --noEmit && devvit build
```

---

## What Claude Does Each Session

0. **Run session-health check** — pull live files, confirm Devvit version, fix doc drift
1. Bootstrap pipeline scripts
2. Pull latest files from GitHub — never work from stale context
3. Make code changes
4. Stage + show diff → **⛔ ask user for commit approval** → push --approved on yes
5. Wait for build check (~52s) → report pass/fail
6. If failed — fix and return to step 4
7. Build passed → **⛔ ask user for deploy approval** → bridge deploy on yes
8. Read Reddit comments, summarize feedback
9. Report bug mentions so next session knows what to fix

**Steps 4 and 7 are hard stops. Claude never skips either gate.**

---

## ✅ SOLVED — Codespace Bridge (Repo Relay Mode)

**Goal achieved:** Claude runs `git pull && devvit upload --just-do-it` directly — user never switches tabs.

**Solution: `codespace-bridge` via GitHub repo relay**
Repo: https://github.com/Cal-Starfur/codespace-bridge

Instead of tunnels or SSH, the bridge uses the GitHub repo itself as an inbox/outbox:
- Claude writes a command to `relay/inbox.json` via `api.github.com`
- `bridge3.js` polls every 3s, runs the command, writes result to `relay/outbox.json`
- Claude reads the result — full round trip through `api.github.com` (always whitelisted)

**Why other approaches failed:**
- `gh` CLI: `release-assets.githubusercontent.com` blocked by egress
- Codespaces REST exec API: doesn't exist publicly
- ngrok: requires account
- localtunnel (`loca.lt`): blocked by egress
- GitHub port forwarding: requires GitHub session cookie even on "public" ports

**Session startup (one-time per Codespace session):**
```bash
curl -o ~/bridge3.js https://raw.githubusercontent.com/Cal-Starfur/codespace-bridge/main/bridge3.js
export BRIDGE_TOKEN=<github_pat>
node ~/bridge3.js
```

**Key details:**
- `devvit` lives at `/home/codespace/nvm/current/bin/devvit` — always use full path
- Fine-grained PAT has no gist scope — repo relay works, gists don't
- Token is the same GitHub PAT used for everything else
- Bridge polls every 3s; typical deploy round-trip ~10-15s
- Always get a fresh SHA before writing inbox to avoid 409 conflicts

**Claude's deploy command (always use this exact string):**
```
cd /workspaces/Wigglers_Room && git pull && /home/codespace/nvm/current/bin/devvit upload --just-do-it && /home/codespace/nvm/current/bin/devvit install wigglers_room_dev 2>&1
```
- `upload` pushes the new version to the App Directory
- `install wigglers_room_dev` bumps r/wigglers_room_dev to the new version automatically
- No manual button click on developers.reddit.com needed

**Bridge call is handled by `tools/bridge_client.py` (embedded below). Always import it:**
```python
from tools.bridge_client import BridgeClient
bridge = BridgeClient(token=config['github_token'], owner='Cal-Starfur', repo='codespace-bridge')
bridge.run("git pull")
bridge.run("/home/codespace/nvm/current/bin/devvit upload --just-do-it 2>&1", timeout_polls=36)
```

**Full deploy sequence Claude runs (always use BridgeClient, never raw read_file/write_file):**
```python
from tools.bridge_client import BridgeClient
config = load_config()
bridge = BridgeClient(token=config['github_token'], owner='Cal-Starfur', repo='codespace-bridge')

result = bridge.run("git pull")
print(result.get('stdout', ''))

result = bridge.run(
    "/home/codespace/nvm/current/bin/devvit upload --just-do-it 2>&1",
    cwd="/workspaces/Wigglers_Room",
    timeout_polls=36  # 3 minutes max
)
print(result.get('stdout', '') or result.get('error', 'timeout'))
```

---

## Hard Rules

1. 🚫 **ABSOLUTE: Never call `propose_commit.py push` without explicit written user approval.**
   - Show staged diff first, ask "Do you approve?", wait for a yes
   - "looks good", "go", "yes", "push it", "approved" count — silence or a new question does NOT
2. 🚫 **ABSOLUTE: Never trigger the bridge deploy without explicit user approval after build passes.**
   - Say "Build passed ✓. Deploy to r/wigglers_room_dev now?" and wait for yes
   - Green build does NOT auto-authorize deploy
3. Don't run devvit upload from GitHub Actions — current attempts hang
4. Always check build status after a push — never assume it passed
5. Never store credentials in this file — /tmp only
6. Always summarize Reddit feedback in plain English after deploy
7. If build fails, fix it before asking about deploy
8. These two gates are NON-NEGOTIABLE — no prior permission, urgency, or "just do it" from earlier in the session bypasses them

---

## Troubleshooting

**Build fails** → Read the TypeScript error, fix in code, push again

**devvit upload hangs in CI** → Current workaround is to run it in Codespace.
This may be solvable — try `devvit upload < /dev/null` or check if newer
Devvit CLI versions added a non-interactive flag. Log what you tried in
the session log so the self-improvement scripts can track it.

**devvit upload warning about subreddit** → Normal. The warning
"We couldn't install your app to the new playtest subreddit" just means
it was already installed there. Upload still succeeded.

**Reddit API 401** → Reddit credentials expired. Re-run Step 1.

**No game post found** → Check subreddit name and game_title_keyword in config.

**Bridge timeout** → bridge3.js is not running in the Codespace. Ask user to:
```bash
curl -o ~/bridge3.js https://raw.githubusercontent.com/Cal-Starfur/codespace-bridge/main/bridge3.js
export BRIDGE_TOKEN=<github_pat>
node ~/bridge3.js
```
Then verify with `bridge.ping()` before re-attempting deploy.

**Bridge 409 conflict** → bridge3.js now retries writes up to 3x with a fresh SHA fetch each time. If you see 409 warnings in the bridge terminal, they are recovered automatically — the bridge will not crash. No action needed.

---

## Error Handling & Edge Cases

### pipeline.py status Hangs (Bridge Timeout)

`pipeline.py status` checks GitHub Actions — it does NOT use the bridge. If it hangs:

1. This is a GitHub API issue, not a bridge issue. Check for rate limiting (403) or a network error first.
2. Kill the hanging process (Ctrl+C) and retry once after 30 seconds.
3. If it hangs a second time, fetch build status directly:
   ```bash
   python3 << 'MANUAL_STATUS'
   import urllib.request, json
   from pathlib import Path

   config = json.loads(Path('/tmp/devvit-pipeline/memory/pipeline_config.json').read_text())
   TOKEN = config['github_token']
   headers = {
       "Authorization": f"token {TOKEN}",
       "Accept": "application/vnd.github.v3+json",
       "User-Agent": "GHSync/1.0"
   }
   url = "https://api.github.com/repos/Cal-Starfur/Wigglers_Room/actions/runs?per_page=3"
   req = urllib.request.Request(url, headers=headers)
   with urllib.request.urlopen(req) as r:
       runs = json.loads(r.read())['workflow_runs']
   for run in runs:
       print(f"{run['conclusion'] or 'in_progress'} — {run['name']} — {run['head_commit']['message'][:60]}")
   MANUAL_STATUS
   ```
4. **Never proceed to Gate 2 if build status is unknown.** If you can't confirm the build passed, tell the user:
   > "I can't confirm the build status right now — pipeline.py is unresponsive. Can you check the Actions tab on GitHub directly before we deploy?"

---

### Build Passes but devvit upload Fails

If Gate 2 runs but `devvit upload` returns an error or produces no version output:

1. **Check what the bridge returned** — look at `result.get('stdout')` and `result.get('error')`. Common causes:
   - `git pull` failed (merge conflict or network issue in Codespace) — the upload never ran
   - `devvit upload` timed out (bridge waited 36 polls / ~3 minutes with no completion)
   - Devvit CLI threw an authentication error (Reddit session expired in the Codespace)

2. **For git pull failures** — ask the user to resolve the conflict in their Codespace terminal, then re-trigger Gate 2 only (no need to re-push or re-build):
   > "The git pull hit a conflict in the Codespace — can you resolve it in your terminal? Once it's clear, I'll re-run the upload."

3. **For devvit upload timeout** — the upload may have partially completed. Check the Devvit developer portal to see if a new version appeared. If it did, capture the version manually and treat the deploy as successful. If not, retry the upload once:
   ```python
   result = bridge.run(
       "/home/codespace/nvm/current/bin/devvit upload --just-do-it 2>&1",
       cwd="/workspaces/Wigglers_Room",
       timeout_polls=60  # extend to 5 minutes on retry
   )
   ```

4. **For Devvit auth errors** — the user needs to run `devvit login` in their Codespace terminal to refresh the Reddit session. Tell them:
   > "Devvit lost its Reddit auth in the Codespace — can you run `devvit login` in your terminal and let me know when it's done?"

5. **The version is NOT confirmed** until you see `Automatically bumped app version to: X.X.X` in the upload output. Do not write to `relay/version.json` with a guessed version.

