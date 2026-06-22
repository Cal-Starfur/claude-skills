#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
scripts/analyze_patterns.py — Pattern Analyzer
Reads the session log and identifies recurring issues worth turning into
new audit rules, tools, or hard rules.

Usage: python3 analyze_patterns.py [--log <path>] [--min-occurrences 2]
"""

import sys, json, re, argparse
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.session_log import read_log, summarize_log


def tokenize(text):
    """Break text into meaningful keywords for pattern matching."""
    text = text.lower()
    # Remove common filler words
    stopwords = {'a','an','the','is','was','in','on','at','to','for','of','and','or',
                 'had','have','has','been','with','from','that','this','it','not','no',
                 'but','by','so','if','as','my','we','i','you','they','did','do','does'}
    words = re.findall(r'\b[a-z]\w+\b', text)
    return [w for w in words if w not in stopwords and len(w) > 3]


def find_recurring_patterns(entries, min_occurrences=2):
    """
    Analyze all session entries and find patterns that repeat.
    Returns dict of pattern categories with their occurrences.
    """
    patterns = {
        'audit_gaps': defaultdict(list),       # things audit.py missed
        'improvised_tasks': defaultdict(list),  # things done manually that should be automated
        'tool_needs': defaultdict(list),        # tools needed but not in library
        'bug_patterns': defaultdict(list),      # recurring bug types
        'time_sinks': defaultdict(list),        # things that keep eating time
        'rule_violations': defaultdict(list),   # rules that keep getting broken
        'platform_specific': defaultdict(list), # platform-specific recurring issues
    }

    # Keyword clusters for similarity grouping
    keyword_buckets = defaultdict(list)

    for i, entry in enumerate(entries):
        ts = entry.get('timestamp', '')[:10]
        project = entry.get('project', 'unknown')
        platform = entry.get('platform', 'unknown')
        label = f"[{ts} {project}]"

        # Audit gaps
        for item in entry.get('audit_missed', []):
            keywords = frozenset(tokenize(item)[:4])
            if keywords:
                patterns['audit_gaps'][keywords].append((label, item))

        # Improvised tasks
        for item in entry.get('improvised', []):
            keywords = frozenset(tokenize(item)[:4])
            if keywords:
                patterns['improvised_tasks'][keywords].append((label, item))

        # Tool needs
        for item in entry.get('new_tools_needed', []):
            keywords = frozenset(tokenize(item)[:3])
            if keywords:
                patterns['tool_needs'][keywords].append((label, item))

        # Bug patterns
        for item in entry.get('bugs_found', []):
            keywords = frozenset(tokenize(item)[:3])
            if keywords:
                patterns['bug_patterns'][keywords].append((label, item))

        # Time sinks
        for item in entry.get('time_spent_on', []):
            keywords = frozenset(tokenize(item)[:3])
            if keywords:
                patterns['time_sinks'][keywords].append((label, item))

        # Rule violations
        for item in entry.get('rule_violations', []):
            keywords = frozenset(tokenize(item)[:3])
            if keywords:
                patterns['rule_violations'][keywords].append((label, item))

        # Platform-specific
        if platform not in ('Unknown', ''):
            for item in entry.get('bugs_found', []) + entry.get('patterns_noticed', []):
                keywords = frozenset([platform.lower().split()[0]] + tokenize(item)[:2])
                patterns['platform_specific'][keywords].append((label, item, platform))

    # Filter to only recurring patterns
    recurring = {}
    for category, bucket in patterns.items():
        recurring[category] = [
            {
                'keywords': list(k),
                'count': len(v),
                'occurrences': v,
                'representative': v[0][1] if v else '',
            }
            for k, v in bucket.items()
            if len(v) >= min_occurrences
        ]
        # Sort by frequency
        recurring[category].sort(key=lambda x: x['count'], reverse=True)

    return recurring


def score_improvement_priority(patterns):
    """
    Score each pattern category by how urgently it needs a fix.
    Returns prioritized list of improvements to propose.
    """
    proposals = []

    for item in patterns.get('audit_gaps', []):
        proposals.append({
            'priority': item['count'] * 3,  # audit gaps are high value
            'type': 'new_audit_rule',
            'description': f"audit.py missed this {item['count']} times: {item['representative']}",
            'keywords': item['keywords'],
            'occurrences': item['count'],
        })

    for item in patterns.get('tool_needs', []):
        proposals.append({
            'priority': item['count'] * 2,
            'type': 'new_tool_function',
            'description': f"Tool needed {item['count']} times: {item['representative']}",
            'keywords': item['keywords'],
            'occurrences': item['count'],
        })

    for item in patterns.get('improvised_tasks', []):
        proposals.append({
            'priority': item['count'] * 2,
            'type': 'automate_task',
            'description': f"Manual task repeated {item['count']} times: {item['representative']}",
            'keywords': item['keywords'],
            'occurrences': item['count'],
        })

    for item in patterns.get('bug_patterns', []):
        proposals.append({
            'priority': item['count'],
            'type': 'new_audit_rule',
            'description': f"Bug seen {item['count']} times: {item['representative']}",
            'keywords': item['keywords'],
            'occurrences': item['count'],
        })

    for item in patterns.get('rule_violations', []):
        proposals.append({
            'priority': item['count'] * 2,
            'type': 'strengthen_rule',
            'description': f"Rule violated {item['count']} times: {item['representative']}",
            'keywords': item['keywords'],
            'occurrences': item['count'],
        })

    proposals.sort(key=lambda x: x['priority'], reverse=True)
    return proposals


def generate_report(entries, patterns, proposals):
    """Generate a human-readable analysis report."""
    summary = summarize_log()

    lines = [
        "=" * 60,
        "LEAD DEV — PATTERN ANALYSIS REPORT",
        "=" * 60,
        f"Sessions analyzed: {summary.get('total_sessions', len(entries))}",
        f"Date range: {summary.get('date_range', 'N/A')}",
        f"Projects: {summary.get('projects', {})}",
        f"Total bugs found across all sessions: {summary.get('total_bugs_found', 0)}",
        f"Total audit gaps: {summary.get('total_audit_gaps', 0)}",
        f"Total improvised tasks: {summary.get('total_things_improvised', 0)}",
        f"Total tool needs identified: {summary.get('total_tool_needs', 0)}",
        "",
        "=" * 60,
        f"RECURRING PATTERNS (appear 2+ times)",
        "=" * 60,
    ]

    category_labels = {
        'audit_gaps': '🔍 AUDIT GAPS (audit.py missed these)',
        'improvised_tasks': '🔧 IMPROVISED TASKS (should be automated)',
        'tool_needs': '🛠️  TOOL NEEDS (functions needed but not in library)',
        'bug_patterns': '🐛 RECURRING BUG PATTERNS',
        'time_sinks': '⏱️  TIME SINKS (recurring effort)',
        'rule_violations': '⚠️  RULE VIOLATIONS (rules being broken repeatedly)',
        'platform_specific': '🔵 PLATFORM-SPECIFIC PATTERNS',
    }

    for category, label in category_labels.items():
        items = patterns.get(category, [])
        if not items:
            continue
        lines.append(f"\n{label} ({len(items)} patterns found)")
        for item in items[:5]:  # top 5 per category
            lines.append(f"  × {item['count']}  {item['representative']}")
            if len(item['occurrences']) > 1:
                for occ in item['occurrences'][:2]:
                    lines.append(f"         {occ[0]}")

    lines += [
        "",
        "=" * 60,
        f"TOP IMPROVEMENT PROPOSALS (by priority)",
        "=" * 60,
    ]

    for i, p in enumerate(proposals[:10], 1):
        type_label = {
            'new_audit_rule': '📋 NEW AUDIT RULE',
            'new_tool_function': '🛠️  NEW TOOL FUNCTION',
            'automate_task': '⚙️  AUTOMATE TASK',
            'strengthen_rule': '💪 STRENGTHEN RULE',
        }.get(p['type'], p['type'])

        lines.append(f"\n{i}. {type_label} (seen {p['occurrences']}x)")
        lines.append(f"   {p['description']}")

    lines += ["", "=" * 60,
              "Run propose_improvements.py to generate actual code for these."]

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default=None, help='Path to session_log.jsonl')
    parser.add_argument('--min-occurrences', type=int, default=2)
    parser.add_argument('--json', action='store_true', help='Output JSON instead of text')
    args = parser.parse_args()

    log_path = args.log or str(Path(__file__).parent.parent / 'memory' / 'session_log.jsonl')
    entries = read_log(log_path)

    if not entries:
        print("No session data found. Log some sessions first with session_log.py")
        sys.exit(0)

    patterns = find_recurring_patterns(entries, args.min_occurrences)
    proposals = score_improvement_priority(patterns)

    if args.json:
        print(json.dumps({'patterns': patterns, 'proposals': proposals}, indent=2))
    else:
        report = generate_report(entries, patterns, proposals)
        print(report)

        # Save report
        out = Path(log_path).parent / 'pattern_report.txt'
        out.write_text(report)
        print(f"\nReport saved: {out}")

    return proposals


if __name__ == '__main__':
    main()

