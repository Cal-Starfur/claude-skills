#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
audit.py — Lead Dev Code Auditor
Scans a JS/HTML game file and reports real problems mechanically.
Usage: python3 audit.py <filepath>
"""

import sys, re, json
from collections import defaultdict, Counter
from pathlib import Path

def extract_js(content):
    """Extract JS from HTML file or return as-is if already JS."""
    if '<script' in content:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        return '\n'.join(scripts)
    return content

def get_lines(content):
    return content.split('\n')

# ── 1. Function Extractor ──────────────────────────────────────────────────
def extract_functions(js, lines):
    functions = []
    patterns = [
        r'function\s+(\w+)\s*\(',           # function foo()
        r'const\s+(\w+)\s*=\s*(?:async\s*)?\(',  # const foo = (
        r'const\s+(\w+)\s*=\s*(?:async\s*)?function',  # const foo = function
        r'(\w+)\s*:\s*(?:async\s*)?function\s*\(',  # foo: function(
        r'(\w+)\s*=\s*(?:async\s*)?function\s*\(',  # foo = function(
    ]
    for i, line in enumerate(lines):
        for pat in patterns:
            m = re.search(pat, line)
            if m:
                name = m.group(1)
                if name not in ('if', 'for', 'while', 'switch', 'catch'):
                    functions.append({'name': name, 'line': i+1, 'raw': line.strip()})
    return functions

# ── 2. Variable Extractor ──────────────────────────────────────────────────
def extract_variables(js, lines):
    variables = []
    pattern = r'\b(var|let|const)\s+(\w+)'
    for i, line in enumerate(lines):
        for m in re.finditer(pattern, line):
            variables.append({'name': m.group(2), 'kind': m.group(1), 'line': i+1})
    return variables

# ── 3. Duplicate Detector ──────────────────────────────────────────────────
def find_duplicates(functions, variables):
    issues = []
    fn_names = [f['name'] for f in functions]
    dupes = [n for n, c in Counter(fn_names).items() if c > 1]
    for d in dupes:
        lines = [f['line'] for f in functions if f['name'] == d]
        issues.append(f"DUPLICATE FUNCTION: '{d}' defined {len(lines)} times at lines {lines}")

    var_names = [v['name'] for v in variables]
    dupes = [n for n, c in Counter(var_names).items() if c > 1]
    for d in dupes:
        lines = [v['line'] for v in variables if v['name'] == d]
        issues.append(f"DUPLICATE VARIABLE: '{d}' declared {len(lines)} times at lines {lines}")
    return issues

# ── 4. Magic Number Detector ──────────────────────────────────────────────
def find_magic_numbers(lines):
    issues = []
    skip = re.compile(r'(\/\/|\/\*|[\'"`]|rgba?\(|hsla?\(|#[0-9a-fA-F])')
    num = re.compile(r'(?<![.\w])(\d{2,})(?![.\w%px])')
    ok_numbers = {'0', '1', '2', '10', '100', '1000', '-1'}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('//') or stripped.startswith('*'):
            continue
        if skip.search(line):
            continue
        for m in num.finditer(line):
            val = m.group(1)
            if val not in ok_numbers:
                issues.append(f"MAGIC NUMBER: {val} at line {i+1} → assign to a named constant")
    return issues[:20]  # cap at 20

# ── 5. Long Function Detector ─────────────────────────────────────────────
def find_long_functions(js, functions):
    issues = []
    lines = js.split('\n')
    for fn in functions:
        start = fn['line'] - 1
        depth = 0
        end = start
        found_open = False
        for i in range(start, min(start + 300, len(lines))):
            for ch in lines[i]:
                if ch == '{':
                    depth += 1
                    found_open = True
                elif ch == '}':
                    depth -= 1
            if found_open and depth == 0:
                end = i
                break
        length = end - start
        if length > 40:
            issues.append(f"LONG FUNCTION: '{fn['name']}' is {length} lines (line {fn['line']}) → consider splitting")
    return issues

# ── 6. Naming Convention Detector ────────────────────────────────────────
def check_naming(functions, variables):
    issues = []
    camel = re.compile(r'^[a-z][a-zA-Z0-9]*$')
    snake = re.compile(r'^[a-z][a-z0-9_]*$')
    bad_names = re.compile(r'^(data|temp|tmp|thing|stuff|val|obj|arr|foo|bar|baz|x|y|z|n|s)$')

    for v in variables:
        if bad_names.match(v['name']):
            issues.append(f"VAGUE NAME: variable '{v['name']}' at line {v['line']} → use a descriptive name")
        if len(v['name']) == 1 and v['name'] not in ('i','j','k','x','y','z'):
            issues.append(f"SINGLE LETTER: variable '{v['name']}' at line {v['line']} → use a descriptive name")

    fn_styles = {'camel': 0, 'snake': 0, 'other': 0}
    for f in functions:
        if camel.match(f['name']): fn_styles['camel'] += 1
        elif snake.match(f['name']): fn_styles['snake'] += 1
        else: fn_styles['other'] += 1

    dominant = max(fn_styles, key=fn_styles.get)
    for f in functions:
        if dominant == 'camel' and not camel.match(f['name']):
            issues.append(f"NAMING MISMATCH: function '{f['name']}' at line {f['line']} → project uses camelCase")
        elif dominant == 'snake' and not snake.match(f['name']):
            issues.append(f"NAMING MISMATCH: function '{f['name']}' at line {f['line']} → project uses snake_case")
    return issues

# ── 7. Dead Code Detector ─────────────────────────────────────────────────
def find_dead_code(js, functions):
    issues = []
    for fn in functions:
        name = fn['name']
        # Count references excluding the definition itself
        refs = len(re.findall(r'\b' + re.escape(name) + r'\b', js))
        if refs <= 1:
            issues.append(f"POSSIBLY DEAD: '{name}' (line {fn['line']}) defined but never called")
    return issues[:15]

# ── 8. Devvit-Specific Checks ─────────────────────────────────────────────
def check_devvit(js, lines):
    issues = []
    if 'postMessage' not in js and 'webviewToBlockMessage' not in js:
        return issues  # Not Devvit

    # Check for raw string message types
    raw_strings = re.findall(r"postMessage\s*\(\s*\{[^}]*type\s*:\s*['\"](\w+)['\"]", js)
    if raw_strings:
        issues.append(f"DEVVIT: Raw string message types found: {raw_strings} → use named constants")

    # Check for localStorage
    if 'localStorage' in js:
        issues.append("DEVVIT: localStorage used → use Redis for persistence in Devvit")

    # Check message handler coverage
    sent = set(re.findall(r"type\s*:\s*['\"](\w+)['\"]", js))
    handled = set(re.findall(r"case\s+['\"](\w+)['\"]", js))
    unhandled = sent - handled
    if unhandled:
        issues.append(f"DEVVIT: Message types sent but no case handler found: {unhandled}")

    return issues

# ── 9. Copy-Paste Detector ────────────────────────────────────────────────
def find_copy_paste(lines):
    issues = []
    chunks = {}
    window = 6  # look for duplicate blocks of 6+ lines
    for i in range(len(lines) - window):
        block = tuple(l.strip() for l in lines[i:i+window] if l.strip())
        if len(block) < window: continue
        key = '\n'.join(block)
        if key in chunks:
            issues.append(f"COPY-PASTE: Lines {i+1}-{i+window} appear similar to lines {chunks[key]+1}-{chunks[key]+window} → extract shared function")
        else:
            chunks[key] = i
    return issues[:5]

# ── Platform Detector ─────────────────────────────────────────────────────
def detect_platform(content):
    if '@devvit/public-api' in content or 'webviewToBlockMessage' in content:
        return 'Devvit'
    if 'new Phaser.Game' in content or 'this.add.' in content:
        return 'Phaser 3'
    if "setup()" in content and "draw()" in content:
        return 'p5.js'
    if "getContext('2d')" in content or 'getContext("2d")' in content:
        return 'Vanilla Canvas'
    if 'import React' in content or 'useState' in content:
        return 'React'
    return 'Unknown'

def detect_game_type(content):
    signals = {
        'Idle/Clicker': ['passive', 'income', 'upgrade', 'prestige', 'click'],
        'Platformer': ['gravity', 'jump', 'velocity', 'platform', 'collision'],
        'Simulation': ['tick', 'simulate', 'environment', 'entity', 'spawn'],
        'Puzzle': ['grid', 'puzzle', 'move', 'solve', 'board'],
        'Tower Defense': ['wave', 'tower', 'enemy', 'path', 'spawn'],
        'RPG': ['inventory', 'stats', 'dialogue', 'quest', 'level'],
    }
    scores = {k: sum(1 for s in v if s.lower() in content.lower()) for k, v in signals.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Unknown'

# ── Main ──────────────────────────────────────────────────────────────────
def audit(filepath):
    content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    js = extract_js(content)
    lines = get_lines(js)

    platform = detect_platform(content)
    game_type = detect_game_type(content)
    functions = extract_functions(js, lines)
    variables = extract_variables(js, lines)

    report = {
        'file': filepath,
        'platform': platform,
        'game_type': game_type,
        'stats': {
            'total_lines': len(get_lines(content)),
            'js_lines': len(lines),
            'functions': len(functions),
            'variables': len(variables),
        },
        'issues': {
            'duplicates': find_duplicates(functions, variables),
            'magic_numbers': find_magic_numbers(lines),
            'long_functions': find_long_functions(js, functions),
            'naming': check_naming(functions, variables),
            'dead_code': find_dead_code(js, functions),
            'devvit': check_devvit(js, lines),
            'copy_paste': find_copy_paste(lines),
        },
        'functions': [{'name': f['name'], 'line': f['line']} for f in functions],
        'variables': [{'name': v['name'], 'kind': v['kind'], 'line': v['line']} for v in variables[:50]],
    }

    total_issues = sum(len(v) for v in report['issues'].values())
    report['total_issues'] = total_issues
    return report

def print_report(report):
    print(f"\n{'='*60}")
    print(f"LEAD DEV AUDIT REPORT")
    print(f"{'='*60}")
    print(f"File:      {report['file']}")
    print(f"Platform:  {report['platform']}")
    print(f"Game Type: {report['game_type']}")
    print(f"Lines:     {report['stats']['total_lines']} total / {report['stats']['js_lines']} JS")
    print(f"Functions: {report['stats']['functions']}")
    print(f"Variables: {report['stats']['variables']}")
    print(f"Issues:    {report['total_issues']} found")
    print(f"{'='*60}\n")

    categories = {
        'duplicates': '🔴 DUPLICATES',
        'long_functions': '🟠 LONG FUNCTIONS',
        'copy_paste': '🟠 COPY-PASTE DETECTED',
        'naming': '🟡 NAMING ISSUES',
        'magic_numbers': '🟡 MAGIC NUMBERS',
        'dead_code': '⚪ POSSIBLY DEAD CODE',
        'devvit': '🔵 DEVVIT-SPECIFIC',
    }

    for key, label in categories.items():
        issues = report['issues'].get(key, [])
        if issues:
            print(f"{label} ({len(issues)})")
            for issue in issues:
                print(f"  → {issue}")
            print()

    print(f"{'='*60}")
    print(f"FUNCTIONS ({len(report['functions'])})")
    print(f"{'='*60}")
    for f in report['functions']:
        print(f"  {f['line']:4d}  {f['name']}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 audit.py <filepath>")
        sys.exit(1)
    filepath = sys.argv[1]
    report = audit(filepath)
    print_report(report)
    # Also save JSON for other scripts to consume
    out = Path(filepath).with_suffix('.audit.json')
    out.write_text(json.dumps(report, indent=2))
    print(f"\nFull report saved: {out}")

