# Skill Buildout Plan

Based on gap analysis from 2026-06-19. Build order is priority × effort.

---

## Phase 1 — Owner Control (Build First)

### 1. session-summary skill

**What:** After every session, output two plain-English paragraphs:
what changed, what system it touched, what could break, push Y/N recommendation.

**Why first:** Highest leverage for a non-fluent owner. Closes the biggest
trust gap between Claude doing work and owner understanding what happened.

**Triggers:** End of any coding session. "What changed?" "Give me the summary."
"Should I push?"

**Key rules:**
- No code in the summary — plain English only
- Must name every file touched
- Must flag anything fragile
- Must end with explicit push recommendation + reason

**Target score:** 90+
**Estimated build time:** 1 session

---

### 2. preflight-checklist skill

**What:** A gate that runs before any code change starts. Checks: correct
file version loaded, architecture doc fresh, last session summary reviewed,
scope of change agreed in plain English before touching anything.

**Why second:** Prevents the "stale context" risk — Claude starting work
with outdated files and making confident-sounding wrong changes.

**Triggers:** Start of any session where code will be changed.
"Let's work on the game." Any file upload + change request.

**Key rules:**
- Must pull fresh files from GitHub before proceeding
- Must state scope in one sentence and get confirmation
- Hard stop if architecture doc is missing or >1 session old
- Output: READY TO PROCEED or BLOCKED (with reason)

**Target score:** 88+
**Estimated build time:** 1 session

---

### 3. rollback skill

**What:** Safe path back to last known-good state. Identifies the last
clean commit, shows what would be lost, gets confirmation, reverts.

**Why third:** Completes the safety triangle — summary (understand),
preflight (prevent), rollback (recover).

**Triggers:** "Something broke." "Undo that." "Go back to before."
"The game is broken." "Revert."

**Key rules:**
- Never rollback without showing what will be lost
- Always identify the last commit where build passed
- Must confirm with owner before executing
- Log the rollback in CHANGELOG

**Target score:** 85+
**Estimated build time:** 1 session

---

## Phase 2 — Process Quality (Build After Phase 1 Stable)

### 4. feature-spec skill

Turn a plain-English idea into a one-page ticket before any code is written.
Fields: what it does, what system it touches, definition of done, risks.

### 5. test-scenario skill

For each feature, generate a human-readable checklist of things to click/check
to verify it works. Non-technical — owner can run this without Claude.

### 6. tech-debt-tracker skill

Every time contractor takes a shortcut, log it. Surface the log at session start.
Prevents "that thing we said we'd fix later" from disappearing forever.

---

## Build Conventions (for all new skills)

- Folder: `skills/{skill-name}/SKILL.md`
- Each skill pushed to `Cal-Starfur/claude-skills` on completion
- Audit run same session as build, score logged in `audits/`
- CHANGELOG and README updated every push
- Target: every new skill scores 85+ before it's considered done
