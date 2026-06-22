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

