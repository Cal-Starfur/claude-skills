#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
generate_architecture.py — Lead Dev Architecture Generator
Parses a game file and generates GAME_ARCHITECTURE.md automatically.
Usage: python3 generate_architecture.py <filepath> [version]
"""

import sys, re, json
from pathlib import Path
from datetime import datetime
def extract_js(content):
    if '<script' in content:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        return '\n'.join(scripts)
    return content

def detect_platform(content):
    if '@devvit/public-api' in content or 'webviewToBlockMessage' in content:
        return 'Devvit (Reddit Mini-App)'
    if 'new Phaser.Game' in content or 'this.add.' in content:
        return 'Phaser 3'
    if 'setup()' in content and 'draw()' in content:
        return 'p5.js'
    if "getContext('2d')" in content or 'getContext("2d")' in content:
        return 'Vanilla Canvas'
    if 'import React' in content or 'useState' in content:
        return 'React'
    return 'Unknown'

def detect_game_type(content):
    signals = {
        'Idle/Clicker': ['passive', 'income', 'upgrade', 'prestige', 'autoClick'],
        'Platformer': ['gravity', 'jump', 'velocity', 'platform', 'collision'],
        'Simulation': ['tick', 'simulate', 'environment', 'entity', 'spawn'],
        'Puzzle': ['grid', 'puzzle', 'solve', 'board', 'tile'],
        'Tower Defense': ['wave', 'tower', 'enemy', 'path', 'spawn'],
        'RPG': ['inventory', 'stats', 'dialogue', 'quest', 'level'],
    }
    scores = {k: sum(1 for s in v if s.lower() in content.lower()) for k, v in signals.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else 'Unknown'

def detect_naming_convention(js):
    vars_found = re.findall(r'\b(?:var|let|const)\s+([a-zA-Z_]\w*)', js)
    fns_found = re.findall(r'function\s+([a-zA-Z_]\w*)', js)
    all_names = vars_found + fns_found

    camel = sum(1 for n in all_names if re.match(r'^[a-z][a-zA-Z0-9]*$', n) and any(c.isupper() for c in n))
    snake = sum(1 for n in all_names if '_' in n and n == n.lower())
    prefixed = sum(1 for n in all_names if len(n) > 2 and n[0].islower() and n[1].isupper())

    # Detect Hungarian-style prefixes
    prefixes = {}
    for name in all_names:
        if len(name) > 2 and name[0].islower() and name[1].isupper():
            prefix = name[0]
            prefixes[prefix] = prefixes.get(prefix, 0) + 1
    common_prefixes = {k: v for k, v in prefixes.items() if v >= 3}

    style = 'camelCase'
    if snake > camel:
        style = 'snake_case'
    if prefixed > camel and prefixed > snake:
        style = 'Hungarian/prefixed camelCase'

    return style, common_prefixes

def extract_functions_detailed(js):
    lines = js.split('\n')
    functions = []
    patterns = [
        (r'function\s+(\w+)\s*\(([^)]*)\)', 'declaration'),
        (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', 'arrow'),
        (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function\s*\(([^)]*)\)', 'expression'),
        (r'(\w+)\s*:\s*(?:async\s*)?function\s*\(([^)]*)\)', 'method'),
    ]

    for i, line in enumerate(lines):
        for pat, kind in patterns:
            m = re.search(pat, line)
            if m:
                name = m.group(1)
                params = m.group(2).strip() if len(m.groups()) > 1 else ''
                if name in ('if', 'for', 'while', 'switch', 'catch', 'return'):
                    continue
                # Estimate length
                depth, end, found = 0, i, False
                for j in range(i, min(i+200, len(lines))):
                    for ch in lines[j]:
                        if ch == '{': depth += 1; found = True
                        elif ch == '}': depth -= 1
                    if found and depth == 0:
                        end = j; break
                length = end - i

                # Get first comment above function
                comment = ''
                if i > 0 and lines[i-1].strip().startswith('//'):
                    comment = lines[i-1].strip().lstrip('/')  .strip()

                functions.append({
                    'name': name,
                    'params': params,
                    'line': i + 1,
                    'length': length,
                    'kind': kind,
                    'comment': comment,
                    'flag': '⚠️ LONG' if length > 40 else ''
                })
                break
    return functions

def extract_variables_detailed(js):
    lines = js.split('\n')
    variables = []
    seen = set()
    pattern = r'\b(var|let|const)\s+(\w+)\s*(?:=\s*([^;,\n]+))?'
    for i, line in enumerate(lines):
        for m in re.finditer(pattern, line):
            name = m.group(2)
            if name in seen or name in ('i','j','k'):
                continue
            seen.add(name)
            value_hint = m.group(3).strip()[:40] if m.group(3) else ''
            # Guess type from value
            vtype = 'unknown'
            if value_hint.startswith('{'):    vtype = 'object'
            elif value_hint.startswith('['):   vtype = 'array'
            elif value_hint.startswith("'") or value_hint.startswith('"'): vtype = 'string'
            elif re.match(r'^-?\d+\.?\d*$', value_hint): vtype = 'number'
            elif value_hint in ('true','false'): vtype = 'boolean'
            elif value_hint.startswith('new '): vtype = 'instance'
            elif value_hint.startswith('function') or '=>' in value_hint: vtype = 'function'
            elif value_hint == '': vtype = 'declared'

            variables.append({
                'name': name,
                'kind': m.group(1),
                'type': vtype,
                'line': i + 1,
                'hint': value_hint[:40]
            })
    return variables

def detect_systems(js, functions):
    """Group functions into logical systems based on naming patterns."""
    systems = defaultdict(list)
    for fn in functions:
        name = fn['name'].lower()
        if any(w in name for w in ['player','payer']):
            systems['Player'].append(fn)
        elif any(w in name for w in ['enemy','mob','npc']):
            systems['Enemy/NPC'].append(fn)
        elif any(w in name for w in ['ui','hud','menu','screen','draw','render','display']):
            systems['UI/Rendering'].append(fn)
        elif any(w in name for w in ['input','key','mouse','click','touch','event']):
            systems['Input'].append(fn)
        elif any(w in name for w in ['score','point','level','progress','save','load']):
            systems['Progression/Save'].append(fn)
        elif any(w in name for w in ['audio','sound','music','sfx']):
            systems['Audio'].append(fn)
        elif any(w in name for w in ['spawn','create','init','setup','start']):
            systems['Initialization'].append(fn)
        elif any(w in name for w in ['update','tick','loop','step','frame']):
            systems['Game Loop'].append(fn)
        elif any(w in name for w in ['collision','hit','overlap','intersect']):
            systems['Collision'].append(fn)
        elif any(w in name for w in ['post','message','send','receive','redis']):
            systems['Communication'].append(fn)
        else:
            systems['Misc/Uncategorized'].append(fn)
    return dict(systems)

def detect_postmessage_types(js):
    types = set()
    types.update(re.findall(r"type\s*:\s*['\"](\w+)['\"]", js))
    types.update(re.findall(r"case\s+['\"](\w+)['\"]", js))
    return sorted(types)

def detect_constants(js):
    consts = []
    for m in re.finditer(r'const\s+([A-Z][A-Z0-9_]+)\s*=\s*([^;\n]+)', js):
        consts.append({'name': m.group(1), 'value': m.group(2).strip()[:60]})
    return consts

# ── Main Generator ────────────────────────────────────────────────────────
def generate(filepath, version='V??'):
    content = Path(filepath).read_text(encoding='utf-8', errors='ignore')
    js = extract_js(content)
    filename = Path(filepath).name

    platform = detect_platform(content)
    game_type = detect_game_type(content)
    naming_style, prefixes = detect_naming_convention(js)
    functions = extract_functions_detailed(js)
    variables = extract_variables_detailed(js)
    systems = detect_systems(js, functions)
    msg_types = detect_postmessage_types(js) if 'Devvit' in platform else []
    constants = detect_constants(js)
    total_lines = len(content.split('\n'))

    prefix_notes = '\n'.join([f'  - `{k}` prefix = {v} variables found' for k, v in prefixes.items()]) if prefixes else '  - No consistent prefix pattern detected'

    # Build the markdown
    md = f"""# GAME_ARCHITECTURE.md
*Source of truth. Updated every session. Never delete entries — only add or mark deprecated.*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Auto-scanned by Lead Dev skill*

---

## Identity
- **Game:** {filename.replace('.html','').replace('.js','')}
- **Platform:** {platform}
- **Game Type:** {game_type}
- **Current Version:** {version}
- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
- **Source File:** `{filename}` ({total_lines} lines)

---

## Platform Context
"""

    if 'Devvit' in platform:
        md += """**Devvit (Reddit Mini-App)**
- Runs inside a Reddit post as a sandboxed webview
- Two separate worlds: Devvit Blocks (main.tsx) ↔ Webview (HTML/JS)
- Communication ONLY via postMessage — never any other method
- Persistence via Redis — never localStorage
- All message types must be named constants, never raw strings
- Context object (userId, postId) passed through Devvit triggers

**Message Types Found:**
"""
        if msg_types:
            for t in msg_types:
                md += f"- `{t}`\n"
        else:
            md += "- None detected yet\n"
    elif 'Phaser' in platform:
        md += "**Phaser 3**\n- Scene-based architecture\n- Physics, input, and assets managed by Phaser systems\n"
    elif 'Canvas' in platform:
        md += "**Vanilla Canvas**\n- Raw HTML5 Canvas API\n- requestAnimationFrame game loop\n- Manual state management\n"
    else:
        md += f"**{platform}**\n- [Add platform-specific context here]\n"

    md += f"""
---

## Naming Conventions (ENFORCED — Never Violate)
- **Style detected:** {naming_style}
- **Prefixes in use:**
{prefix_notes}
- **Constants:** ALL_CAPS_SNAKE_CASE
- **Rule:** Match existing style exactly. Never introduce a new naming pattern.

---

## Systems Map
*Auto-detected from function names. Review and refine each session.*

"""
    for system_name, fns in systems.items():
        md += f"### {system_name}\n"
        md += f"- **Functions ({len(fns)}):** "
        md += ', '.join([f'`{f["name"]}()`' for f in fns[:8]])
        if len(fns) > 8:
            md += f' + {len(fns)-8} more'
        md += '\n- **Talks To:** [fill in]\n- **Must NOT modify:** [fill in]\n\n'

    md += f"""---

## Constants Registry
*All named constants found in the codebase.*

| Constant | Value |
|---|---|
"""
    if constants:
        for c in constants[:30]:
            md += f"| `{c['name']}` | `{c['value']}` |\n"
    else:
        md += "| — | No ALL_CAPS constants found — magic numbers may be in use |\n"

    md += f"""
---

## Function Registry
*Every function. Line numbers current as of last scan.*

| Function | Line | Length | Notes |
|---|---|---|---|
"""
    for f in functions:
        flag = f.get('flag', '')
        comment = f.get('comment', '')[:50]
        md += f"| `{f['name']}({f['params'][:20]})` | {f['line']} | {f['length']} lines | {flag} {comment} |\n"

    md += f"""
---

## Variable Registry
*Key variables tracked across sessions.*

| Variable | Kind | Type | Line | Hint |
|---|---|---|---|---|
"""
    for v in variables[:60]:
        md += f"| `{v['name']}` | {v['kind']} | {v['type']} | {v['line']} | `{v['hint']}` |\n"

    md += """
---

## Known Issues / Tech Debt
*Honest. Never hide problems. Add entries every session.*

- [ ] [Run audit.py to populate this section]

---

## Do Not Touch
*Fragile, deprecated, or in active refactor.*

- [None identified yet — populate as issues are found]

---

## Changelog

### """ + version + """ — """ + datetime.now().strftime('%Y-%m-%d') + """
- **Intent:** Initial architecture scan
- **Changed:** Generated GAME_ARCHITECTURE.md from source file
- **New systems:** [list any]
- **Debt added:** None
- **Next session:** Review auto-detected systems, fill in system boundaries

---
*This file is maintained by the Lead Dev skill. Update it every session.*
"""
    return md

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 generate_architecture.py <filepath> [version]")
        sys.exit(1)
    filepath = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else 'V??'
    md = generate(filepath, version)
    out = Path(filepath).parent / 'GAME_ARCHITECTURE.md'
    out.write_text(md)
    print(f"Generated: {out}")
    print(f"Lines: {len(md.splitlines())}")

