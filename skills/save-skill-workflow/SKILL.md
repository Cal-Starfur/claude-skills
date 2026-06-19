---
name: Save Skill Workflow
description: How to create and save a Claude skill with the one-click Save Skill button. Use this whenever you need to package knowledge or workflows into a reusable skill for any project, or when a user says "turn this into a skill", "save this as a skill", "make this reusable", "package this workflow", or asks how to avoid a 404 skill download error, how to update an existing skill, or how to get the Save skill button to appear. CRITICAL WORKFLOW: After creating or updating ANY skill, ALWAYS immediately write it to /mnt/user-data/outputs/SKILL.md and call present_files — every time, without being asked. Never skip this step. Backup: if the user says "i didn't get the save skill", do it immediately without explanation.
---

# How to Create & Save a Claude Skill (Zero Friction Method)

Produces the Save skill button in Claude UI - one-click install, no zipping.

## The Magic Formula

Three things must be true:

1. Filename must be SKILL.md - all caps, exact spelling
2. File must be in the outputs root - /mnt/user-data/outputs/SKILL.md
3. File must start with YAML frontmatter - name and description fields

## The Exact Steps

### Step 1 - Write the skill content
Draft your skill as a markdown document with YAML frontmatter.

### Step 2 - Create the file
Use create_file tool or python:
```python
from pathlib import Path
Path("/mnt/user-data/outputs/SKILL.md").write_text(skill_content)
```

### Step 3 - Present it
```python
present_files(["/mnt/user-data/outputs/SKILL.md"])
```

### Step 4 - User clicks Save skill
One tap. Done. Live in Settings > Customize > Skills.

## Frontmatter Rules

- name - human-friendly label, max 64 characters
- description - critical: Claude reads this to decide when to auto-load
  - Be specific: name the project/domain, list what is inside, say when to trigger
  - Vague descriptions = skill never triggers automatically

Good description:
  Load this skill for any Wigglers Room session. Covers architecture, drain system, naming.

Bad description:
  Architecture reference for a game.

## What NOT to Do

- Do not name it skill.md (lowercase) - no Save button
- Do not put it in a subdirectory - causes 404
- Do not skip the YAML frontmatter - skill will not auto-trigger
- Do not copy the save-skill-workflow description into example templates
  Use a placeholder like "When to load this and what it does."

## Multi-File Skills (Bundled Assets)

For skills that need scripts, embed them in SKILL.md using this pattern:

## EMBEDDED SCRIPT: script-name.py
Write this to /tmp/my-skill/script-name.py

(python code block)

Then add a bootstrap Step 0 that extracts embedded scripts to /tmp/ via regex.
See session-health or github-sync skills for working examples.

## Skill Content Best Practices

- One skill per workflow - focused skills compose better
- Lead with the most-referenced info
- Include gotchas - things that caused bugs or confusion before
- Step 0 = bootstrap if skill has embedded scripts
- File editing protocol if for a codebase

## Updating a Skill

1. Edit the content
2. Write to /mnt/user-data/outputs/SKILL.md
3. Call present_files - user clicks Save skill to overwrite

## Example Skill Template

---
name: My Project Skill
description: Load when working on [project]. Covers [what it does]. Triggers on [keywords].
---

# My Project Skill

## Quick Reference
[Most-used constants or commands]

## Architecture
[How the system works]

## Common Gotchas
[Things that caused bugs]

## Safe Editing Protocol
[How to read/edit/output files]

---

Updated: June 2026 - added multi-file guidance, fixed copy-paste error in example template
