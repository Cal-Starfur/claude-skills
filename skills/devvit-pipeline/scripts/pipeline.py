#!/usr/bin/env python3
"""
scripts/pipeline.py — Full Devvit Deploy Pipeline
Orchestrates: push code → trigger deploy → monitor → read feedback

Usage:
    python3 pipeline.py deploy     # trigger deploy workflow + monitor
    python3 pipeline.py status     # check last deploy status
    python3 pipeline.py feedback   # read Reddit comments on game post
    python3 pipeline.py monitor    # watch for new comments (live)
    python3 pipeline.py setup      # push deploy workflow to repo
    python3 pipeline.py configure  # set credentials
"""

import sys, json, time, argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/tmp/devvit-pipeline')

CONFIG_FILE = Path('/tmp/devvit-pipeline/memory/pipeline_config.json')


def load_config():
    if not CONFIG_FILE.exists():
        raise ValueError(
            "Not configured. Run: python3 pipeline.py configure"
        )
    return json.loads(CONFIG_FILE.read_text())

def save_config(config):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))

def get_github_client():
    from tools.github_client import GitHubClient
    config = load_config()
    return GitHubClient(
        config['github_token'],
        config['github_owner'],
        config['github_repo'],
    )

def get_actions_client():
    from tools.actions_client import ActionsClient
    config = load_config()
    return ActionsClient(
        config['github_token'],
        config['github_owner'],
        config['github_repo'],
    )

def get_reddit_client():
    from tools.reddit_client import RedditClient
    config = load_config()
    rc = config.get('reddit', {})
    return RedditClient(
        client_id=rc['client_id'],
        client_secret=rc['client_secret'],
        username=rc['username'],
        password=rc['password'],
        user_agent=f"{config['github_repo']}/1.0 by u/{rc['username']}",
    )


# ── Configure ─────────────────────────────────────────────────────────────

def cmd_configure(args):
    """Save all pipeline credentials."""
    config = load_config() if CONFIG_FILE.exists() else {}

    print("\nGitHub credentials:")
    if getattr(args, 'github_token', None): config['github_token'] = args.github_token
    if getattr(args, 'github_owner', None): config['github_owner'] = args.github_owner
    if getattr(args, 'github_repo', None):  config['github_repo'] = args.github_repo

    print("Reddit credentials:")
    if not config.get('reddit'):
        config['reddit'] = {}
    if getattr(args, 'reddit_client_id', None):
        config['reddit']['client_id'] = args.reddit_client_id
    if getattr(args, 'reddit_client_secret', None):
        config['reddit']['client_secret'] = args.reddit_client_secret
    if getattr(args, 'reddit_username', None):
        config['reddit']['username'] = args.reddit_username
    if getattr(args, 'reddit_password', None):
        config['reddit']['password'] = args.reddit_password

    if getattr(args, 'subreddit', None):
        config['subreddit'] = args.subreddit
    if getattr(args, 'game_title_keyword', None):
        config['game_title_keyword'] = args.game_title_keyword

    save_config(config)
    print(f"\n✓ Config saved")

    # Test connections
    try:
        gh = get_github_client()
        gh.test_connection()
    except Exception as e:
        print(f"⚠️  GitHub: {e}")

    try:
        reddit = get_reddit_client()
        reddit.test_connection()
    except Exception as e:
        print(f"⚠️  Reddit: {e}")


# ── Setup ──────────────────────────────────────────────────────────────────

def cmd_setup(args):
    """
    Push the GitHub Actions deploy workflow to the repo.
    Only needs to be done once.
    """
    print("\n" + "="*60)
    print("SETUP — Push Deploy Workflow to GitHub")
    print("="*60)

    actions = get_actions_client()
    gh = get_github_client()

    # Check if workflow already exists
    existing = gh.file_exists('.github/workflows/deploy.yml')
    if existing and not getattr(args, 'force', False):
        print("✓ deploy.yml already exists in repo")
        print("  Use --force to overwrite")
        return

    # Generate workflow content
    workflow_yaml = actions.generate_deploy_workflow()

    print("\nWorkflow to push:")
    print("  .github/workflows/deploy.yml")
    print("  Triggers: push to main + manual dispatch")
    print("  Steps: checkout → node setup → npm ci → devvit upload")
    print()
    print("⚠️  IMPORTANT: You need to add DEVVIT_TOKEN to GitHub Secrets:")
    print("  GitHub repo → Settings → Secrets → Actions → New secret")
    print("  Name: DEVVIT_TOKEN")
    print("  Value: your Devvit auth token (run 'devvit tokens' in Codespaces to get it)")
    print()

    confirm = input("Push workflow? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Cancelled.")
        return

    result = gh.write_file(
        path='.github/workflows/deploy.yml',
        content=workflow_yaml,
        commit_message='ci: add Devvit deploy workflow',
    )
    print(f"\n✓ Pushed: {result['file_url']}")
    print(f"  Commit: {result['commit_sha']}")
    print("\nNext: add DEVVIT_TOKEN secret, then run: python3 pipeline.py deploy")


# ── Deploy ─────────────────────────────────────────────────────────────────

def cmd_deploy(args):
    """Trigger deployment and monitor until complete."""
    print("\n" + "="*60)
    print("DEPLOYING WIGGLERS ROOM")
    print("="*60)

    actions = get_actions_client()

    # Check workflow exists
    workflow_id = actions.get_workflow_id('deploy.yml')
    if not workflow_id:
        print("✗ deploy.yml workflow not found in repo")
        print("  Run: python3 pipeline.py setup")
        return

    print(f"\nTriggering deploy workflow...")
    run = actions.trigger_workflow('deploy.yml', inputs={
        'reason': f'Deploy triggered from Claude — {datetime.now().strftime("%Y-%m-%d %H:%M")}'
    })

    run_id = run.get('run_id')
    if not run_id:
        print(f"✗ Could not get run ID — check GitHub Actions tab")
        return

    print(f"Run ID: {run_id}")
    print(f"URL: {run.get('url', 'check GitHub Actions')}")
    print()

    # Monitor
    result = actions.wait_for_completion(run_id, timeout_seconds=300)

    print()
    if result['conclusion'] == 'success':
        print("✓ DEPLOY SUCCESSFUL")
        print("  Wigglers Room is live on Reddit")

        # Read logs for confirmation
        try:
            jobs = actions.get_job_logs(run_id)
            for job in jobs:
                print(f"\n  Job: {job['name']} → {job['conclusion']}")
                for step in job['steps']:
                    icon = '✓' if step['conclusion'] == 'success' else '✗'
                    print(f"    {icon} {step['name']}")
        except:
            pass

        # Save deploy record
        _log_deploy(run_id, 'success')

        print("\nChecking for player feedback...")
        cmd_feedback(args)

    else:
        print(f"✗ DEPLOY FAILED — conclusion: {result['conclusion']}")
        print(f"  URL: {result.get('url', '')}")
        print("\nFetching logs...")
        try:
            logs = actions.get_run_logs(run_id, max_lines=50)
            print(logs)
        except Exception as e:
            print(f"Could not fetch logs: {e}")

        _log_deploy(run_id, result['conclusion'])


# ── Status ─────────────────────────────────────────────────────────────────

def cmd_status(args):
    """Show recent deploy status."""
    print("\n" + "="*60)
    print("DEPLOY STATUS")
    print("="*60)

    actions = get_actions_client()
    config = load_config()

    runs = actions.get_recent_runs(limit=5)
    if not runs:
        print("No recent runs found")
        return

    for run in runs:
        conclusion = run.get('conclusion') or run['status']
        icon = {'success': '✓', 'failure': '✗', 'cancelled': '○'}.get(conclusion, '?')
        print(f"\n{icon} {run['name']}")
        print(f"  Status:  {run['status']} / {conclusion}")
        print(f"  Branch:  {run['branch']} @ {run['commit']}")
        print(f"  Time:    {run['created']}")
        print(f"  URL:     {run['url']}")


# ── Feedback ───────────────────────────────────────────────────────────────

def cmd_feedback(args):
    """Read player comments on the game post."""
    print("\n" + "="*60)
    print("PLAYER FEEDBACK")
    print("="*60)

    config = load_config()
    reddit = get_reddit_client()

    subreddit = config.get('subreddit')
    keyword = config.get('game_title_keyword', 'Wigglers')

    if not subreddit:
        print("No subreddit configured. Run: python3 pipeline.py configure --subreddit yoursubreddit")
        return

    # Find the game post
    print(f"Looking for '{keyword}' post in r/{subreddit}...")
    post = reddit.find_game_post(subreddit, keyword)

    if not post:
        print(f"✗ No '{keyword}' post found in r/{subreddit}")
        print("  Has the game been posted yet?")
        return

    print(f"\n✓ Found: {post['title']}")
    print(f"  URL: {post['url']}")
    print(f"  Score: {post['score']} | Comments: {post['num_comments']}")
    print(f"  Posted: {post['created']}")

    # Get comments
    comments = reddit.get_comments(subreddit, post['id'], limit=20)

    if not comments:
        print("\n  No comments yet")
        return

    since_minutes = getattr(args, 'since', None)
    if since_minutes:
        comments = reddit.get_new_comments_since(subreddit, post['id'], since_minutes)
        print(f"\nNew comments (last {since_minutes} min): {len(comments)}")
    else:
        print(f"\nRecent comments ({len(comments)}):")

    for c in comments[:10]:
        print(f"\n  u/{c['author']} [{c['created']}] ↑{c['score']}")
        # Wrap long comments
        body = c['body'].replace('\n', ' ')
        if len(body) > 200:
            body = body[:197] + '...'
        print(f"  {body}")

    # Summary for Claude to act on
    if len(comments) > 0:
        print(f"\n{'─'*60}")
        print(f"SUMMARY FOR ACTION:")
        print(f"  Total comments: {len(comments)}")
        bug_words = ['bug', 'broken', 'crash', 'error', 'doesn\'t work', 'not working', 'fix']
        bugs = [c for c in comments if any(w in c['body'].lower() for w in bug_words)]
        if bugs:
            print(f"  Possible bug reports: {len(bugs)}")
            for b in bugs[:3]:
                print(f"    → u/{b['author']}: {b['body'][:100]}")

    # Save post ID for future calls
    config['last_game_post_id'] = post['id']
    config['last_game_post_url'] = post['url']
    save_config(config)


# ── Monitor ────────────────────────────────────────────────────────────────

def cmd_monitor(args):
    """Watch for new comments on the game post (polls every 60s)."""
    config = load_config()
    reddit = get_reddit_client()
    subreddit = config.get('subreddit')
    keyword = config.get('game_title_keyword', 'Wigglers')

    post = reddit.find_game_post(subreddit, keyword)
    if not post:
        print(f"✗ No game post found in r/{subreddit}")
        return

    print(f"\nMonitoring: {post['title']}")
    print(f"URL: {post['url']}")
    print("Checking for new comments every 60 seconds... (Ctrl+C to stop)\n")

    seen_ids = set()
    while True:
        try:
            comments = reddit.get_comments(subreddit, post['id'], limit=25)
            new = [c for c in comments if c['id'] not in seen_ids]
            for c in new:
                print(f"[{c['created']}] u/{c['author']}: {c['body'][:150]}")
                seen_ids.add(c['id'])
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nStopped monitoring.")
            break


# ── Deploy Log ─────────────────────────────────────────────────────────────

def _log_deploy(run_id, conclusion):
    log_path = Path('/tmp/devvit-pipeline/memory/deploy_log.jsonl')
    log_path.parent.mkdir(exist_ok=True)
    entry = {
        'timestamp': datetime.now().isoformat(),
        'run_id': run_id,
        'conclusion': conclusion,
    }
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Devvit Deploy Pipeline')
    subparsers = parser.add_subparsers(dest='command')

    # configure
    p = subparsers.add_parser('configure', help='Set all credentials')
    p.add_argument('--github-token')
    p.add_argument('--github-owner')
    p.add_argument('--github-repo')
    p.add_argument('--reddit-client-id')
    p.add_argument('--reddit-client-secret')
    p.add_argument('--reddit-username')
    p.add_argument('--reddit-password')
    p.add_argument('--subreddit')
    p.add_argument('--game-title-keyword', default='Wigglers')

    # setup
    p = subparsers.add_parser('setup', help='Push deploy workflow to repo')
    p.add_argument('--force', action='store_true')

    # deploy
    subparsers.add_parser('deploy', help='Trigger deploy and monitor')

    # status
    subparsers.add_parser('status', help='Show recent deploy runs')

    # feedback
    p = subparsers.add_parser('feedback', help='Read player comments')
    p.add_argument('--since', type=int, help='Only show comments from last N minutes')

    # monitor
    subparsers.add_parser('monitor', help='Watch for new comments live')

    args = parser.parse_args()

    commands = {
        'configure': cmd_configure,
        'setup': cmd_setup,
        'deploy': cmd_deploy,
        'status': cmd_status,
        'feedback': cmd_feedback,
        'monitor': cmd_monitor,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

