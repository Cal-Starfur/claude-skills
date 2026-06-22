---
name: skill-audit
description: Load this skill whenever the user wants to run a skill audit, score a skill, track skill performance over time, update the claude-skills repo, or document skill improvements. Triggers on phrases like "audit the skills", "score this skill", "how are our skills doing", "push the audit to GitHub", "update the skill tracker", "run a deep audit on X", or "log this to the changelog". Also triggers automatically when session-summary is run and a skill was modified or created this session, or any skill's score was noted as below 75. This is the memory and tracking system for the entire Claude skill ecosystem — it knows the repo location, scoring methodology, current baseline scores, and the workflow for running and saving audits.
---

# Skill Audit Skill

Tracks, scores, and improves the Claude skill ecosystem over time.
All audit results live at: **https://github.com/Cal-Starfur/claude-skills**

---

## Repo Structure

```
claude-skills/                        ← Cal-Starfur/claude-skills on GitHub
├── README.md                         — skill roster + audit methodology overview
├── CHANGELOG.md                      — running log of all skill changes
└── audits/
    └── 2026-06-19-baseline.md        — first baseline audit (all 9 skills scored)
```

**Push target:** `Cal-Starfur/claude-skills` branch `main`
**Token:** provided fresh each session — never stored here

---

## Scoring Methodology

Each skill scored 0–100 across four dimensions:

| Dimension | What it measures |
|---|---|
| **Trigger** | Does the description clearly tell Claude when to load it? |
| **Content quality** | Is the instruction body accurate and well-organized? |
| **Completeness** | Are edge cases, fallbacks, and hard rules covered? |
| **Freshness** | How likely is the skill to drift out of sync with reality? |

**Overall score** = weighted average (all four dimensions equal weight for now)

**Grade bands:**
- 80–100 = ✅ Strong
- 65–79  = 🟢 Good
- 50–64  = 🟡 OK — needs improvement
- <50    = 🔴 Weak — fix before next session
- <50    = 🔴 Critical — do not use until fixed (see below)

---

## Baseline Scores — June 19, 2026

| Skill | Trigger | Quality | Complete | Fresh | **Overall** |
|---|---|---|---|---|---|
| github-sync | 90 | 88 | 92 | 80 | **88** |
| lead-dev | 85 | 90 | 88 | 75 | **85** |
| contractor | 82 | 85 | 88 | 72 | **82** |
| devvit-pipeline | 100 | 87 | 100 | 83 | **92** |
| wigglers-architecture | 88 | 75 | 70 | 55 | **72** |
| save-skill-workflow | 75 | 100 | 100 | 100 | **93** |
| canvas-art-optimizer | 75 | 70 | 65 | 60 | **68** |
| png-canvas-art-optimizer | 65 | 60 | 55 | 58 | **60** |
| session-health | 95 | 98 | 98 | 97 | **97** |

**Average: 84/100** (incl. save-skill-workflow update) | Last audited: 2026-06-19

---

## Priority Fix List (from baseline)

| Priority | Skill | Fix needed |
|---|---|---|
| 🔴 High | png-canvas-art-optimizer | Document actual iteration loop + vision API approach |
| 🔴 High | wigglers-architecture | Auto-enforce github-sync pull; remove hardcoded version |
| 🟡 Med | save-skill-workflow | Fix copy-paste error in example template |
| 🟡 Med | lead-dev | Make session log examples dynamic |
| 🟡 Med | contractor | Clarify handoff boundary with lead-dev |
| 🟢 Low | github-sync | Remove hardcoded V62 from examples |
| 🟢 Low | devvit-pipeline | Add stale-warning to devvit upload workaround section |

---

## Audit Workflow (Every Session)

### Running a deep audit on one skill

1. Read the skill's SKILL.md fully via `view`
2. Score it on all four dimensions (0–100 each)
3. Write findings: strengths, warnings, fixes needed
4. Compare to baseline score — did it improve?
5. Push updated audit to `audits/YYYY-MM-DD-skillname.md` in claude-skills repo
6. Update `CHANGELOG.md` with one-line entry

### Pushing to claude-skills repo

```python
# Bootstrap github-sync first (always)
# Then set token and point at claude-skills repo:
import json
from pathlib import Path
Path('/tmp/github-sync/memory').mkdir(parents=True, exist_ok=True)
Path('/tmp/github-sync/memory/github_config.json').write_text(json.dumps({
    'token': '<token from user>',
    'owner': 'Cal-Starfur',
    'repo': 'claude-skills',
    'branch': 'main'
}, indent=2))
```

Then use `propose_commit.py` to stage + show diff + push with approval.

### Audit file naming convention

```
audits/YYYY-MM-DD-baseline.md          ← first run ever
audits/YYYY-MM-DD-skillname.md         ← deep audit on one skill
audits/YYYY-MM-DD-full.md              ← re-score all skills
```

### CHANGELOG entry format

```
## YYYY-MM-DD — Description

- What changed
- Skill: old score → new score (if applicable)
- Why the change was made
```

---

## Running the Full Audit Dashboard

To regenerate the visual dashboard in chat:

> "Run skill audits on all our skills"

Claude will:
1. Read all skill SKILL.md files
2. Score each on the four dimensions
3. Show the interactive dashboard widget
4. Compare scores to baseline (table above)
5. Highlight improvements or regressions

---

## What to Audit Next

After each session, note what was audited and what's next:

- **Done:** Baseline audit (all 9 skills) — 2026-06-19
- **Next:** Deep audit `png-canvas-art-optimizer` (score: 60 — lowest)
- **Then:** Deep audit `wigglers-architecture` (freshness risk: 55)

---

## Key Insight from Baseline

The **core Devvit workflow trio** (github-sync, lead-dev, contractor) is solid — scores 82–88.
The **biggest risk** is freshness: skills that have version numbers or file sizes baked in
will drift silently every session. `wigglers-architecture` is the most exposed.
The **weakest skill** is `png-canvas-art-optimizer` — it promises behavior it doesn't document.

---

## Edge Cases

### Skill Scores Below 50 — Critical Triage Protocol

A score below 50 means the skill is actively harmful to load — it will give Claude wrong instructions, wrong paths, or wrong expectations. This is different from a low-scoring skill (65–79) which is merely incomplete.

**Immediate actions when a skill scores below 50:**

1. **Flag it as DO NOT LOAD** in the audit output:
   > "⛔ [skill-name] scored [N]/100 — this skill should not be loaded until fixed. Loading it may cause worse outcomes than having no skill at all."

2. **Identify which dimension is lowest** — this determines the fix type:
   - Trigger < 50 → the skill will never load when needed, or load when it shouldn't. Fix the description first.
   - Quality < 50 → the instructions are wrong, contradictory, or dangerous. Fix the content before anything else.
   - Completeness < 50 → the skill has no error handling and will fail silently in real use. Add edge cases.
   - Freshness < 50 → the skill has hardcoded values that are almost certainly wrong. Strip all hardcoded specifics.

3. **Do not attempt partial fixes on a sub-50 skill in the same session as other work.** It needs a dedicated focused session. Log it as the top priority for next session:
   > "Logging [skill-name] as P0 — needs dedicated fix session before it can be used."

4. **Write the audit finding to GitHub** even if the fix isn't done yet:
   ```
   audits/YYYY-MM-DD-[skillname]-critical.md
   ```
   Document: what scored below 50, why, what the fix requires, estimated effort.

5. **If the skill is currently wired into a session-start flow** (e.g. session-health, github-sync) and it scored below 50 — tell the user immediately:
   > "This skill is part of your session startup — running sessions without fixing it first is risky. I'd recommend fixing it before the next Wigglers session."

6. **Below 30 = rewrite, not patch.** A skill scoring below 30 has fundamental structural problems that can't be fixed incrementally. Flag it for a full rewrite and treat the current version as retired until the rewrite is complete.

