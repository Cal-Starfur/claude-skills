---
name: Save Skill Workflow
description: How to create and save a Claude skill with the one-click Save Skill button. Use this whenever you need to package knowledge or workflows into a reusable skill for any project, or when a user says "turn this into a skill", "save this as a skill", "make this reusable", "package this workflow", or asks how to avoid a 404 skill download error, how to update an existing skill, or how to get the Save skill button to appear. CRITICAL WORKFLOW: After creating or updating ANY skill, ALWAYS immediately write it to /mnt/user-data/outputs/SKILL.md and call present_files — every time, without being asked. Never skip this step. Backup: if the user says "i didn't get the save skill", do it immediately without explanation.
---

# How to Create & Save a Claude Skill (Zero Friction Method)

Produces the **"Save skill"** button in Claude's UI — one-click install, no zipping or re-uploading.

---

## The Magic Formula

Three things must be true to get the Save Skill button:

1. **Filename must be `SKILL.md`** — all caps, exact spelling
2. **File must be in the outputs root** — `/mnt/user-data/outputs/SKILL.md`
3. **File must start with YAML frontmatter** — `name` and `description` fields

If any of these are wrong you get a plain markdown download or a 404.

---

## The Exact Steps

### Step 1 — Write the skill content
Draft your skill as a markdown document with YAML frontmatter.

### Step 2 — Create the file at the correct path
```bash
cat > /mnt/user-data/outputs/SKILL.md << 'SKILLEOF'
---
name: Your Skill Name
description: When to load this skill and what it does. Be specific.
---

# Skill Title

Your skill content here.
SKILLEOF
```

### Step 3 — Call present_files
```python
present_files(['/mnt/user-data/outputs/SKILL.md'])
```

This surfaces the Save Skill button. The user clicks it once — done.

---

## Updating an Existing Skill

Same process — overwrite the file at the same path and call `present_files` again.
The Save Skill button will update the existing skill in place.

```bash
# Overwrite existing
cat > /mnt/user-data/outputs/SKILL.md << 'SKILLEOF'
---
name: Same Skill Name As Before
description: Updated description.
---
...updated content...
SKILLEOF
```

Then `present_files(['/mnt/user-data/outputs/SKILL.md'])`.

---

## Multi-File Skills (scripts/ and references/)

Some skills have companion files (Python scripts, reference docs) stored in `scripts/` or `references/` subfolders in `Cal-Starfur/claude-skills`. The SKILL.md is still the only thing that gets saved via the Save Skill button — the companion files live in the repo and are fetched at runtime by the bootstrap block inside SKILL.md.

**Pattern for multi-file skills:**
1. Push companion files to `skills/{name}/scripts/` in `claude-skills` via github-sync
2. Write SKILL.md with a bootstrap block that fetches them from GitHub at session start
3. Save SKILL.md via the Save Skill button as normal

The user never needs to manually manage the companion files — the bootstrap handles it automatically.

---

## Hard Rules

1. **Always present_files immediately** after writing SKILL.md — never wait to be asked
2. **Never name it anything other than SKILL.md** — `my-skill.md`, `SKILL (1).md` etc. will not trigger the button
3. **Frontmatter must be first** — even a blank line before `---` breaks it
4. **One SKILL.md at a time** — if saving multiple skills in one session, present each one separately and wait for confirmation before presenting the next
5. **If the user says "I didn't get the save skill button"** — re-run present_files immediately, no explanation needed

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Got a download, not Save Skill | File not named exactly `SKILL.md` |
| 404 error on save | Frontmatter missing or malformed — must start with `---` on line 1 |
| Save Skill button missing | `present_files` not called, or file not in `/mnt/user-data/outputs/` |
| Skill saved but not loading | Description trigger words too vague — make description more specific |
