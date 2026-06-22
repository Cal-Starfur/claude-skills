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

```
