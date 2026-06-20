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

/tmp clears between sessions. Run this to restore all scripts:

```bash
python3 << 'BOOTSTRAP'
import re
from pathlib import Path

skill_path = '/mnt/skills/user/github-sync/SKILL.md'
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

## EMBEDDED SCRIPT: tools/github_client.py
*Write this to `/tmp/github-sync/tools/github_client.py`*

```python
"""
tools/github_client.py — GitHub API Client
Full read/write access to a GitHub repository.

Import:
    from tools.github_client import GitHubClient
    gh = GitHubClient(token='ghp_...', owner='yourname', repo='wigglers')
"""

import json
import base64
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


class GitHubClient:
    """
    Full GitHub REST API client.
    Supports: read files, write files, create branches, open PRs, commit history.
    """

    BASE = 'https://api.github.com'

    def __init__(self, token, owner, repo, default_branch='main'):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.default_branch = default_branch
        self.base_repo = f"{self.BASE}/repos/{owner}/{repo}"

    def _headers(self):
        return {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json',
            'User-Agent': 'LeadDevSkill/1.0',
        }

    def _request(self, method, url, data=None):
        """Make an authenticated GitHub API request."""
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(url, data=body, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read()), resp.status
        except urllib.error.HTTPError as e:
            error_body = {}
            try:
                error_body = json.loads(e.read())
            except:
                pass
            raise GitHubError(e.code, error_body.get('message', str(e)), url)

    # ── Read Operations ────────────────────────────────────────────────────

    def get_file(self, path, branch=None):
        """
        Get file content from repo.
        Returns: {'content': str, 'sha': str, 'path': str, 'size': int}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/contents/{path}?ref={branch}"
        data, _ = self._request('GET', url)
        content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
        return {
            'content': content,
            'sha': data['sha'],
            'path': data['path'],
            'size': data['size'],
            'url': data['html_url'],
        }

    def file_exists(self, path, branch=None):
        """Check if a file exists in the repo."""
        try:
            self.get_file(path, branch)
            return True
        except GitHubError as e:
            if e.status == 404:
                return False
            raise

    def list_files(self, path='', branch=None):
        """
        List files/directories at a path.
        Returns list of {'name', 'path', 'type' (file|dir), 'size'}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/contents/{path}?ref={branch}"
        data, _ = self._request('GET', url)
        if isinstance(data, list):
            return [{'name': f['name'], 'path': f['path'],
                     'type': f['type'], 'size': f.get('size', 0)} for f in data]
        return []

    def get_branch(self, branch=None):
        """Get branch info including latest commit SHA."""
        branch = branch or self.default_branch
        url = f"{self.base_repo}/branches/{branch}"
        data, _ = self._request('GET', url)
        return {
            'name': data['name'],
            'sha': data['commit']['sha'],
            'commit_url': data['commit']['url'],
        }

    def get_commit_history(self, path=None, branch=None, limit=10):
        """
        Get recent commits, optionally for a specific file.
        Returns list of {'sha', 'message', 'author', 'date'}
        """
        branch = branch or self.default_branch
        url = f"{self.base_repo}/commits?sha={branch}&per_page={limit}"
        if path:
            url += f"&path={path}"
        data, _ = self._request('GET', url)
        return [{
            'sha': c['sha'][:7],
            'message': c['commit']['message'].split('\n')[0],
            'author': c['commit']['author']['name'],
            'date': c['commit']['author']['date'][:10],
        } for c in data]

    # ── Write Operations ───────────────────────────────────────────────────

    def write_file(self, path, content, commit_message, branch=None, sha=None):
        """
        Create or update a file in the repo.
        If file exists, sha must be provided (get it from get_file()).
        Returns: {'commit_sha', 'file_url', 'branch'}
        """
        branch = branch or self.default_branch

        # Auto-get SHA if file exists and sha not provided
        if sha is None and self.file_exists(path, branch):
            existing = self.get_file(path, branch)
            sha = existing['sha']

        encoded = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        payload = {
            'message': commit_message,
            'content': encoded,
            'branch': branch,
        }
        if sha:
            payload['sha'] = sha

        url = f"{self.base_repo}/contents/{path}"
        data, _ = self._request('PUT', url, payload)
        return {
            'commit_sha': data['commit']['sha'][:7],
            'file_url': data['content']['html_url'],
            'branch': branch,
            'path': path,
        }

    def delete_file(self, path, commit_message, branch=None):
        """Delete a file from the repo."""
        branch = branch or self.default_branch
        existing = self.get_file(path, branch)
        payload = {
            'message': commit_message,
            'sha': existing['sha'],
            'branch': branch,
        }
        url = f"{self.base_repo}/contents/{path}"
        data, _ = self._request('DELETE', url, payload)
        return {'commit_sha': data['commit']['sha'][:7]}

    # ── Branch Operations ──────────────────────────────────────────────────

    def create_branch(self, branch_name, from_branch=None):
        """Create a new branch from an existing one."""
        from_branch = from_branch or self.default_branch
        source = self.get_branch(from_branch)
        url = f"{self.base_repo}/git/refs"
        payload = {
            'ref': f'refs/heads/{branch_name}',
            'sha': source['sha'],
        }
        try:
            data, _ = self._request('POST', url, payload)
            return {'branch': branch_name, 'sha': source['sha']}
        except GitHubError as e:
            if e.status == 422:  # Branch already exists
                return {'branch': branch_name, 'sha': source['sha'], 'existed': True}
            raise

    def branch_exists(self, branch_name):
        """Check if a branch exists."""
        try:
            self.get_branch(branch_name)
            return True
        except GitHubError as e:
            if e.status == 404:
                return False
            raise

    # ── Pull Request Operations ────────────────────────────────────────────

    def create_pull_request(self, title, body, head_branch, base_branch=None):
        """
        Open a pull request.
        Returns: {'number', 'url', 'title'}
        """
        base_branch = base_branch or self.default_branch
        url = f"{self.base_repo}/pulls"
        payload = {
            'title': title,
            'body': body,
            'head': head_branch,
            'base': base_branch,
        }
        data, _ = self._request('POST', url, payload)
        return {
            'number': data['number'],
            'url': data['html_url'],
            'title': data['title'],
            'state': data['state'],
        }

    def list_pull_requests(self, state='open'):
        """List PRs. state: 'open' | 'closed' | 'all'"""
        url = f"{self.base_repo}/pulls?state={state}&per_page=10"
        data, _ = self._request('GET', url)
        return [{
            'number': pr['number'],
            'title': pr['title'],
            'url': pr['html_url'],
            'branch': pr['head']['ref'],
            'created': pr['created_at'][:10],
        } for pr in data]

    # ── Repo Info ──────────────────────────────────────────────────────────

    def get_repo_info(self):
        """Get basic repo information."""
        data, _ = self._request('GET', self.base_repo)
        return {
            'name': data['name'],
            'description': data.get('description', ''),
            'default_branch': data['default_branch'],
            'private': data['private'],
            'url': data['html_url'],
            'last_push': data['pushed_at'][:10],
        }

    def test_connection(self):
        """Verify credentials and repo access. Returns True or raises."""
        info = self.get_repo_info()
        print(f"✓ Connected to: {self.owner}/{self.repo}")
        print(f"  Branch: {info['default_branch']}")
        print(f"  Last push: {info['last_push']}")
        return True


class GitHubError(Exception):
    def __init__(self, status, message, url=''):
        self.status = status
        self.message = message
        self.url = url
        super().__init__(f"GitHub API {status}: {message}")

```

---

## EMBEDDED SCRIPT: scripts/propose_commit.py
*Write this to `/tmp/github-sync/scripts/propose_commit.py`*

```python
#!/usr/bin/env python3
"""
scripts/propose_commit.py — Commit Proposal Engine
The core of the approve-before-push workflow.

Claude stages changes, shows you exactly what will be committed,
waits for your approval, then pushes.

Usage:
    python3 propose_commit.py stage <file> <repo_path> [--message "why"]
    python3 propose_commit.py status
    python3 propose_commit.py diff
    python3 propose_commit.py push --token <token> --owner <owner> --repo <repo>
    python3 propose_commit.py clear
"""

import sys, json, os, argparse, difflib, hashlib
from pathlib import Path
from datetime import datetime

# Staging area lives in skill memory
STAGING_FILE = Path(__file__).parent.parent / 'memory' / 'staged_commits.json'
CONFIG_FILE = Path(__file__).parent.parent / 'memory' / 'github_config.json'


# ── Config Management ─────────────────────────────────────────────────────

def load_config():
    """Load GitHub config (token, owner, repo)."""
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text())

def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_client(args=None):
    """Get a configured GitHubClient."""
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from tools.github_client import GitHubClient

    config = load_config()

    token = (args and getattr(args, 'token', None)) or config.get('token') or os.environ.get('GITHUB_TOKEN')
    owner = (args and getattr(args, 'owner', None)) or config.get('owner')
    repo  = (args and getattr(args, 'repo', None))  or config.get('repo')
    branch = (args and getattr(args, 'branch', None)) or config.get('branch', 'main')

    if not all([token, owner, repo]):
        raise ValueError(
            "GitHub credentials missing. Run:\n"
            "  python3 propose_commit.py configure --token ghp_... --owner yourname --repo wigglers"
        )

    return GitHubClient(token, owner, repo, branch)


# ── Staging Area ──────────────────────────────────────────────────────────

def load_staged():
    """Load current staging area."""
    if not STAGING_FILE.exists():
        return {'files': [], 'created_at': None}
    return json.loads(STAGING_FILE.read_text())

def save_staged(staged):
    STAGING_FILE.parent.mkdir(parents=True, exist_ok=True)
    STAGING_FILE.write_text(json.dumps(staged, indent=2))

def clear_staged():
    staged = {'files': [], 'created_at': None, 'cleared_at': datetime.now().isoformat()}
    save_staged(staged)
    print("Staging area cleared.")


# ── File Type Handling ────────────────────────────────────────────────────

def get_file_type(filename):
    """Categorize file for display and handling."""
    ext = Path(filename).suffix.lower()
    types = {
        '.html': 'game',
        '.js': 'game',
        '.ts': 'game',
        '.tsx': 'game',
        '.md': 'docs',
        '.json': 'config',
        '.css': 'style',
        '.svg': 'art',
        '.png': 'art',
        '.jpg': 'art',
        '.jpeg': 'art',
        '.gif': 'art',
        '.txt': 'docs',
    }
    return types.get(ext, 'other')

def is_binary(filepath):
    """Check if file is binary (images etc)."""
    binary_exts = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.ttf'}
    return Path(filepath).suffix.lower() in binary_exts

def read_file_content(filepath):
    """Read file content, handling binary files."""
    if is_binary(filepath):
        import base64
        with open(filepath, 'rb') as f:
            return base64.b64encode(f.read()).decode(), True  # content, is_binary
    with open(filepath, encoding='utf-8', errors='replace') as f:
        return f.read(), False


# ── Diff Generation ───────────────────────────────────────────────────────

def generate_diff(old_content, new_content, filename, context=5):
    """Generate a human-readable diff between old and new content."""
    if old_content is None:
        lines_added = len(new_content.split('\n'))
        return f"NEW FILE: {filename}\n+{lines_added} lines added", lines_added, 0

    old_lines = old_content.split('\n')
    new_lines = new_content.split('\n')

    diff = list(difflib.unified_diff(
        old_lines, new_lines,
        fromfile=f'a/{filename}',
        tofile=f'b/{filename}',
        lineterm='',
        n=context
    ))

    added = sum(1 for l in diff if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in diff if l.startswith('-') and not l.startswith('---'))

    return '\n'.join(diff[:100]), added, removed  # cap diff display at 100 lines


def summarize_changes(new_content, old_content, filename):
    """Generate a plain-English summary of what changed."""
    if old_content is None:
        lines = len(new_content.split('\n'))
        return f"New file ({lines} lines)"

    old_lines = set(old_content.split('\n'))
    new_lines = set(new_content.split('\n'))
    added = len(new_lines - old_lines)
    removed = len(old_lines - new_lines)

    ext = Path(filename).suffix.lower()

    if ext in ('.js', '.ts', '.html'):
        # Count function changes
        import re
        old_fns = set(re.findall(r'function\s+(\w+)', old_content))
        new_fns = set(re.findall(r'function\s+(\w+)', new_content))
        added_fns = new_fns - old_fns
        removed_fns = old_fns - new_fns
        fn_summary = ''
        if added_fns:
            fn_summary += f" | +functions: {', '.join(sorted(added_fns)[:5])}"
        if removed_fns:
            fn_summary += f" | -functions: {', '.join(sorted(removed_fns)[:5])}"
        return f"+{added} lines, -{removed} lines{fn_summary}"

    elif ext == '.md':
        import re
        old_headers = re.findall(r'^#+\s+(.+)', old_content, re.MULTILINE)
        new_headers = re.findall(r'^#+\s+(.+)', new_content, re.MULTILINE)
        added_sections = set(new_headers) - set(old_headers)
        if added_sections:
            return f"+{added} lines, -{removed} lines | new sections: {', '.join(list(added_sections)[:3])}"

    return f"+{added} lines, -{removed} lines"


# ── Stage Command ─────────────────────────────────────────────────────────

def cmd_stage(args):
    """Stage a file for commit."""
    local_path = Path(args.file)
    if not local_path.exists():
        # Check uploads folder
        upload_path = Path('/mnt/user-data/uploads') / local_path.name
        if upload_path.exists():
            local_path = upload_path
        else:
            print(f"Error: {args.file} not found")
            sys.exit(1)

    repo_path = args.repo_path
    message = args.message or f"Update {Path(repo_path).name}"
    file_type = get_file_type(repo_path)
    content, binary = read_file_content(local_path)

    # Try to get current version from GitHub for diff
    old_content = None
    old_sha = None
    try:
        gh = get_client(args)
        existing = gh.get_file(repo_path)
        old_content = existing['content']
        old_sha = existing['sha']
    except Exception:
        pass  # New file — that's fine

    # Generate diff summary
    diff_text, lines_added, lines_removed = generate_diff(
        old_content, content if not binary else '[binary file]', repo_path
    )
    change_summary = summarize_changes(
        content if not binary else '[binary]',
        old_content,
        repo_path
    )

    # Add to staging area
    staged = load_staged()
    if staged.get('created_at') is None:
        staged['created_at'] = datetime.now().isoformat()

    # Remove if already staged
    staged['files'] = [f for f in staged['files'] if f['repo_path'] != repo_path]

    staged['files'].append({
        'local_path': str(local_path),
        'repo_path': repo_path,
        'file_type': file_type,
        'message': message,
        'binary': binary,
        'content': content,
        'old_sha': old_sha,
        'is_new': old_content is None,
        'lines_added': lines_added,
        'lines_removed': lines_removed,
        'change_summary': change_summary,
        'staged_at': datetime.now().isoformat(),
        'checksum': hashlib.md5(content.encode()).hexdigest()[:8],
    })
    save_staged(staged)

    print(f"\n✓ Staged: {repo_path}")
    print(f"  Type:    {file_type}")
    print(f"  Changes: {change_summary}")
    print(f"  {'NEW FILE' if old_content is None else 'UPDATE'}")
    print(f"\nRun 'python3 propose_commit.py status' to see all staged files.")


# ── Status Command ────────────────────────────────────────────────────────

def cmd_status(args):
    """Show what's staged and ready to commit."""
    staged = load_staged()
    files = staged.get('files', [])

    print(f"\n{'='*60}")
    print(f"COMMIT PROPOSAL — Staged Changes")
    print(f"{'='*60}")

    if not files:
        print("Nothing staged. Use 'stage' to add files.")
        return

    config = load_config()
    print(f"Repo:   {config.get('owner','?')}/{config.get('repo','?')}")
    print(f"Branch: {config.get('branch','main')}")
    print(f"Staged: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'─'*60}")

    by_type = {}
    for f in files:
        t = f['file_type']
        by_type.setdefault(t, []).append(f)

    type_icons = {'game':'🎮', 'docs':'📄', 'art':'🎨', 'config':'⚙️', 'style':'🎨', 'other':'📦'}
    total_added = sum(f['lines_added'] for f in files)
    total_removed = sum(f['lines_removed'] for f in files)

    for ftype, flist in by_type.items():
        icon = type_icons.get(ftype, '📦')
        print(f"\n{icon} {ftype.upper()} ({len(flist)} files)")
        for f in flist:
            status = '+ NEW' if f['is_new'] else '~ MOD'
            print(f"  {status}  {f['repo_path']}")
            print(f"        {f['change_summary']}")
            print(f"        Commit message: \"{f['message']}\"")

    print(f"\n{'─'*60}")
    print(f"Total: {len(files)} files | +{total_added} lines | -{total_removed} lines")
    print(f"{'='*60}")
    print(f"\nTo push: python3 propose_commit.py push")
    print(f"To see full diff: python3 propose_commit.py diff")
    print(f"To cancel: python3 propose_commit.py clear")


# ── Diff Command ──────────────────────────────────────────────────────────

def cmd_diff(args):
    """Show full diffs for staged files."""
    staged = load_staged()
    files = staged.get('files', [])

    if not files:
        print("Nothing staged.")
        return

    filter_path = getattr(args, 'file', None)

    for f in files:
        if filter_path and filter_path not in f['repo_path']:
            continue
        if f['binary']:
            print(f"\n[Binary file: {f['repo_path']}]")
            continue

        print(f"\n{'='*60}")
        print(f"File: {f['repo_path']}")
        print(f"{'='*60}")

        try:
            gh = get_client(args)
            existing = gh.get_file(f['repo_path'])
            old_content = existing['content']
        except Exception:
            old_content = None

        diff_text, added, removed = generate_diff(
            old_content, f['content'], f['repo_path']
        )
        print(diff_text)
        print(f"\n+{added} lines  -{removed} lines")


# ── Push Command ──────────────────────────────────────────────────────────

def cmd_push(args):
    """Push all staged files to GitHub. Requires --approved flag to prevent accidental pushes."""
    staged = load_staged()
    files = staged.get('files', [])

    if not files:
        print("Nothing staged to push.")
        return

    # ── APPROVAL GATE ─────────────────────────────────────────────────────
    # Claude must pass --approved only after explicit user approval in chat.
    # This flag is the hard enforcement layer — it cannot be bypassed by
    # Claude deciding "the user probably meant yes". If the flag is missing,
    # the push is blocked regardless of any prior instructions.
    approved = getattr(args, 'approved', False)
    if not approved:
        print()
        print("╔══════════════════════════════════════════════════════════╗")
        print("║  ⛔  PUSH BLOCKED — AWAITING EXPLICIT USER APPROVAL      ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print("║                                                          ║")
        print("║  Show the status above to the user and ask:             ║")
        print("║  'Ready to push these files. Do you approve?'           ║")
        print("║                                                          ║")
        print("║  Only after they say yes, run:                          ║")
        print("║  python3 propose_commit.py push --approved              ║")
        print("║                                                          ║")
        print("╚══════════════════════════════════════════════════════════╝")
        print()
        sys.exit(1)

    try:
        gh = get_client(args)
        gh.test_connection()
    except Exception as e:
        print(f"Connection failed: {e}")
        sys.exit(1)

    config = load_config()
    branch = config.get('branch', 'main')

    print(f"\n{'='*60}")
    print(f"PUSHING {len(files)} FILES TO GITHUB")
    print(f"{'='*60}")

    results = []
    errors = []

    for f in files:
        try:
            print(f"\n→ {f['repo_path']}...")
            result = gh.write_file(
                path=f['repo_path'],
                content=f['content'],
                commit_message=f['message'],
                branch=branch,
                sha=f.get('old_sha'),
            )
            results.append({'file': f['repo_path'], 'commit': result['commit_sha'], 'url': result['file_url']})
            print(f"  ✓ Committed: {result['commit_sha']} → {result['file_url']}")
        except Exception as e:
            errors.append({'file': f['repo_path'], 'error': str(e)})
            print(f"  ✗ Failed: {e}")

    print(f"\n{'='*60}")
    print(f"PUSH COMPLETE")
    print(f"  Succeeded: {len(results)}/{len(files)}")
    if errors:
        print(f"  Failed: {len(errors)}")
        for e in errors:
            print(f"    ✗ {e['file']}: {e['error']}")
    print(f"{'='*60}")

    # Log the push
    push_log = {
        'timestamp': datetime.now().isoformat(),
        'branch': branch,
        'files_pushed': len(results),
        'commits': results,
        'errors': errors,
    }
    log_path = Path(__file__).parent.parent / 'memory' / 'push_log.jsonl'
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, 'a') as lf:
        lf.write(json.dumps(push_log) + '\n')

    # Clear staging area after successful push
    if not errors:
        clear_staged()
        print("\nStaging area cleared. Ready for next commit.")

    return results


# ── Configure Command ─────────────────────────────────────────────────────

def cmd_configure(args):
    """Save GitHub config to memory."""
    config = load_config()
    if getattr(args, 'token', None): config['token'] = args.token
    if getattr(args, 'owner', None): config['owner'] = args.owner
    if getattr(args, 'repo', None):  config['repo'] = args.repo
    if getattr(args, 'branch', None): config['branch'] = args.branch
    save_config(config)
    print(f"✓ Config saved: {config.get('owner')}/{config.get('repo')} [{config.get('branch','main')}]")

    # Test connection
    try:
        gh = get_client()
        gh.test_connection()
    except Exception as e:
        print(f"⚠️  Connection test failed: {e}")
        print("Config saved but connection failed — check your token and repo name.")


# ── Log Command ───────────────────────────────────────────────────────────

def cmd_log(args):
    """Show recent push history."""
    log_path = Path(__file__).parent.parent / 'memory' / 'push_log.jsonl'
    if not log_path.exists():
        print("No push history yet.")
        return

    entries = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except:
                    continue

    print(f"\n{'='*60}")
    print(f"PUSH HISTORY ({len(entries)} pushes)")
    print(f"{'='*60}")
    for e in entries[-10:]:
        print(f"\n{e['timestamp'][:16]}  [{e['branch']}]  {e['files_pushed']} files")
        for c in e.get('commits', []):
            print(f"  {c['commit']}  {c['file']}")


# ── Main ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='GitHub Commit Proposal Engine')
    subparsers = parser.add_subparsers(dest='command')

    # configure
    p = subparsers.add_parser('configure', help='Set GitHub credentials')
    p.add_argument('--token', help='GitHub Personal Access Token')
    p.add_argument('--owner', help='GitHub username or org')
    p.add_argument('--repo', help='Repository name')
    p.add_argument('--branch', default='main', help='Default branch')

    # stage
    p = subparsers.add_parser('stage', help='Stage a file for commit')
    p.add_argument('file', help='Local file path')
    p.add_argument('repo_path', help='Path in the repo (e.g. src/game.html)')
    p.add_argument('--message', '-m', help='Commit message')
    p.add_argument('--token'); p.add_argument('--owner'); p.add_argument('--repo'); p.add_argument('--branch')

    # status
    p = subparsers.add_parser('status', help='Show staged changes')
    p.add_argument('--token'); p.add_argument('--owner'); p.add_argument('--repo'); p.add_argument('--branch')

    # diff
    p = subparsers.add_parser('diff', help='Show full diffs')
    p.add_argument('file', nargs='?', help='Specific file to diff')
    p.add_argument('--token'); p.add_argument('--owner'); p.add_argument('--repo'); p.add_argument('--branch')

    # push
    p = subparsers.add_parser('push', help='Push staged files to GitHub (requires --approved)')
    p.add_argument('--approved', action='store_true',
                   help='Required flag — only set after explicit user approval in chat')
    p.add_argument('--token'); p.add_argument('--owner'); p.add_argument('--repo'); p.add_argument('--branch')

    # clear
    subparsers.add_parser('clear', help='Clear staging area')

    # log
    subparsers.add_parser('log', help='Show push history')

    args = parser.parse_args()

    commands = {
        'configure': cmd_configure,
        'stage': cmd_stage,
        'status': cmd_status,
        'diff': cmd_diff,
        'push': cmd_push,
        'clear': clear_staged,
        'log': cmd_log,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

```

---

## EMBEDDED SCRIPT: scripts/sync_from_github.py
*Write this to `/tmp/github-sync/scripts/sync_from_github.py`*

```python
#!/usr/bin/env python3
"""
scripts/sync_from_github.py — Pull Latest From GitHub
Reads the current state of your repo so Claude always has fresh context.
Replaces the need to manually re-upload files to project knowledge.

Usage:
    python3 sync_from_github.py                    # sync all tracked files
    python3 sync_from_github.py --file src/game.html  # sync specific file
    python3 sync_from_github.py --list             # show what's in repo
    python3 sync_from_github.py --diff src/game.html  # compare local vs remote
"""

import sys, json, argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.github_client import GitHubClient, GitHubError

CONFIG_FILE = Path(__file__).parent.parent / 'memory' / 'github_config.json'
SYNC_STATE  = Path(__file__).parent.parent / 'memory' / 'sync_state.json'
LOCAL_CACHE = Path(__file__).parent.parent / 'memory' / 'file_cache'


def load_config():
    if not CONFIG_FILE.exists():
        raise ValueError("Not configured. Run: python3 propose_commit.py configure --token ... --owner ... --repo ...")
    return json.loads(CONFIG_FILE.read_text())

def get_client():
    config = load_config()
    return GitHubClient(
        token=config['token'],
        owner=config['owner'],
        repo=config['repo'],
        default_branch=config.get('branch', 'main')
    )

def load_sync_state():
    if not SYNC_STATE.exists():
        return {'tracked_files': [], 'last_sync': None, 'file_shas': {}}
    return json.loads(SYNC_STATE.read_text())

def save_sync_state(state):
    SYNC_STATE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE.write_text(json.dumps(state, indent=2))

def cache_file(repo_path, content):
    """Save a file to local cache so Claude can read it without re-fetching."""
    LOCAL_CACHE.mkdir(parents=True, exist_ok=True)
    # Use safe filename
    safe_name = repo_path.replace('/', '__').replace('\\', '__')
    cache_path = LOCAL_CACHE / safe_name
    cache_path.write_text(content, encoding='utf-8')
    return cache_path

def read_cached(repo_path):
    """Read a file from local cache."""
    safe_name = repo_path.replace('/', '__').replace('\\', '__')
    cache_path = LOCAL_CACHE / safe_name
    if cache_path.exists():
        return cache_path.read_text(encoding='utf-8')
    return None


def cmd_sync(args):
    """Pull latest versions of all tracked files from GitHub."""
    gh = get_client()
    config = load_config()
    state = load_sync_state()

    files_to_sync = state.get('tracked_files', [])
    if getattr(args, 'file', None):
        files_to_sync = [args.file]

    if not files_to_sync:
        print("No files tracked yet. Use --track <path> to add files.")
        print("Or use --list to see what's in the repo.")
        return

    print(f"\n{'='*60}")
    print(f"SYNCING FROM GITHUB")
    print(f"Repo: {config['owner']}/{config['repo']} [{config.get('branch','main')}]")
    print(f"{'='*60}")

    updated = []
    unchanged = []
    errors = []

    for repo_path in files_to_sync:
        try:
            remote = gh.get_file(repo_path)
            old_sha = state.get('file_shas', {}).get(repo_path)

            if remote['sha'] == old_sha:
                unchanged.append(repo_path)
                print(f"  = {repo_path} (unchanged)")
            else:
                cache_path = cache_file(repo_path, remote['content'])
                state.setdefault('file_shas', {})[repo_path] = remote['sha']
                updated.append({'path': repo_path, 'sha': remote['sha'][:7], 'cache': str(cache_path)})
                print(f"  ↓ {repo_path} (updated → {remote['sha'][:7]})")

        except GitHubError as e:
            errors.append({'path': repo_path, 'error': str(e)})
            print(f"  ✗ {repo_path} ({e})")

    state['last_sync'] = datetime.now().isoformat()
    save_sync_state(state)

    print(f"\n{'─'*60}")
    print(f"Updated: {len(updated)} | Unchanged: {len(unchanged)} | Errors: {len(errors)}")

    if updated:
        print(f"\nUpdated files cached to:")
        for f in updated:
            print(f"  {f['cache']}")
        print(f"\nClaude can now read these directly from the cache.")

    return updated


def cmd_track(args):
    """Add a file to the sync tracking list."""
    state = load_sync_state()
    tracked = state.get('tracked_files', [])

    if args.file not in tracked:
        tracked.append(args.file)
        state['tracked_files'] = tracked
        save_sync_state(state)
        print(f"✓ Now tracking: {args.file}")
        print(f"  Run 'sync_from_github.py' to pull current version.")
    else:
        print(f"Already tracking: {args.file}")

    print(f"\nAll tracked files ({len(tracked)}):")
    for f in tracked:
        print(f"  {f}")


def cmd_untrack(args):
    """Remove a file from tracking."""
    state = load_sync_state()
    tracked = state.get('tracked_files', [])
    if args.file in tracked:
        tracked.remove(args.file)
        state['tracked_files'] = tracked
        save_sync_state(state)
        print(f"✓ Untracked: {args.file}")
    else:
        print(f"Not tracking: {args.file}")


def cmd_list(args):
    """List files in the repo."""
    gh = get_client()
    config = load_config()
    path = getattr(args, 'path', '') or ''

    print(f"\n{'='*60}")
    print(f"REPO CONTENTS: {config['owner']}/{config['repo']}/{path}")
    print(f"{'='*60}")

    try:
        files = gh.list_files(path)
        state = load_sync_state()
        tracked = state.get('tracked_files', [])
        shas = state.get('file_shas', {})

        for f in sorted(files, key=lambda x: (x['type'] == 'file', x['name'])):
            icon = '📁' if f['type'] == 'dir' else '📄'
            tracking = '✓' if f['path'] in tracked else ' '
            synced = f" [{shas[f['path']][:7]}]" if f['path'] in shas else ''
            size = f" ({f['size']}b)" if f['type'] == 'file' and f['size'] else ''
            print(f"  {tracking} {icon} {f['name']}{size}{synced}")

        print(f"\nLegend: ✓ = tracked for sync")
        print(f"Use --track <path> to add files to sync list.")

    except GitHubError as e:
        print(f"Error: {e}")


def cmd_status(args):
    """Show sync status — what's tracked and when last synced."""
    config = load_config()
    state = load_sync_state()

    print(f"\n{'='*60}")
    print(f"GITHUB SYNC STATUS")
    print(f"{'='*60}")
    print(f"Repo:      {config.get('owner','?')}/{config.get('repo','?')}")
    print(f"Branch:    {config.get('branch','main')}")
    print(f"Last sync: {state.get('last_sync','Never')[:16] if state.get('last_sync') else 'Never'}")

    tracked = state.get('tracked_files', [])
    shas = state.get('file_shas', {})

    print(f"\nTracked files ({len(tracked)}):")
    if not tracked:
        print("  None yet. Use --track <path> to add files.")
    for f in tracked:
        sha = shas.get(f, 'not synced')[:7] if shas.get(f) else 'not synced'
        cached = read_cached(f) is not None
        print(f"  {'✓' if cached else '○'} {f} [{sha}]")

    print(f"\n{'─'*60}")
    print(f"Run 'sync_from_github.py' to pull latest versions.")


def cmd_read(args):
    """
    Read a file from GitHub (or cache) and print it.
    This is how Claude gets fresh file content each session.
    """
    # Try cache first
    cached = read_cached(args.file)
    if cached and not getattr(args, 'fresh', False):
        print(f"[From cache — run sync to update]\n")
        print(cached)
        return

    # Fetch fresh from GitHub
    try:
        gh = get_client()
        remote = gh.get_file(args.file)
        cache_file(args.file, remote['content'])
        print(f"[Fresh from GitHub: {remote['sha'][:7]}]\n")
        print(remote['content'])
    except GitHubError as e:
        print(f"Error reading {args.file}: {e}")


def cmd_history(args):
    """Show commit history for a file or the whole repo."""
    gh = get_client()
    config = load_config()
    filepath = getattr(args, 'file', None)

    history = gh.get_commit_history(path=filepath, limit=15)

    print(f"\n{'='*60}")
    print(f"COMMIT HISTORY: {config['owner']}/{config['repo']}")
    if filepath:
        print(f"File: {filepath}")
    print(f"{'='*60}")
    for c in history:
        print(f"  {c['sha']}  {c['date']}  {c['author']}")
        print(f"           {c['message']}")
    print()


def main():
    parser = argparse.ArgumentParser(description='GitHub Sync — Keep Claude current')
    subparsers = parser.add_subparsers(dest='command')

    # sync
    p = subparsers.add_parser('sync', help='Pull latest from GitHub')
    p.add_argument('--file', help='Sync specific file only')

    # track
    p = subparsers.add_parser('track', help='Add file to sync tracking')
    p.add_argument('file', help='Repo path to track (e.g. src/game.html)')

    # untrack
    p = subparsers.add_parser('untrack', help='Remove file from tracking')
    p.add_argument('file')

    # list
    p = subparsers.add_parser('list', help='List files in repo')
    p.add_argument('path', nargs='?', default='', help='Subdirectory to list')

    # status
    subparsers.add_parser('status', help='Show sync status')

    # read
    p = subparsers.add_parser('read', help='Read a file from GitHub')
    p.add_argument('file')
    p.add_argument('--fresh', action='store_true', help='Force fetch, ignore cache')

    # history
    p = subparsers.add_parser('history', help='Show commit history')
    p.add_argument('file', nargs='?', help='File to show history for')

    args = parser.parse_args()

    commands = {
        'sync': cmd_sync,
        'track': cmd_track,
        'untrack': cmd_untrack,
        'list': cmd_list,
        'status': cmd_status,
        'read': cmd_read,
        'history': cmd_history,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

```
