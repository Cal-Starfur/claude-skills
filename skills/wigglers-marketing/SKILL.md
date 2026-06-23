---
name: wigglers-marketing
description: Automatically generates Reddit marketing posts from a Wigglers Room dev session and pushes them to the hub calendar. Load this skill at the end of every Wigglers Room dev session, immediately after session-summary runs. Triggers on: "generate posts", "add to calendar", "marketing posts", "what should I post about this session", or automatically after session-summary completes for a Wigglers Room session. Reads the session summary output and commit history already in the conversation — never asks the user to re-explain what happened. Generates 2-3 ready-to-paste Reddit posts targeting the right communities for that specific content, then stages them for push to docs/post-calendar.html in the Wigglers_Room repo.
---

# Wigglers Marketing Skill

**One job: turn this dev session into Reddit posts and push them to the calendar.**

No manual form. No re-explaining. Read what's already in the conversation, generate the posts, push them. The user should never have to think about this.

---

## When to Run

This skill runs **automatically at session end**, right after session-summary completes.

| Trigger | Action |
|---|---|
| session-summary just completed for a Wigglers Room session | Run automatically — offer posts without being asked |
| "generate posts from this session" | Run immediately |
| "add to marketing calendar" | Run immediately |
| "what should I post about today" | Run immediately |
| "marketing posts" | Run immediately |
| User is wrapping up a Wigglers Room session | Offer: "Want me to generate Reddit posts from this session?" |

**Never wait for the user to ask if you can tell a session just ended.**

---

## Step 0 — Read the Session (Never Ask the User)

Everything needed is already in the conversation. Extract:

**From the session-summary output:**
- What shipped (specific features, fixes, bug names)
- What broke or surprised (these are the best stories)
- Which files changed
- Push recommendation (PUSH = safe to include link, HOLD = don't mention link yet)

**From the commit history visible in the conversation:**
- Session number (look for "S26", "Session 26", or version bumps)
- Devvit version (from `propose_commit.py` output or audit doc reads)
- Specific issue IDs that shipped (ISS-19, FEAT-2, etc.)

**From the conversation tone and content:**
- Any quotes, moments, or revelations that came up naturally
- Problems that took a long time to figure out
- Anything the user expressed frustration or excitement about

If the session was marketing/docs only (no game code): generate posts about the workflow, the hub, the planning process instead.

---

## Step 1 — Identify the 2-3 Best Stories

Not every commit is a post. Find the ones with narrative:

**Best stories:**
- Bug that was hard to find (especially: only showed in production, took multiple sessions, had a weird root cause)
- Feature that changed how the game feels
- Mechanic that surprised you or the player
- Performance improvement with real numbers (21k → 1 canvas call)
- Design decision that was debated or changed
- Something that broke and was fixed
- A moment of "oh that's why it wasn't working"

**Skip:**
- Routine version bumps
- Docs-only changes (unless the doc itself is interesting content)
- Config changes
- Dependency updates

---

## Step 2 — Match Stories to Communities

Each story has a natural home. Match it:

| Story type | Primary community | Secondary |
|---|---|---|
| Bug hunt, root cause, took sessions to find | r/gamedev | r/indiegaming |
| Performance fix with numbers | r/incremental_games | r/gamedev |
| Shared world mechanic, multiplayer consequence | r/incremental_games | r/GrowAGarden |
| Player experience, emotional hook | r/CozyGamers | r/neopets |
| AI dev workflow, Claude as co-dev | r/ClaudeAI | r/artificial |
| Devvit-specific technical story | r/devvit | r/gamedev |
| Death/rebirth mechanic | r/Tamagotchi | r/neopets |
| Weekly cycle, community event | r/GrowAGarden | r/incremental_games |
| Mobile dev workflow | r/iOSProgramming | r/SoloDev |
| Solo dev story, shipping moment | r/indiegaming | r/SoloDev |

---

## Step 3 — Generate the Posts

Write 2-3 posts. Rules:

**Voice:** Developer sharing genuinely. No marketing language. No hype. Honest about what went wrong. Write like a real Reddit post from a real person, not an announcement.

**Structure per post:**
- Title: specific, hooks the community, not clickbait
- Body: 150-250 words
- Opening: the situation in one sentence
- Middle: what happened, what was discovered, what it means for the game
- End: current status, brief game description, link placeholder [LINK] if PUSH session

**Title formulas that work for gaming subs:**
- "The [bug/mechanic/system] that [outcome] — here's why it happened"
- "After [N] sessions, [discovery/fix/moment]"
- "[Mechanic name] in [game] — why I designed it the way I did"
- "The [problem] that only showed in production — and how we finally found it"
- "My [AI/solo dev] workflow just [moment] — here's what that looks like"

**What to include:**
- Specific numbers if available (21k canvas ops → 1, 3 weeks to diagnose, Session 26)
- The Devvit version if it's a platform-specific story
- What the game is in one sentence at the end (always)
- [LINK] placeholder only if PUSH — never on HOLD sessions

**What to never include:**
- "Check out my game" without substance
- Vague "exciting update" language
- Marketing claims ("best idle game", "revolutionary mechanics")
- More than one [LINK] per post

---

## Step 4 — Assign Day Numbers

Find the current max day number in the calendar:
- The hub file at `docs/post-calendar.html` in `Cal-Starfur/Wigglers_Room`
- Look for the highest `"num":` value in the POSTS array
- Session-generated posts start at max + 1 and increment

Tag each generated post with:
```json
{
  "num": 151,
  "date": "Session 26",
  "subreddit": "r/incremental_games",
  "title": "...",
  "body": "...",
  "phase": "Phase 3 — Launch",
  "stream": "gamer",
  "session_generated": true
}
```

---

## Step 5 — Show the Posts and Get Approval

Present all generated posts clearly before pushing anything. For each:

```
POST 1 — r/incremental_games
Title: [title]

[body]

Communities: r/incremental_games (primary), r/gamedev (secondary)
Why: [one sentence]
```

Then ask: **"Add all 3 to the calendar? Or pick which ones?"**

Wait for approval. This is the same approval gate as github-sync — never push without a go-ahead.

---

## Step 6 — Push to GitHub

After approval, push the new posts to the calendar.

The calendar lives at `docs/post-calendar.html` in `Cal-Starfur/Wigglers_Room`.

**The push approach:**
The POSTS array is embedded as JSON in a `<script type="application/json">` tag in the HTML. Read the current file, parse the JSON, append the new posts, rebuild the file, push via the github-sync approve-before-push workflow.

```bash
# Bootstrap github-sync if not already done this session
python3 << 'BOOTSTRAP'
import urllib.request, json, base64, sys
from pathlib import Path
# [standard bootstrap — see github-sync skill]
BOOTSTRAP

# Read current calendar file
python3 /tmp/github-sync/scripts/sync_from_github.py read docs/post-calendar.html

# Parse, append, push
python3 << 'PUSH'
import re, json, base64
from pathlib import Path

# Read current file
content = Path('/tmp/github-sync/cache/docs/post-calendar.html').read_text()

# Find and parse the POSTS JSON
match = re.search(r'<script id="posts-data" type="application/json">(.*?)</script>', content, re.DOTALL)
posts = json.loads(match.group(1))

# Append new posts
new_posts = [
    # ... generated posts here
]
posts.extend(new_posts)

# Rebuild the file
new_json = json.dumps(posts, ensure_ascii=False, separators=(',',':'))
updated = content[:match.start(1)] + new_json + content[match.end(1):]

# Write to tmp for staging
Path('/tmp/new_calendar.html').write_text(updated)
PUSH

# Stage and push via github-sync approve-before-push
python3 /tmp/github-sync/scripts/propose_commit.py stage \
  /tmp/new_calendar.html docs/post-calendar.html \
  --message "Session [N]: add [X] marketing posts — [brief description]"

python3 /tmp/github-sync/scripts/propose_commit.py status
# [wait for approval]
python3 /tmp/github-sync/scripts/propose_commit.py push
```

**Commit message format:**
```
Session [N]: add [X] posts — [r/community], [r/community], [r/community]
```

---

## Step 7 — Confirm and Report

After push:

```
✓ Added [N] posts to the marketing calendar (Days [X]–[Y])

Day [X] — r/[community]: "[title]"
Day [X+1] — r/[community]: "[title]"
[...]

These will show up in the Gamer stream at:
https://cal-starfur.github.io/Wigglers_Room/post-calendar.html
```

---

## Hard Rules

1. **Never ask the user to re-explain the session.** Everything is in the conversation.
2. **Never generate posts for HOLD sessions** that include game links — the game isn't ready to share.
3. **Always get approval before pushing** — same gate as github-sync.
4. **Never generate more than 3 posts per session** — quality over quantity.
5. **Never use marketing language** — "exciting", "amazing", "revolutionary", "best". Just facts.
6. **Never cross-post identical content** — each post must be meaningfully different even if the topic overlaps.
7. **The form in the hub is the fallback** — this skill does the same thing automatically. Both should produce equivalent output.
8. **If no good story exists in the session** — say so. A short doc-only session might only produce 1 post or none. Don't pad.

---

## Community Posting Rules (Critical)

**r/incremental_games:**
- Self-promotion only in Friday thread
- Discussion/mechanic posts allowed any day — don't frame them as promo
- No IGM-made games (not applicable — ours is hand-built)

**r/GrowAGarden:**
- 18.6M members — post must be immediately compelling or it dies in seconds
- Frame as "for GaG players who want X" not "check out my game"

**r/playmygame:**
- Best place for direct launch posts — built for self-promotion
- Use [PC][Web] flair

**r/CozyGamers:**
- No technical language — vibe and feeling only
- Screenshots or GIFs perform better than text posts

**r/ClaudeAI:**
- This community loves specifics about Claude workflows
- Be honest about failures and friction — they'll respect it more than success stories

**r/gamedev / r/indiegaming:**
- Dev diary and honest retrospective tone only
- War stories outperform success stories

---

## Session Post History

Track generated posts in the conversation so you don't duplicate across sessions:

After each push, note:
```
Session [N] posts pushed:
- Day [X]: r/[community] — "[title]"
- Day [Y]: r/[community] — "[title]"
```

On the next session, don't generate posts about things already covered.

---

## Integration with Other Skills

**Runs after:** session-summary (reads its output directly)
**Uses:** github-sync (for the push)
**Updates:** docs/post-calendar.html in Wigglers_Room repo
**Also updates:** WIGGLERS_MARKETING_MASTER.md if the story is significant enough to add to the raw material section

**The full session-end sequence:**
1. session-summary runs → PUSH or HOLD recommendation
2. wigglers-marketing runs → 2-3 posts generated and staged
3. Approval → both the game code push AND the calendar update push
4. project-calendar syncs if 2+ tasks were completed
5. Session closes
