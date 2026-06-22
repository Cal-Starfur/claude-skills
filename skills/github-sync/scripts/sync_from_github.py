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

