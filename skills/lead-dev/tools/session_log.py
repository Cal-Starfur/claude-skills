"""
tools/session_log.py — Session Logger
Appends structured data after every coding session.
The raw material for pattern analysis and self-improvement.

Usage (at end of every session):
    import sys; sys.path.insert(0, '/mnt/skills/user/lead-dev')
    from tools.session_log import log_session
    log_session(
        project='wigglers',
        version='V62',
        platform='Devvit',
        intent='user wanted to add worm spawning',
        bugs_found=['duplicate function spawnWorm', 'localStorage used instead of Redis'],
        fixes_applied=['removed duplicate', 'replaced with Redis.set'],
        patterns_noticed=['postMessage handler missing for WORM_SPAWN type'],
        improvised=['had to manually check all postMessage types - audit.py missed this'],
        audit_missed=['postMessage handler coverage incomplete'],
        new_tools_needed=['function to verify all sent types have handlers'],
        time_spent_on=['untangling duplicate logic', 'Redis key naming'],
        debt_added=['spawn rate not configurable yet'],
        log_path='/mnt/skills/user/lead-dev/memory/session_log.jsonl'
    )
"""

import json
import os
from datetime import datetime
from pathlib import Path


def log_session(
    project,
    version,
    platform,
    intent,
    bugs_found=None,
    fixes_applied=None,
    patterns_noticed=None,
    improvised=None,          # things I had to do manually that a script should handle
    audit_missed=None,        # things audit.py failed to catch
    new_tools_needed=None,    # utilities I had to write inline that belong in tools/
    time_spent_on=None,       # what took the most effort (signals pain points)
    debt_added=None,
    rule_violations=None,     # which hard rules were nearly broken or broken
    log_path=None
):
    """Append a session entry to the session log."""

    if log_path is None:
        log_path = Path(__file__).parent.parent / 'memory' / 'session_log.jsonl'
    else:
        log_path = Path(log_path)

    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        'timestamp': datetime.now().isoformat(),
        'project': project,
        'version': version,
        'platform': platform,
        'intent': intent,
        'bugs_found': bugs_found or [],
        'fixes_applied': fixes_applied or [],
        'patterns_noticed': patterns_noticed or [],
        'improvised': improvised or [],
        'audit_missed': audit_missed or [],
        'new_tools_needed': new_tools_needed or [],
        'time_spent_on': time_spent_on or [],
        'debt_added': debt_added or [],
        'rule_violations': rule_violations or [],
    }

    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

    print(f"Session logged: {project} {version} → {log_path}")
    return entry


def read_log(log_path=None, last_n=None):
    """Read all session entries, optionally last N only."""
    if log_path is None:
        log_path = Path(__file__).parent.parent / 'memory' / 'session_log.jsonl'
    else:
        log_path = Path(log_path)

    if not log_path.exists():
        return []

    entries = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if last_n:
        return entries[-last_n:]
    return entries


def summarize_log(log_path=None):
    """Quick summary of the session log for display."""
    entries = read_log(log_path)
    if not entries:
        return "No sessions logged yet."

    projects = {}
    all_bugs = []
    all_improvised = []
    all_audit_missed = []
    all_tools_needed = []

    for e in entries:
        p = e.get('project', 'unknown')
        projects[p] = projects.get(p, 0) + 1
        all_bugs.extend(e.get('bugs_found', []))
        all_improvised.extend(e.get('improvised', []))
        all_audit_missed.extend(e.get('audit_missed', []))
        all_tools_needed.extend(e.get('new_tools_needed', []))

    return {
        'total_sessions': len(entries),
        'projects': projects,
        'total_bugs_found': len(all_bugs),
        'total_things_improvised': len(all_improvised),
        'total_audit_gaps': len(all_audit_missed),
        'total_tool_needs': len(all_tools_needed),
        'date_range': f"{entries[0]['timestamp'][:10]} → {entries[-1]['timestamp'][:10]}",
    }


if __name__ == '__main__':
    # Demo: log a fake session
    log_session(
        project='wigglers',
        version='V62',
        platform='Devvit',
        intent='add worm spawning system',
        bugs_found=[
            'duplicate function: spawnWorm defined twice',
            'localStorage used instead of Redis for worm count',
            'magic number 42 used for spawn rate',
        ],
        fixes_applied=[
            'removed duplicate spawnWorm, kept V2 version',
            'replaced localStorage with Redis.set worms:userId:count',
            'extracted SPAWN_RATE = 42 as named constant',
        ],
        patterns_noticed=[
            'postMessage type WORM_SPAWN sent but no case handler in blocks',
            'every spawn function manually checks Redis — should be abstracted',
        ],
        improvised=[
            'manually scanned all postMessage sends vs handlers — audit.py missed 2 unhandled types',
            'had to write Redis key validator inline — should be in tools/',
        ],
        audit_missed=[
            'postMessage handler coverage check incomplete',
            'did not detect localStorage in minified section',
        ],
        new_tools_needed=[
            'validate_message_handlers(js) → check all sent types have case handlers',
            'validate_redis_keys(js) → check all keys are namespaced correctly',
        ],
        time_spent_on=[
            'untangling duplicate spawn logic (15+ min)',
            'tracing which version of spawnWorm was correct',
        ],
        debt_added=['spawn rate not yet configurable per level'],
        rule_violations=['Rule 2: new system added without checking if one existed (spawn was partially in updateWorms)'],
    )

    print("\nLog summary:")
    summary = summarize_log()
    for k, v in summary.items():
        print(f"  {k}: {v}")

