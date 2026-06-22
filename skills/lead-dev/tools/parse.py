"""
tools/parse.py — Shared JS/HTML Parser
Used by audit.py, generate_architecture.py, drift_detect.py, and any future skill.

Import:
    import sys; sys.path.insert(0, '/mnt/skills/user/lead-dev')
    from tools.parse import extract_js, extract_functions, extract_variables, detect_platform, detect_game_type
"""

import re
from collections import Counter

# ── Content Extraction ────────────────────────────────────────────────────

def extract_js(content):
    """Extract JS from HTML file or return as-is if already JS."""
    if '<script' in content:
        scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
        return '\n'.join(scripts)
    return content

def extract_css(content):
    """Extract CSS from HTML file."""
    return '\n'.join(re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL))

# ── Platform & Game Detection ─────────────────────────────────────────────

PLATFORM_SIGNALS = {
    'Devvit': ['@devvit/public-api', 'webviewToBlockMessage', 'Devvit.addMenuItem', 'Devvit.addCustomPostType'],
    'Phaser 3': ['new Phaser.Game', 'this.add.', 'this.physics.', 'Phaser.Scene'],
    'p5.js': ['function setup()', 'function draw()', 'createCanvas(', 'noStroke('],
    'Vanilla Canvas': ["getContext('2d')", 'getContext("2d")', 'requestAnimationFrame', 'HTMLCanvasElement'],
    'React': ['import React', 'useState', 'useEffect', 'jsx', 'ReactDOM'],
    'Pixi.js': ['PIXI.Application', 'PIXI.Sprite', 'new PIXI'],
    'Three.js': ['THREE.Scene', 'THREE.Camera', 'new THREE'],
}

GAME_TYPE_SIGNALS = {
    'Idle/Clicker': ['passive', 'income', 'upgrade', 'prestige', 'autoClick', 'perSecond'],
    'Platformer': ['gravity', 'jump', 'velocity', 'platform', 'collision', 'grounded'],
    'Simulation': ['tick', 'simulate', 'environment', 'entity', 'worm', 'compost', 'drain'],
    'Puzzle': ['grid', 'puzzle', 'solve', 'board', 'tile', 'swap', 'match'],
    'Tower Defense': ['wave', 'tower', 'enemy', 'pathfind', 'turret'],
    'RPG': ['inventory', 'stats', 'dialogue', 'quest', 'level', 'xp', 'equipment'],
    'Shooter': ['bullet', 'shoot', 'projectile', 'laser', 'ammo', 'fire'],
    'Racing': ['speed', 'lap', 'track', 'drift', 'finish'],
}

def detect_platform(content):
    """Returns (platform_name, confidence_score)."""
    scores = {}
    for platform, signals in PLATFORM_SIGNALS.items():
        score = sum(1 for s in signals if s in content)
        if score > 0:
            scores[platform] = score
    if not scores:
        return 'Unknown', 0
    best = max(scores, key=scores.get)
    return best, scores[best]

def detect_game_type(content):
    """Returns (game_type, confidence_score)."""
    scores = {}
    content_lower = content.lower()
    for gtype, signals in GAME_TYPE_SIGNALS.items():
        score = sum(1 for s in signals if s.lower() in content_lower)
        if score > 0:
            scores[gtype] = score
    if not scores:
        return 'Unknown', 0
    best = max(scores, key=scores.get)
    return best, scores[best]

def detect_naming_convention(js):
    """
    Returns (style, prefix_map).
    style: 'camelCase' | 'snake_case' | 'Hungarian/prefixed camelCase' | 'mixed'
    prefix_map: {'p': 'likely player', 'e': 'likely enemy', ...}
    """
    all_names = re.findall(r'\b(?:var|let|const|function)\s+([a-zA-Z_]\w*)', js)

    camel_count = sum(1 for n in all_names if re.match(r'^[a-z][a-zA-Z0-9]+$', n) and any(c.isupper() for c in n[1:]))
    snake_count = sum(1 for n in all_names if '_' in n and n == n.lower())
    prefix_count = sum(1 for n in all_names if len(n) > 2 and n[0].islower() and n[1].isupper())

    # Detect prefix patterns (Hungarian notation)
    prefix_map = {}
    for name in all_names:
        if len(name) > 2 and name[0].islower() and name[1].isupper():
            prefix = name[0]
            prefix_map[prefix] = prefix_map.get(prefix, 0) + 1
    # Only report prefixes used 3+ times
    common_prefixes = {k: v for k, v in prefix_map.items() if v >= 3}

    dominant_count = max(camel_count, snake_count, prefix_count)
    if dominant_count == 0:
        style = 'unknown'
    elif prefix_count == dominant_count and common_prefixes:
        style = 'Hungarian/prefixed camelCase'
    elif snake_count == dominant_count:
        style = 'snake_case'
    else:
        style = 'camelCase'

    # Mixed check
    if camel_count > 2 and snake_count > 2:
        style = 'mixed (PROBLEM: inconsistent)'

    return style, common_prefixes

# ── Function Extraction ───────────────────────────────────────────────────

FUNCTION_PATTERNS = [
    (r'function\s+(\w+)\s*\(([^)]*)\)', 'declaration'),
    (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', 'arrow'),
    (r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function\s*\(([^)]*)\)', 'expression'),
    (r'(\w+)\s*:\s*(?:async\s*)?function\s*\(([^)]*)\)', 'method'),
    (r'async\s+function\s+(\w+)\s*\(([^)]*)\)', 'async'),
]

SKIP_KEYWORDS = {'if', 'for', 'while', 'switch', 'catch', 'return', 'else', 'case'}

def extract_functions(js):
    """
    Returns list of dicts:
    {name, params, line, length, kind, comment, is_long}
    """
    lines = js.split('\n')
    functions = []
    seen = set()

    for i, line in enumerate(lines):
        for pat, kind in FUNCTION_PATTERNS:
            m = re.search(pat, line)
            if not m:
                continue
            name = m.group(1)
            if name in SKIP_KEYWORDS or name in seen:
                continue
            seen.add(name)

            params = m.group(2).strip() if len(m.groups()) > 1 else ''

            # Measure function length by brace counting
            depth, end, found_open = 0, i, False
            for j in range(i, min(i + 300, len(lines))):
                for ch in lines[j]:
                    if ch == '{':
                        depth += 1
                        found_open = True
                    elif ch == '}':
                        depth -= 1
                if found_open and depth == 0:
                    end = j
                    break
            length = end - i

            # Grab comment above function if present
            comment = ''
            if i > 0 and '//' in lines[i-1]:
                comment = lines[i-1].strip().lstrip('/').strip()

            functions.append({
                'name': name,
                'params': params,
                'line': i + 1,
                'length': length,
                'kind': kind,
                'comment': comment,
                'is_long': length > 40
            })
            break

    return functions

# ── Variable Extraction ───────────────────────────────────────────────────

def extract_variables(js):
    """
    Returns list of dicts:
    {name, kind, type, line, value_hint}
    """
    lines = js.split('\n')
    variables = []
    seen = set()
    pattern = r'\b(var|let|const)\s+(\w+)\s*(?:=\s*([^;,\n]+))?'

    for i, line in enumerate(lines):
        for m in re.finditer(pattern, line):
            name = m.group(2)
            if name in seen or name in ('i', 'j', 'k'):
                continue
            seen.add(name)

            hint = (m.group(3) or '').strip()[:50]

            # Infer type from value hint
            vtype = 'unknown'
            if hint.startswith('{'):       vtype = 'object'
            elif hint.startswith('['):      vtype = 'array'
            elif hint.startswith(("'",'"')): vtype = 'string'
            elif re.match(r'^-?\d+\.?\d*$', hint): vtype = 'number'
            elif hint in ('true', 'false'): vtype = 'boolean'
            elif hint.startswith('new '):   vtype = 'instance'
            elif '=>' in hint or hint.startswith('function'): vtype = 'function'
            elif hint == '':               vtype = 'declared'

            variables.append({
                'name': name,
                'kind': m.group(1),
                'type': vtype,
                'line': i + 1,
                'value_hint': hint
            })

    return variables

# ── PostMessage / Devvit Extraction ───────────────────────────────────────

def extract_message_types(js):
    """Find all postMessage type strings used in code."""
    types = set()
    types.update(re.findall(r"type\s*:\s*['\"](\w+)['\"]", js))
    types.update(re.findall(r"case\s+['\"](\w+)['\"]", js))
    return sorted(types)

def extract_redis_keys(js):
    """Find Redis key patterns used in Devvit code."""
    keys = re.findall(r"redis\.\w+\s*\(['\"]([^'\"]+)['\"]", js)
    return sorted(set(keys))

# ── Constants Extraction ──────────────────────────────────────────────────

def extract_constants(js):
    """Find ALL_CAPS_SNAKE_CASE constants."""
    constants = []
    for m in re.finditer(r'(?:const|let|var)\s+([A-Z][A-Z0-9_]{2,})\s*=\s*([^;\n]+)', js):
        constants.append({
            'name': m.group(1),
            'value': m.group(2).strip()[:60]
        })
    return constants

# ── System Grouper ────────────────────────────────────────────────────────

SYSTEM_KEYWORDS = {
    'Player':           ['player', 'payer', 'hero', 'character'],
    'Enemy/NPC':        ['enemy', 'mob', 'npc', 'monster', 'creature'],
    'UI/Rendering':     ['ui', 'hud', 'menu', 'screen', 'draw', 'render', 'display', 'paint'],
    'Input':            ['input', 'key', 'mouse', 'click', 'touch', 'event', 'control'],
    'Progression/Save': ['score', 'point', 'level', 'progress', 'save', 'load', 'high'],
    'Audio':            ['audio', 'sound', 'music', 'sfx', 'play', 'mute'],
    'Physics':          ['physics', 'gravity', 'velocity', 'collision', 'bounce', 'friction'],
    'Initialization':   ['init', 'setup', 'start', 'create', 'spawn', 'reset'],
    'Game Loop':        ['update', 'tick', 'loop', 'step', 'frame', 'animate'],
    'Collision':        ['collision', 'hit', 'overlap', 'intersect', 'detect'],
    'Communication':    ['post', 'message', 'send', 'receive', 'redis', 'fetch', 'request'],
    'Particles':        ['particle', 'effect', 'emitter', 'burst', 'trail'],
    'Camera':           ['camera', 'viewport', 'scroll', 'pan', 'zoom'],
    'Animation':        ['anim', 'sprite', 'frame', 'sequence', 'transition'],
}

def group_into_systems(functions):
    """Group functions by detected system. Returns {system_name: [fn_dicts]}."""
    from collections import defaultdict
    systems = defaultdict(list)
    for fn in functions:
        name_lower = fn['name'].lower()
        assigned = False
        for system, keywords in SYSTEM_KEYWORDS.items():
            if any(kw in name_lower for kw in keywords):
                systems[system].append(fn)
                assigned = True
                break
        if not assigned:
            systems['Misc/Uncategorized'].append(fn)
    return dict(systems)

# ── Quick Stats ───────────────────────────────────────────────────────────

def file_stats(content, js):
    return {
        'total_lines': len(content.split('\n')),
        'js_lines': len(js.split('\n')),
        'blank_lines': sum(1 for l in js.split('\n') if not l.strip()),
        'comment_lines': sum(1 for l in js.split('\n') if l.strip().startswith('//')),
        'char_count': len(content),
    }


# ── AUTO-GENERATED BY SELF-IMPROVEMENT ENGINE ─────────────────────────────
# Generated from pattern: validate_message_handlers needed 3x across sessions
# Added: 2026-06-15

def validate_message_handlers(js):
    """
    Check that every postMessage type sent has a corresponding case handler.
    This was the #1 recurring audit gap across Devvit projects.

    Usage:
        from tools.parse import validate_message_handlers
        issues = validate_message_handlers(js)
        # returns [] if clean, or list of issue strings

    Returns:
        List of issue strings for unhandled message types.
        Empty list if all sent types have handlers.
    """
    import re
    issues = []

    # Find all types being SENT via postMessage
    sent_types = set(re.findall(r"type\s*:\s*['\"](\w+)['\"]", js))

    # Find all types being HANDLED via case statements
    handled_types = set(re.findall(r"case\s+['\"](\w+)['\"]", js))

    # Also check object-style handlers: MSG_TYPES.FOO or similar
    constant_refs = set(re.findall(r'MSG(?:_TYPES?)?\.\s*(\w+)', js))
    handled_types.update(constant_refs)

    unhandled = sent_types - handled_types
    for t in sorted(unhandled):
        issues.append(
            f"POSTMESSAGE: type '{t}' is sent but has no case handler — "
            f"messages will be silently dropped"
        )

    # Also check for handlers with no corresponding send (orphaned handlers)
    orphaned = handled_types - sent_types - {'default', 'INIT', 'READY'}
    for t in sorted(orphaned):
        issues.append(
            f"POSTMESSAGE: case handler for '{t}' exists but type is never sent — "
            f"possible dead code or renamed type"
        )

    return issues


def validate_redis_key_namespacing(js):
    """
    Check that all Redis key strings are properly namespaced.
    Unnamespaced keys cause collisions between users and posts.
    Pattern: keys should follow gameName:userId:keyName format.

    Generated from pattern: Redis namespace violations seen 2x across sessions.

    Returns:
        List of issue strings for unnamespaced Redis keys.
    """
    import re
    issues = []

    # Find Redis set/get calls with string literal keys
    redis_calls = re.findall(
        r'redis\.\w+\s*\(\s*[\'"]([^\'"]+)[\'"]',
        js
    )

    for key in redis_calls:
        parts = key.split(':')
        if len(parts) < 2:
            issues.append(
                f"REDIS: Key '{key}' is not namespaced — "
                f"use format 'gameName:userId:keyName' to prevent collisions"
            )
        elif len(parts) < 3 and 'userId' not in js[js.find(key)-50:js.find(key)+50]:
            issues.append(
                f"REDIS: Key '{key}' may be missing userId namespace — "
                f"verify it includes user-specific scoping"
            )

    return issues

