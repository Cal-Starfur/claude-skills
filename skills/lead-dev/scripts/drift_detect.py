#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
drift_detect.py — Lead Dev Drift Detector
Compares current game file against GAME_ARCHITECTURE.md to find what changed.
Usage: python3 drift_detect.py <game_filepath> <architecture_filepath>
"""

import sys, re
from pathlib import Path
from datetime import datetime

def extract_js(content):
    if '<script' in content:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        return '\n'.join(scripts)
    return content

def get_functions_from_file(js):
    """Extract all function names from the live file."""
    names = set()
    patterns = [
        r'function\s+(\w+)\s*\(',
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(',
        r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function',
        r'(\w+)\s*:\s*(?:async\s*)?function\s*\(',
    ]
    for pat in patterns:
        for m in re.finditer(pat, js):
            name = m.group(1)
            if name not in ('if','for','while','switch','catch','return'):
                names.add(name)
    return names

def get_functions_from_architecture(arch_content):
    """Extract function names documented in GAME_ARCHITECTURE.md."""
    names = set()
    # Match table rows like | `functionName(...)` |
    for m in re.finditer(r'\|\s*`(\w+)\s*\(', arch_content):
        names.add(m.group(1))
    # Also match inline code like `functionName()`
    for m in re.finditer(r'`(\w+)\(\)`', arch_content):
        names.add(m.group(1))
    return names

def get_variables_from_file(js):
    """Extract all variable names from the live file."""
    names = set()
    for m in re.finditer(r'\b(?:var|let|const)\s+(\w+)', js):
        names.add(m.group(1))
    return names

def get_variables_from_architecture(arch_content):
    """Extract variable names documented in GAME_ARCHITECTURE.md."""
    names = set()
    for m in re.finditer(r'\|\s*`(\w+)`\s*\|\s*(?:var|let|const)', arch_content):
        names.add(m.group(1))
    return names

def get_version_from_architecture(arch_content):
    m = re.search(r'Current Version.*?(V\d+)', arch_content)
    return m.group(1) if m else 'Unknown'

def get_last_updated(arch_content):
    m = re.search(r'Last Updated.*?(\d{4}-\d{2}-\d{2})', arch_content)
    return m.group(1) if m else 'Unknown'

def get_known_issues(arch_content):
    issues = re.findall(r'- \[[ x]\] (.+)', arch_content)
    return issues

def detect_new_postmessage_types(js, arch_content):
    """Find postMessage types in file not documented in architecture."""
    in_file = set(re.findall(r"type\s*:\s*['\"](\w+)['\"]", js))
    in_arch = set(re.findall(r'`([A-Z_]+)`', arch_content))
    return in_file - in_arch

def check_naming_drift(js, arch_content):
    """Check if new code violates the naming convention in the architecture."""
    issues = []
    # Get convention from architecture
    style_match = re.search(r'Style detected.*?:\s*(.+)', arch_content)
    if not style_match:
        return issues
    style = style_match.group(1).strip()

    new_fns = re.findall(r'function\s+(\w+)\s*\(', js)
    if 'camelCase' in style:
        for name in new_fns:
            if '_' in name:
                issues.append(f"Naming drift: '{name}' uses snake_case but project uses camelCase")
    elif 'snake_case' in style:
        for name in new_fns:
            if any(c.isupper() for c in name):
                issues.append(f"Naming drift: '{name}' uses camelCase but project uses snake_case")
    return issues

def estimate_changes(game_content, arch_content):
    """Rough estimate of how much the file has changed since architecture was generated."""
    arch_line_count = re.search(r'(\d+) lines\)', arch_content)
    current_lines = len(game_content.split('\n'))
    if arch_line_count:
        prev_lines = int(arch_line_count.group(1))
        diff = current_lines - prev_lines
        return current_lines, prev_lines, diff
    return current_lines, 0, 0

def drift_report(game_filepath, arch_filepath):
    game_content = Path(game_filepath).read_text(encoding='utf-8', errors='ignore')
    arch_content = Path(arch_filepath).read_text(encoding='utf-8', errors='ignore')

    js = extract_js(game_content)

    # Extract sets
    fns_in_file = get_functions_from_file(js)
    fns_in_arch = get_functions_from_architecture(arch_content)
    vars_in_file = get_variables_from_file(js)
    vars_in_arch = get_variables_from_architecture(arch_content)

    # Compute diffs
    new_functions = fns_in_file - fns_in_arch
    deleted_functions = fns_in_arch - fns_in_file
    new_variables = vars_in_file - vars_in_arch

    version = get_version_from_architecture(arch_content)
    last_updated = get_last_updated(arch_content)
    current_lines, prev_lines, line_diff = estimate_changes(game_content, arch_content)
    naming_issues = check_naming_drift(js, arch_content)
    new_msg_types = detect_new_postmessage_types(js, arch_content)
    known_issues = get_known_issues(arch_content)

    # Build report
    report = {
        'game_file': game_filepath,
        'arch_file': arch_filepath,
        'arch_version': version,
        'arch_last_updated': last_updated,
        'current_lines': current_lines,
        'prev_lines': prev_lines,
        'line_diff': line_diff,
        'new_functions': sorted(new_functions),
        'deleted_functions': sorted(deleted_functions),
        'new_variables': sorted(new_variables)[:20],
        'naming_violations': naming_issues,
        'undocumented_message_types': sorted(new_msg_types),
        'known_issues': known_issues,
        'drift_score': len(new_functions) + len(deleted_functions) * 2,
    }
    return report

def print_drift_report(r):
    drift = r['drift_score']
    if drift == 0: severity = "✅ CLEAN"
    elif drift < 5: severity = "🟡 MINOR DRIFT"
    elif drift < 15: severity = "🟠 MODERATE DRIFT"
    else: severity = "🔴 MAJOR DRIFT — ARCHITECTURE NEEDS UPDATE"

    print(f"\n{'='*60}")
    print(f"LEAD DEV — DRIFT DETECTION REPORT")
    print(f"{'='*60}")
    print(f"Architecture version: {r['arch_version']} (last updated {r['arch_last_updated']})")
    print(f"Current file lines:   {r['current_lines']} (was {r['prev_lines']}, diff: {r['line_diff']:+d})")
    print(f"Drift status:         {severity}")
    print(f"{'='*60}\n")

    if r['new_functions']:
        print(f"🆕 NEW FUNCTIONS ({len(r['new_functions'])}) — Not in architecture yet:")
        for f in r['new_functions']:
            print(f"   + {f}()")
        print()

    if r['deleted_functions']:
        print(f"🗑️  DELETED/RENAMED ({len(r['deleted_functions'])}) — In architecture but not in file:")
        for f in r['deleted_functions']:
            print(f"   - {f}()")
        print("   → Were these intentionally removed? Update or mark deprecated in architecture.\n")

    if r['new_variables']:
        print(f"📦 NEW VARIABLES ({len(r['new_variables'])}) — Not documented:")
        for v in r['new_variables'][:10]:
            print(f"   + {v}")
        if len(r['new_variables']) > 10:
            print(f"   ... and {len(r['new_variables'])-10} more")
        print()

    if r['naming_violations']:
        print(f"⚠️  NAMING VIOLATIONS:")
        for v in r['naming_violations']:
            print(f"   → {v}")
        print()

    if r['undocumented_message_types']:
        print(f"🔵 UNDOCUMENTED MESSAGE TYPES (Devvit):")
        for t in r['undocumented_message_types']:
            print(f"   → '{t}' sent/handled but not in architecture")
        print()

    if r['known_issues']:
        print(f"📋 OPEN ISSUES FROM LAST SESSION ({len(r['known_issues'])}):")
        for issue in r['known_issues']:
            print(f"   [ ] {issue}")
        print()

    print(f"{'='*60}")
    if drift > 0:
        print(f"ACTION REQUIRED: Run generate_architecture.py to update the source of truth.")
    else:
        print(f"Architecture is current. No action needed.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 drift_detect.py <game_file> <GAME_ARCHITECTURE.md>")
        sys.exit(1)
    report = drift_report(sys.argv[1], sys.argv[2])
    print_drift_report(report)

