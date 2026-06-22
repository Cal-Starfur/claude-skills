#!/usr/bin/env python3
"""
version_bump.py — Lead Dev Version Manager
Increments version, stamps the file header, creates changelog entry.
Usage: python3 version_bump.py <game_filepath> [--arch <arch_filepath>] [--intent "what changed"]
"""

import sys, re, argparse
from pathlib import Path
from datetime import datetime

def get_current_version(content):
    """Extract version number from file or architecture doc."""
    patterns = [
        r'//\s*Version[:\s]+V?(\d+)',
        r'/\*\s*V(\d+)',
        r'Current Version.*?V(\d+)',
        r'V(\d+)',
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            return int(m.group(1))
    return None

def bump_version_in_file(content, old_v, new_v):
    """Update version references in the game file."""
    # Update comment header if exists
    content = re.sub(
        r'(//\s*(?:Version|V)[\s:]*V?)' + str(old_v),
        lambda m: m.group(1) + str(new_v),
        content
    )
    # Update version variable if exists
    content = re.sub(
        r"((?:const|let|var)\s+(?:version|VERSION|gameVersion)\s*=\s*['\"]?)V?" + str(old_v),
        lambda m: m.group(1) + 'V' + str(new_v),
        content
    )
    return content

def bump_version_in_architecture(arch_content, old_v, new_v, intent=''):
    """Update architecture doc with new version and changelog entry."""
    # Update current version line
    arch_content = re.sub(
        r'(\*\*Current Version:\*\*\s*)V?\d+',
        r'\g<1>V' + str(new_v),
        arch_content
    )
    # Update last updated
    today = datetime.now().strftime('%Y-%m-%d')
    arch_content = re.sub(
        r'(\*\*Last Updated:\*\*\s*)[\d-]+',
        r'\g<1>' + today,
        arch_content
    )
    # Add changelog entry
    changelog_entry = f"""
### V{new_v} — {today}
- **Intent:** {intent or '[describe what the user wanted]'}
- **Changed:** [list what was modified]
- **New systems:** [anything added]
- **Removed:** [anything deleted or deprecated]
- **Debt added:** [any shortcuts taken]
- **Next:** [what still needs doing]
"""
    # Insert after ## Changelog header
    arch_content = re.sub(
        r'(## Changelog\n)',
        r'\1' + changelog_entry,
        arch_content
    )
    return arch_content

def add_version_header(content, version, filename):
    """Add or update a version header comment at the top of the file."""
    today = datetime.now().strftime('%Y-%m-%d')
    header = f"// ═══════════════════════════════════════════════════════\n"
    header += f"// {filename} — V{version}\n"
    header += f"// Last modified: {today}\n"
    header += f"// Maintained by Lead Dev skill\n"
    header += f"// ═══════════════════════════════════════════════════════\n"

    # Remove existing header if present
    content = re.sub(r'^(//\s*[═=─-]{10,}.*?\n)+', '', content, flags=re.MULTILINE)

    # Add to top (after <!DOCTYPE or <html> if HTML file)
    if content.strip().startswith('<!DOCTYPE') or content.strip().startswith('<html'):
        # Insert after opening HTML tag
        content = re.sub(r'(<html[^>]*>)', r'\1\n<!-- ' + f'V{version} | {today}' + ' -->', content, count=1)
    else:
        content = header + '\n' + content

    return content

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('game_file', help='Path to game file')
    parser.add_argument('--arch', help='Path to GAME_ARCHITECTURE.md', default=None)
    parser.add_argument('--intent', help='What was the intent of this session', default='')
    parser.add_argument('--major', action='store_true', help='Force version bump even if no changes detected')
    args = parser.parse_args()

    game_path = Path(args.game_file)
    if not game_path.exists():
        print(f"Error: {args.game_file} not found")
        sys.exit(1)

    content = game_path.read_text(encoding='utf-8', errors='ignore')

    # Try to get version from architecture first, then file
    old_version = None
    arch_path = None

    if args.arch:
        arch_path = Path(args.arch)
    else:
        # Look for architecture file in same directory
        candidate = game_path.parent / 'GAME_ARCHITECTURE.md'
        if candidate.exists():
            arch_path = candidate

    if arch_path and arch_path.exists():
        arch_content = arch_path.read_text(encoding='utf-8', errors='ignore')
        old_version = get_current_version(arch_content)

    if old_version is None:
        old_version = get_current_version(content) or 1

    new_version = old_version + 1

    print(f"\n{'='*50}")
    print(f"LEAD DEV — VERSION BUMP")
    print(f"{'='*50}")
    print(f"File:    {game_path.name}")
    print(f"Version: V{old_version} → V{new_version}")
    if args.intent:
        print(f"Intent:  {args.intent}")
    print(f"{'='*50}\n")

    # Bump in game file
    new_content = bump_version_in_file(content, old_version, new_version)
    new_content = add_version_header(new_content, new_version, game_path.name)

    # Write updated game file
    game_path.write_text(new_content, encoding='utf-8')
    print(f"✓ Updated: {game_path}")

    # Bump in architecture
    if arch_path and arch_path.exists():
        arch_content = arch_path.read_text(encoding='utf-8', errors='ignore')
        new_arch = bump_version_in_architecture(arch_content, old_version, new_version, args.intent)
        arch_path.write_text(new_arch, encoding='utf-8')
        print(f"✓ Updated: {arch_path}")
        print(f"\n→ Fill in the V{new_version} changelog entry in GAME_ARCHITECTURE.md")

    print(f"\nOutput file stamped as V{new_version}")
    print(f"{'='*50}\n")
    return new_version

if __name__ == '__main__':
    main()

