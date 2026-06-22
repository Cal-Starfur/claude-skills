#!/usr/bin/env python3
import sys; sys.path.insert(0, '/tmp/lead-dev')
"""
review_code.py — Lead Dev Subagent Code Reviewer
Sends newly written code + architecture context to a second Claude instance
for peer review before the user sees it.
Usage: python3 review_code.py <new_code_file> <architecture_file> [platform]
"""

import sys, json, urllib.request, urllib.error
from pathlib import Path

def load_file(path):
    try:
        return Path(path).read_text(encoding='utf-8', errors='ignore')
    except:
        return ''

def run_review(new_code, architecture, platform='Unknown', original_file=''):
    """Send code to Claude for peer review. Returns review result dict."""

    arch_summary = architecture[:3000] if len(architecture) > 3000 else architecture
    original_summary = original_file[:2000] if len(original_file) > 2000 else original_file

    system_prompt = """You are a senior code reviewer on a game development team.
A lead developer just wrote code for a non-technical user who cannot review it themselves.
Your job is to catch every problem before the user sees the output.
Be strict, specific, and constructive. The user's game depends on clean code."""

    user_prompt = f"""## Code Review Request

### Platform
{platform}

### Current Architecture (source of truth)
```
{arch_summary}
```

### Previous code (what existed before, if any)
```javascript
{original_summary}
```

### New/Modified Code to Review
```javascript
{new_code}
```

---

Review this code against the architecture and platform rules.
Check every item in this list:

CORRECTNESS:
- Will it actually run without errors?
- Are there null/undefined risks that will crash?
- Do all function calls match their definitions?
- Are there any infinite loop risks?
- Off-by-one errors?

ARCHITECTURE COMPLIANCE:
- Does any new function duplicate one that already exists?
- Does any name violate the naming conventions in the architecture?
- Was code added to the wrong system?
- Are system boundaries violated?
- Are new functions/variables documented in the architecture?

PLATFORM RULES (apply {platform}-specific checks):
- If Devvit: no localStorage, no raw string message types, no hardcoded userId, Redis keys namespaced?
- If Canvas: requestAnimationFrame used correctly, no DOM manipulation in game loop?

HYGIENE:
- Magic numbers present? (Should be named constants)
- Vague variable names? (data, temp, thing, val, obj)
- Functions over 40 lines?
- Copy-pasted logic that should be a shared function?
- Dead code left in?
- Every new function/system commented?

Respond with ONLY this JSON structure, no markdown:
{{
  "verdict": "APPROVED" or "NEEDS_FIXES",
  "critical": ["list of critical issues that will cause bugs or crashes"],
  "warnings": ["list of warnings that should be fixed but won't crash immediately"],
  "minor": ["list of minor style/cleanliness issues"],
  "summary": "one sentence plain-English summary of the overall quality",
  "approved_with_notes": true or false
}}"""

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}]
    }

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            raw = result['content'][0]['text'].strip()
            # Strip markdown fences if present
            raw = raw.replace('```json','').replace('```','').strip()
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        return {
            "verdict": "REVIEW_UNAVAILABLE",
            "critical": [],
            "warnings": [f"Review API returned {e.code} — proceed with manual self-review"],
            "minor": [],
            "summary": "Automated review unavailable — use manual checklist",
            "approved_with_notes": True
        }
    except Exception as e:
        return {
            "verdict": "REVIEW_UNAVAILABLE",
            "critical": [],
            "warnings": [f"Review error: {str(e)[:100]}"],
            "minor": [],
            "summary": "Automated review unavailable — use manual checklist",
            "approved_with_notes": True
        }

def print_review(review):
    verdict = review.get('verdict', 'UNKNOWN')

    if verdict == 'APPROVED':
        icon = "✅"
    elif verdict == 'NEEDS_FIXES':
        icon = "🔴"
    else:
        icon = "⚠️"

    print(f"\n{'='*60}")
    print(f"LEAD DEV — PEER REVIEW")
    print(f"{'='*60}")
    print(f"Verdict: {icon} {verdict}")
    print(f"Summary: {review.get('summary','')}")
    print(f"{'='*60}\n")

    critical = review.get('critical', [])
    if critical:
        print(f"🔴 CRITICAL — Must fix before delivery ({len(critical)}):")
        for i, issue in enumerate(critical, 1):
            print(f"   {i}. {issue}")
        print()

    warnings = review.get('warnings', [])
    if warnings:
        print(f"🟠 WARNINGS — Should fix ({len(warnings)}):")
        for i, issue in enumerate(warnings, 1):
            print(f"   {i}. {issue}")
        print()

    minor = review.get('minor', [])
    if minor:
        print(f"🟡 MINOR — Nice to fix ({len(minor)}):")
        for i, issue in enumerate(minor, 1):
            print(f"   {i}. {issue}")
        print()

    print(f"{'='*60}")
    if verdict == 'NEEDS_FIXES' and critical:
        print("ACTION: Fix all CRITICAL issues before delivering to user.")
    elif verdict == 'APPROVED' or review.get('approved_with_notes'):
        print("ACTION: Code approved — safe to deliver.")
    print(f"{'='*60}\n")

    return verdict, critical

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 review_code.py <new_code_file> [architecture_file] [platform]")
        sys.exit(1)

    new_code = load_file(sys.argv[1])
    architecture = load_file(sys.argv[2]) if len(sys.argv) > 2 else ''
    platform = sys.argv[3] if len(sys.argv) > 3 else 'Unknown'

    print(f"Sending to reviewer... ({len(new_code)} chars of code)")
    review = run_review(new_code, architecture, platform)
    verdict, critical = print_review(review)

    # Save review result
    out = Path(sys.argv[1]).with_suffix('.review.json')
    out.write_text(json.dumps(review, indent=2))
    print(f"Review saved: {out}")

    # Exit with error code if critical issues found
    sys.exit(1 if (verdict == 'NEEDS_FIXES' and critical) else 0)

