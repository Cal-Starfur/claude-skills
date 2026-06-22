"""
devvit_inspector.py — Contractor's Devvit File Scanner
Runs on any uploaded file and produces a tight brief:
  - Which file type it is (main.tsx / game.js / index.html / yaml)
  - What message types are sent vs received (and mismatches)
  - What Redis keys are used
  - What Devvit permissions are configured
  - Any obvious bug patterns found
  - Surgical entry points relevant to common tickets

Usage:
  python3 /tmp/contractor/devvit_inspector.py <filepath>
  python3 /tmp/contractor/devvit_inspector.py <filepath> --ticket "add shield powerup"
"""

import sys
import re
import json
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_file(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"ERROR: Cannot read {path}: {e}")
        sys.exit(1)

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def subsection(title):
    print(f"\n── {title} " + "─" * max(0, 54 - len(title)))

def warn(msg):
    print(f"  ⚠️  {msg}")

def ok(msg):
    print(f"  ✓  {msg}")

def info(msg):
    print(f"  →  {msg}")

def flag(msg):
    print(f"  🚩 {msg}")


# ── File Type Detection ───────────────────────────────────────────────────────

def detect_file_type(path, content):
    p = str(path).lower()
    if p.endswith('.yaml') or p.endswith('.yml'):
        return 'devvit_yaml'
    if p.endswith('main.tsx') or p.endswith('main.ts'):
        return 'blocks_main'
    if 'devvit' in content[:500] and 'postMessage' in content:
        return 'blocks_main'
    if '@devvit/public-api' in content:
        return 'blocks_main'
    if p.endswith('game.js') or (p.endswith('.js') and 'canvas' in content.lower()):
        return 'webview_game'
    if p.endswith('.html') or p.endswith('index.html'):
        return 'webview_html'
    if 'getContext' in content or 'requestAnimationFrame' in content:
        return 'webview_game'
    if 'window.parent.postMessage' in content:
        return 'webview_game'
    return 'unknown'


# ── Message Type Extraction ───────────────────────────────────────────────────

def extract_sent_messages(content, file_type):
    """Find all message types being sent FROM this file."""
    sent = []
    
    # window.parent.postMessage({ type: 'X' ... }) — webview sending up
    for m in re.finditer(r"window\.parent\.postMessage\s*\(\s*\{[^}]*?type\s*:\s*['\"]([^'\"]+)['\"]", content, re.DOTALL):
        sent.append(('webview→blocks', m.group(1), m.start()))
    
    # context.ui.webView.postMessage(id, { type: 'X' }) — blocks sending down
    for m in re.finditer(r"\.postMessage\s*\(\s*['\"][^'\"]*['\"]\s*,\s*\{[^}]*?type\s*:\s*['\"]([^'\"]+)['\"]", content, re.DOTALL):
        sent.append(('blocks→webview', m.group(1), m.start()))
    
    # Also catch postMessage with variable: { type: MSG_TYPES.X }
    for m in re.finditer(r"type\s*:\s*([A-Z_]+\.[A-Z_]+)", content):
        sent.append(('constant_ref', m.group(1), m.start()))
    
    return sent

def extract_received_messages(content, file_type):
    """Find all message type handlers (case statements) in this file."""
    received = []
    
    # switch (msg.type) / switch (message.type) / switch (data.type)
    switch_blocks = re.findall(
        r"switch\s*\([^)]*\.type[^)]*\)\s*\{(.*?)(?=^}|\Z)",
        content, re.DOTALL | re.MULTILINE
    )
    
    for block in switch_blocks:
        cases = re.findall(r"case\s+['\"]([^'\"]+)['\"]", block)
        received.extend(cases)
    
    # Also: if (msg.type === 'X')
    for m in re.finditer(r"\.type\s*===?\s*['\"]([^'\"]+)['\"]", content):
        received.append(m.group(1))
    
    return list(set(received))  # dedupe

def find_message_mismatches(sent, received):
    """Flag types that are sent but have no handler, or vice versa."""
    sent_types = set(t for _, t, _ in sent if not '.' in t)
    received_types = set(received)
    
    orphaned_sends = sent_types - received_types
    orphaned_handlers = received_types - sent_types
    
    return orphaned_sends, orphaned_handlers


# ── Redis Analysis ────────────────────────────────────────────────────────────

def extract_redis_keys(content):
    """Find all Redis key patterns used in the file."""
    keys = []
    
    # redis.get(`...`) / redis.set(`...`) etc
    redis_ops = ['get', 'set', 'mGet', 'mSet', 'del', 'expire', 'incrBy', 'decrBy',
                 'hGet', 'hSet', 'hGetAll', 'zAdd', 'zRange', 'zScore', 'zRem',
                 'lPush', 'lPop', 'lRange']
    
    for op in redis_ops:
        pattern = rf"\.redis\.{op}\s*\(\s*[`'\"]([^`'\"]+)[`'\"]"
        for m in re.finditer(pattern, content):
            keys.append((op, m.group(1)))
    
    return keys

def analyze_redis_namespacing(keys):
    """Check if keys follow the gameName:userId:keyName pattern."""
    issues = []
    for op, key in keys:
        parts = key.split(':')
        if len(parts) < 2:
            issues.append(f"Key '{key}' has no namespace — may collide across posts/users")
        elif '${' not in key and len(parts) < 3:
            issues.append(f"Key '{key}' — consider adding user/post scoping")
    return issues


# ── Permission Check ─────────────────────────────────────────────────────────

def check_permissions(content, file_type):
    """Detect permission usage vs configuration."""
    issues = []
    
    if file_type == 'blocks_main':
        uses_redis = 'context.redis' in content or 'redis:' in content
        uses_realtime = 'context.realtime' in content
        uses_reddit_api = 'context.reddit.' in content
        
        configured_redis = 'redis: true' in content or "redis:true" in content
        configured_realtime = 'realtime: true' in content
        configured_reddit = 'redditAPI: true' in content or 'reddit_api' in content
        
        if uses_redis and not configured_redis:
            issues.append("Uses context.redis but 'redis: true' not found in Devvit.configure()")
        if uses_realtime and not configured_realtime:
            issues.append("Uses context.realtime but 'realtime: true' not found in Devvit.configure()")
        if uses_reddit_api and not configured_reddit:
            issues.append("Uses context.reddit but 'redditAPI: true' not found in Devvit.configure()")
    
    if file_type == 'devvit_yaml':
        # Check yaml permissions
        permissions = re.findall(r'-\s*(redis|realtime|reddit_api)', content)
        info(f"devvit.yaml permissions declared: {permissions or 'none found'}")
    
    return issues


# ── Bug Pattern Detection ─────────────────────────────────────────────────────

WEBVIEW_ANTIPATTERNS = [
    ('localStorage', 'localStorage in webview — data will NOT persist on Reddit app (iOS/Android). Use postMessage to blocks→Redis instead.'),
    ('sessionStorage', 'sessionStorage in webview — same issue as localStorage.'),
    ('fetch(', 'fetch() in webview — may be blocked by Reddit CSP. Route network calls through main.tsx.'),
    ('XMLHttpRequest', 'XMLHttpRequest in webview — same CSP issue as fetch.'),
]

BLOCKS_ANTIPATTERNS = [
    ('window.', 'window object in blocks layer — not available. Blocks run in React Native, not a browser.'),
    ('document.', 'document object in blocks layer — not available.'),
    ('localStorage', 'localStorage in blocks layer — not available. Use Redis.'),
    ("type: '", "Raw string message type — use a named constant instead (e.g., MSG_TYPES.SCORE_UPDATE)."),
    ('type: "', "Raw string message type — use a named constant instead."),
]

def check_antipatterns(content, file_type):
    issues = []
    patterns = []
    
    if file_type == 'webview_game' or file_type == 'webview_html':
        patterns = WEBVIEW_ANTIPATTERNS
    elif file_type == 'blocks_main':
        patterns = BLOCKS_ANTIPATTERNS
    
    for pattern, message in patterns:
        if pattern in content:
            # Get line number
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if pattern in line:
                    issues.append((i, message))
                    break  # only flag first occurrence
    
    return issues


# ── Surgical Entry Points ─────────────────────────────────────────────────────

COMMON_TICKETS = {
    'score': ['score', 'points', 'tally', 'counter'],
    'sound': ['audio', 'sound', 'play', 'AudioContext', 'oscillator'],
    'powerup': ['powerup', 'shield', 'boost', 'pickup', 'collectible'],
    'leaderboard': ['leaderboard', 'highScore', 'top', 'zRange', 'zAdd'],
    'physics': ['velocity', 'gravity', 'friction', 'collision', 'bounce'],
    'render': ['draw', 'render', 'paint', 'ctx.', 'fillRect', 'requestAnimationFrame'],
    'input': ['keydown', 'keyup', 'mousedown', 'touchstart', 'click', 'addEventListener'],
    'init': ['init', 'start', 'reset', 'READY', 'INIT'],
    'player': ['player', 'character', 'hero', 'worm', 'pHP', 'pGut'],
}

def find_entry_points(content, ticket_keyword=None):
    """Find functions relevant to a ticket keyword."""
    if not ticket_keyword:
        return []
    
    keyword_lower = ticket_keyword.lower()
    relevant_systems = []
    
    for system, keywords in COMMON_TICKETS.items():
        if any(kw.lower() in keyword_lower for kw in keywords) or keyword_lower in system:
            relevant_systems.append(system)
    
    results = []
    lines = content.split('\n')
    
    for system in relevant_systems:
        for kw in COMMON_TICKETS[system]:
            for i, line in enumerate(lines, 1):
                if re.search(rf'\b{re.escape(kw)}\b', line, re.IGNORECASE):
                    fn_context = find_enclosing_function(lines, i-1)
                    results.append({
                        'line': i,
                        'keyword': kw,
                        'system': system,
                        'content': line.strip(),
                        'function': fn_context,
                    })
                    break  # one hit per keyword is enough
    
    return results

def find_enclosing_function(lines, line_idx):
    """Walk backwards from a line to find the enclosing function name."""
    for i in range(line_idx, max(0, line_idx - 30), -1):
        m = re.search(r'function\s+(\w+)\s*\(', lines[i])
        if m:
            return m.group(1)
        m = re.search(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', lines[i])
        if m:
            return m.group(1)
        m = re.search(r'(\w+)\s*:\s*(?:async\s*)?(?:function\s*)?\(', lines[i])
        if m:
            return m.group(1)
    return None


# ── Function Registry ─────────────────────────────────────────────────────────

def extract_functions(content):
    """Get all function names and their line numbers."""
    functions = []
    
    # function name(...)
    for m in re.finditer(r'^(?:async\s+)?function\s+(\w+)\s*\(', content, re.MULTILINE):
        line = content[:m.start()].count('\n') + 1
        functions.append((line, m.group(1), 'function'))
    
    # const name = (...) => / const name = async (...) =>
    for m in re.finditer(r'^const\s+(\w+)\s*=\s*(?:async\s*)?\(', content, re.MULTILINE):
        line = content[:m.start()].count('\n') + 1
        functions.append((line, m.group(1), 'arrow'))
    
    functions.sort()
    return functions


# ── Main Report ───────────────────────────────────────────────────────────────

def run(filepath, ticket=None):
    path = Path(filepath)
    content = read_file(filepath)
    file_type = detect_file_type(path, content)
    
    lines = content.split('\n')
    
    print(f"\n{'#'*60}")
    print(f"  DEVVIT INSPECTOR — Contractor Brief")
    print(f"  File: {path.name}")
    print(f"  Type: {file_type}")
    print(f"  Size: {len(lines)} lines, {len(content):,} chars")
    print(f"{'#'*60}")
    
    # ── Bridge Messages
    section("MESSAGE BRIDGE")
    
    sent = extract_sent_messages(content, file_type)
    received = extract_received_messages(content, file_type)
    
    subsection("Sent message types")
    if sent:
        for direction, msg_type, pos in sent:
            line_num = content[:pos].count('\n') + 1
            info(f"line {line_num:4d}  [{direction}]  type: '{msg_type}'")
    else:
        info("None found")
    
    subsection("Handled message types (case statements)")
    if received:
        for t in sorted(received):
            info(f"  case '{t}'")
    else:
        info("None found")
    
    orphaned_sends, orphaned_handlers = find_message_mismatches(sent, received)
    if orphaned_sends:
        subsection("⚠️  SENT but NO handler found")
        for t in orphaned_sends:
            warn(f"type '{t}' is sent but has no case handler — will silently do nothing")
    if orphaned_handlers:
        subsection("ℹ️  Handlers with no matching send")
        for t in orphaned_handlers:
            info(f"case '{t}' — no matching postMessage found in this file (may be in the other file)")
    
    # ── Redis
    if file_type == 'blocks_main':
        section("REDIS USAGE")
        keys = extract_redis_keys(content)
        if keys:
            for op, key in keys:
                info(f"redis.{op}('{key}')")
            ns_issues = analyze_redis_namespacing(keys)
            for issue in ns_issues:
                warn(issue)
        else:
            info("No Redis calls found in this file")
    
    # ── Permissions
    section("PERMISSIONS")
    perm_issues = check_permissions(content, file_type)
    if perm_issues:
        for issue in perm_issues:
            warn(issue)
    else:
        ok("No permission mismatches detected")
    
    # ── Bug Patterns
    section("BUG PATTERNS")
    antipatterns = check_antipatterns(content, file_type)
    if antipatterns:
        for line_num, msg in antipatterns:
            flag(f"line {line_num}: {msg}")
    else:
        ok("No known antipatterns detected")
    
    # ── Function Registry
    section("FUNCTION REGISTRY")
    functions = extract_functions(content)
    if functions:
        for line_num, name, fn_type in functions[:30]:
            info(f"line {line_num:4d}  {name}()")
        if len(functions) > 30:
            info(f"... and {len(functions)-30} more")
    else:
        info("No named functions found")
    
    # ── Ticket Entry Points
    if ticket:
        section(f"ENTRY POINTS FOR TICKET: '{ticket}'")
        entry_points = find_entry_points(content, ticket)
        if entry_points:
            for ep in entry_points[:10]:
                fn = f" [in {ep['function']}()]" if ep['function'] else ""
                info(f"line {ep['line']:4d}{fn}  → {ep['content'][:70]}")
        else:
            info(f"No specific entry points found for '{ticket}' — use function registry above")
    
    # ── Contractor Recommendation
    section("CONTRACTOR RECOMMENDATION")
    
    if file_type == 'blocks_main':
        info("This is the BLOCKS side (main.tsx)")
        info("Good for: Redis reads/writes, Reddit API calls, message routing, leaderboards")
        info("Bad for: any game logic, canvas, physics, rendering")
    elif file_type == 'webview_game':
        info("This is the WEBVIEW GAME side (game.js)")
        info("Good for: all game logic, rendering, input, audio, physics")
        info("Bad for: saving data, Reddit API, knowing who the user is")
    elif file_type == 'webview_html':
        info("This is the WEBVIEW HTML shell (index.html)")
        info("Good for: layout, loading game.js, initial setup")
    elif file_type == 'devvit_yaml':
        info("This is the app config (devvit.yaml)")
        info("Check: permissions match what main.tsx actually uses")
    
    if orphaned_sends:
        print()
        warn("HIGHEST PRIORITY: Fix orphaned message sends before doing anything else")
        warn("These are silent failures — the game sends but nobody listens")
    
    print(f"\n{'─'*60}")
    print(f"  Inspector complete. Now grep for your specific ticket target.")
    print(f"{'─'*60}\n")


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 devvit_inspector.py <filepath> [--ticket 'add shield powerup']")
        sys.exit(1)
    
    filepath = sys.argv[1]
    ticket = None
    
    if '--ticket' in sys.argv:
        idx = sys.argv.index('--ticket')
        if idx + 1 < len(sys.argv):
            ticket = sys.argv[idx + 1]
    
    run(filepath, ticket)
