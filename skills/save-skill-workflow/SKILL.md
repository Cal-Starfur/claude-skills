[Fresh from GitHub: 8605047]

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

---

## Error Handling & Edge Cases

### present_files Fails Silently (No Save Skill Button Appears)

If `present_files` is called but the Save Skill button never appears in the UI:

1. **Most common cause:** the file path is wrong. The button only appears for files in `/mnt/user-data/outputs/`. Verify:
   ```bash
   ls -la /mnt/user-data/outputs/SKILL.md
   ```
   If the file isn't there, write it first before calling `present_files`.

2. **Second most common cause:** the file was written but `present_files` was called with a different path (e.g. a `/tmp/` path). Always call `present_files` with the `/mnt/user-data/outputs/SKILL.md` path, not the source path.

3. **If the user says the button appeared but disappeared** — this can happen if a follow-up message was sent immediately after. The Save Skill button is attached to the message that called `present_files` — it doesn't disappear, but it may scroll out of view. Tell the user to scroll up to find it.

4. **If the file is confirmed at the right path and `present_files` was called correctly but still no button** — re-call `present_files` once more without explanation. If it still doesn't appear after two attempts, tell the user to copy the skill content directly from the chat and save it manually.

5. **Never tell the user the skill is saved when `present_files` hasn't confirmed it.** The button is the confirmation — without it, the skill is not saved to their project.

---

### Skill Is >500 Lines — Should It Be Right-Sized First?

A SKILL.md over 500 lines is a signal the skill may be doing too much. Before saving a large skill:

1. **Ask: does this skill have one clear job?** If it's doing three different things that could each be their own skill, right-size it first. Saving a bloated skill embeds the complexity permanently.

2. **Check for script content.** Skills should contain instructions and workflow steps — not embedded Python scripts of >50 lines. If large chunks are scripts, extract them to a `scripts/` subfolder in the repo and reference them by path in the skill.

3. **When to save anyway (>500 lines is fine):**
   - The skill is complex but genuinely single-purpose (e.g. `wigglers-architecture` at ~450 lines is reference material, not bloat)
   - The content is reference tables, examples, and edge cases — not duplicated logic
   - Splitting it would require loading two skills to do one job

4. **When to right-size first:**
   - The skill contains two or more distinct workflows that are each independently useful
   - The skill has >200 lines of embedded scripts that belong in `scripts/`
   - The trigger description is trying to cover too many unrelated use cases

5. If in doubt, save it as-is and flag it in the audit:
   > "This skill is [N] lines — saved as-is. Recommend reviewing for right-sizing in a future audit session."
