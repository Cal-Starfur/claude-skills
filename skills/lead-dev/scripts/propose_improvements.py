#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
scripts/propose_improvements.py — Self-Improvement Engine
Reads pattern analysis output and uses the Claude API to write actual
new audit rules, tool functions, and skill updates.

This is the skill writing its own code.

Usage: python3 propose_improvements.py [--log <path>] [--auto-apply]
"""

import sys, json, re, argparse, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.session_log import read_log
from scripts.analyze_patterns import find_recurring_patterns, score_improvement_priority


SKILL_ROOT = Path(__file__).parent.parent


def load_existing_audit(audit_path=None):
    """Load current audit.py to give Claude context on what already exists."""
    if audit_path is None:
        audit_path = SKILL_ROOT / 'scripts' / 'audit.py'
    try:
        content = Path(audit_path).read_text()
        # Summarize to save tokens — just function signatures and docstrings
        lines = content.split('\n')
        summary = []
        for i, line in enumerate(lines):
            if line.startswith('def ') or line.startswith('# ──'):
                summary.append(line)
            elif summary and lines[max(0,i-1)].startswith('def ') and '"""' in line:
                summary.append(line)
        return '\n'.join(summary[:60])
    except:
        return '# audit.py not found'


def load_existing_tools(tools_path=None):
    """Summarize what's already in the tools library."""
    if tools_path is None:
        tools_path = SKILL_ROOT / 'tools'
    summaries = []
    for pyfile in Path(tools_path).glob('*.py'):
        if pyfile.name == '__init__.py':
            continue
        content = pyfile.read_text()
        # Extract function signatures only
        fns = re.findall(r'^def (\w+)\([^)]*\):', content, re.MULTILINE)
        if fns:
            summaries.append(f"tools/{pyfile.name}: {', '.join(fns)}")
    return '\n'.join(summaries)


def call_claude(system_prompt, user_prompt, max_tokens=3000):
    """Call Claude API and return response text."""
    payload = {
        'model': 'claude-sonnet-4-6',
        'max_tokens': max_tokens,
        'system': system_prompt,
        'messages': [{'role': 'user', 'content': user_prompt}]
    }
    try:
        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=json.dumps(payload).encode(),
            headers={
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read())
            return result['content'][0]['text']
    except urllib.error.HTTPError as e:
        return f"# API Error {e.code}: {e.reason}"
    except Exception as e:
        return f"# Error: {str(e)[:200]}"


def propose_audit_rule(description, occurrences, existing_audit_summary):
    """Ask Claude to write a new audit function for a recurring bug pattern."""
    system = """You are a senior Python developer writing audit functions for a game code analyzer.
You write clean, precise Python that detects specific code quality issues in JS/HTML game files.
Output ONLY valid Python code — no explanation, no markdown fences."""

    prompt = f"""Write a new Python audit function to detect this recurring issue:

PROBLEM: {description}
SEEN: {occurrences} times across multiple sessions

EXISTING AUDIT FUNCTIONS (don't duplicate):
{existing_audit_summary}

Write ONE Python function that:
1. Takes (js: str, lines: list) as parameters — js is the raw JS, lines is js.split('\\n')
2. Returns a list of issue strings (empty list if no issues found)
3. Each issue string starts with the category in caps, e.g. "POSTMESSAGE: ..."
4. Is specific enough to catch the real pattern, not generate false positives
5. Has a clear docstring

Example format:
def check_postmessage_handlers(js, lines):
    \"\"\"Check that every postMessage type sent has a corresponding case handler.\"\"\"
    issues = []
    sent_types = set(re.findall(r"type\\s*:\\s*['\\"](\\w+)['\\"]\", js))
    handled_types = set(re.findall(r"case\\s+['\\"](\\w+)['\\"]\", js))
    unhandled = sent_types - handled_types
    for t in unhandled:
        issues.append(f"POSTMESSAGE: type '{{t}}' is sent but has no case handler")
    return issues

Now write a similar function for: {description}"""

    return call_claude(system, prompt, max_tokens=1000)


def propose_tool_function(description, existing_tools_summary):
    """Ask Claude to write a new shared tool function."""
    system = """You are a senior Python developer writing utility functions for a shared game dev tools library.
You write clean, reusable Python utilities that work across multiple skills.
Output ONLY valid Python code — no explanation, no markdown fences."""

    prompt = f"""Write a new Python utility function for the tools library.

NEED: {description}

EXISTING TOOLS (don't duplicate):
{existing_tools_summary}

Write ONE Python function that:
1. Is reusable across different game projects and platforms
2. Has a clear docstring explaining usage and return value
3. Has sensible default parameters
4. Returns something useful (don't print — return)
5. Includes a usage example in the docstring

The function will be imported like:
    from tools.parse import your_function_name
    from tools.score import your_function_name

Choose the right module based on what it does:
- parse.py → JS/HTML analysis
- score.py → image comparison
- palette.py → color utilities
- If it doesn't fit, suggest a new module name as a comment

Write the function now:"""

    return call_claude(system, prompt, max_tokens=800)


def propose_skill_update(pattern_report, current_skill_rules):
    """Ask Claude to propose updates to SKILL.md hard rules or workflow."""
    system = """You are updating a Lead Dev skill file (SKILL.md) based on recurring patterns found in session logs.
You write precise, actionable rule updates.
Output ONLY the new/updated rule text — no explanation, no markdown fences around the whole thing."""

    prompt = f"""Based on these recurring patterns from real coding sessions, propose updates to the skill's hard rules.

PATTERNS FOUND:
{pattern_report}

CURRENT HARD RULES (don't duplicate):
{current_skill_rules}

Propose 1-3 new hard rules or updates to existing ones.
Format each as:
## NEW RULE: [rule number]. [Rule title]
[Rule description — one clear sentence]

Or for updates:
## UPDATE RULE: [existing rule number]
OLD: [old text]
NEW: [improved text]

Only propose rules that directly address the recurring patterns.
Do not propose vague rules. Each rule must be checkable — either a thing is done or it isn't."""

    return call_claude(system, prompt, max_tokens=600)


def apply_improvement(improvement_type, code, target_path, dry_run=True):
    """Apply a proposed improvement to the actual skill files."""
    if dry_run:
        print(f"\n[DRY RUN] Would write to: {target_path}")
        print(f"{'─'*50}")
        print(code[:500] + ('...' if len(code) > 500 else ''))
        print(f"{'─'*50}")
        return False

    target = Path(target_path)

    if improvement_type == 'new_audit_rule':
        # Append new function to audit.py
        existing = target.read_text()
        # Insert before the main() function
        insertion_point = existing.rfind('\n# ── Main')
        if insertion_point == -1:
            insertion_point = existing.rfind('\ndef audit(')
        if insertion_point == -1:
            insertion_point = len(existing)

        new_content = existing[:insertion_point] + '\n\n' + code + '\n' + existing[insertion_point:]
        target.write_text(new_content)
        print(f"✓ Applied new audit rule to {target}")
        return True

    elif improvement_type == 'new_tool_function':
        # Append to appropriate tools file
        existing = target.read_text()
        new_content = existing + '\n\n' + code + '\n'
        target.write_text(new_content)
        print(f"✓ Applied new tool function to {target}")
        return True

    elif improvement_type == 'skill_update':
        # These go into a proposals file for human review
        proposals_path = SKILL_ROOT / 'memory' / 'skill_proposals.md'
        proposals_path.parent.mkdir(exist_ok=True)
        with open(proposals_path, 'a') as f:
            f.write(f"\n\n## Proposed Update — {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(code)
        print(f"✓ Skill update proposal saved to {proposals_path}")
        return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--log', default=None)
    parser.add_argument('--auto-apply', action='store_true',
                        help='Actually write proposed improvements to files (default: dry run)')
    parser.add_argument('--max-proposals', type=int, default=5)
    args = parser.parse_args()

    log_path = args.log or str(SKILL_ROOT / 'memory' / 'session_log.jsonl')
    entries = read_log(log_path)

    if not entries:
        print("No session data found. Need logged sessions to analyze.")
        sys.exit(0)

    print(f"\n{'='*60}")
    print(f"LEAD DEV — SELF-IMPROVEMENT ENGINE")
    print(f"{'='*60}")
    print(f"Analyzing {len(entries)} sessions...")

    patterns = find_recurring_patterns(entries, min_occurrences=2)
    proposals = score_improvement_priority(patterns)

    if not proposals:
        print("No recurring patterns found yet. Need more sessions (2+ of same pattern).")
        sys.exit(0)

    print(f"Found {len(proposals)} improvement opportunities.")
    print(f"Processing top {min(args.max_proposals, len(proposals))}...\n")

    existing_audit = load_existing_audit()
    existing_tools = load_existing_tools()
    dry_run = not args.auto_apply

    if dry_run:
        print("MODE: Dry run — showing proposals only (use --auto-apply to write to files)\n")

    results = []
    for i, proposal in enumerate(proposals[:args.max_proposals], 1):
        print(f"\n{'─'*60}")
        print(f"PROPOSAL {i}/{min(args.max_proposals, len(proposals))}")
        print(f"Type: {proposal['type']}")
        print(f"Pattern: {proposal['description'][:80]}")
        print(f"Seen: {proposal['occurrences']} times")
        print(f"Generating code...")

        if proposal['type'] == 'new_audit_rule':
            code = propose_audit_rule(
                proposal['description'],
                proposal['occurrences'],
                existing_audit
            )
            target = SKILL_ROOT / 'scripts' / 'audit.py'
            applied = apply_improvement('new_audit_rule', code, target, dry_run)

        elif proposal['type'] == 'new_tool_function':
            code = propose_tool_function(
                proposal['description'],
                existing_tools
            )
            target = SKILL_ROOT / 'tools' / 'parse.py'
            applied = apply_improvement('new_tool_function', code, target, dry_run)

        elif proposal['type'] in ('automate_task', 'strengthen_rule'):
            # These become skill rule proposals
            pattern_summary = f"Pattern: {proposal['description']}\nSeen {proposal['occurrences']} times"
            current_rules = "Never start coding without reading architecture.\nNever duplicate functions.\nAlways bump version."
            code = propose_skill_update(pattern_summary, current_rules)
            target = SKILL_ROOT / 'memory' / 'skill_proposals.md'
            applied = apply_improvement('skill_update', code, target, dry_run)

        else:
            code = f"# {proposal['type']}: {proposal['description']}"
            applied = False

        results.append({
            'proposal': proposal,
            'code': code,
            'applied': applied,
        })

    # Save all proposals to review file
    proposals_path = SKILL_ROOT / 'memory' / 'improvement_proposals.json'
    proposals_path.parent.mkdir(exist_ok=True)
    with open(proposals_path, 'w') as f:
        json.dump([{
            'type': r['proposal']['type'],
            'description': r['proposal']['description'],
            'occurrences': r['proposal']['occurrences'],
            'proposed_code': r['code'],
            'applied': r['applied'],
            'generated_at': datetime.now().isoformat(),
        } for r in results], f, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"{'='*60}")
    print(f"Proposals generated: {len(results)}")
    print(f"Applied to files: {sum(1 for r in results if r['applied'])}")
    print(f"Saved to: {proposals_path}")
    if dry_run:
        print(f"\nTo apply: python3 propose_improvements.py --auto-apply")
    print(f"{'='*60}\n")

    return results


if __name__ == '__main__':
    main()

