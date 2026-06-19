---
name: skill-audit
description: Load this skill whenever the user wants to run a skill audit, score a skill, track skill performance over time, update the claude-skills repo, or document skill improvements. Triggers on phrases like "audit the skills", "score this skill", "how are our skills doing", "push the audit to GitHub", "update the skill tracker", "run a deep audit on X", or "log this to the changelog". This is the memory and tracking system for the entire Claude skill ecosystem — it knows the repo location, scoring methodology, current baseline scores, and the workflow for running and saving audits.
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

---

## Baseline Scores — June 19, 2026

| Skill | Trigger | Quality | Complete | Fresh | **Overall** |
|---|---|---|---|---|---|
| github-sync | 90 | 88 | 92 | 80 | **88** |
| lead-dev | 85 | 90 | 88 | 75 | **85** |
| contractor | 82 | 85 | 88 | 72 | **82** |
| devvit-pipeline | 80 | 82 | 85 | 68 | **79** |
| wigglers-architecture | 88 | 75 | 70 | 55 | **72** |
| save-skill-workflow | 70 | 72 | 80 | 65 | **72** |
| canvas-art-optimizer | 75 | 70 | 65 | 60 | **68** |
| png-canvas-art-optimizer | 65 | 60 | 55 | 58 | **60** |
| session-health | 95 | 98 | 98 | 97 | **97** |

**Average: 77/100** (incl. session-health v2) | Last audited: 2026-06-19

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

