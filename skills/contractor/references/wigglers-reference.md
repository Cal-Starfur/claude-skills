## DEVVIT ARCHITECTURE — Complete Mental Model

This is the full picture of how a Devvit game works. Read this before touching any Devvit file.

### The Two Worlds

```
┌─────────────────────────────────────────────────────────────┐
│                    REDDIT APP (Blocks)                       │
│                      src/main.tsx                            │
│                                                             │
│  • Runs in Reddit's native environment (iOS/Android/Web)    │
│  • Written in TypeScript / JSX                              │
│  • Uses Devvit Blocks UI (<vstack>, <hstack>, <image> etc)  │
│  • Has access to: Redis, Reddit API, Realtime, Scheduler    │
│  • NO access to: DOM, window, localStorage, fetch           │
│  • Handles: post creation, user data, leaderboards          │
│  • Communicates UP via: context.ui.webView.postMessage()    │
│  • Receives DOWN via: onMessage handler                     │
└────────────────────┬────────────────────────────────────────┘
                     │  postMessage (JSON only)
                     │  ↕  bidirectional bridge
┌────────────────────▼────────────────────────────────────────┐
│                   WEBVIEW (Game)                             │
│              webroot/index.html + game.js                    │
│                                                             │
│  • Standard HTML5 page running in an iframe/webview         │
│  • Full browser APIs: canvas, audio, localStorage* (NO!)    │
│  • Has access to: DOM, Canvas, Web Audio, fetch             │
│  • NO access to: Reddit API, Redis, user data directly      │
│  • Communicates UP via: window.parent.postMessage()         │
│  • Receives DOWN via: window.addEventListener('message')    │
└─────────────────────────────────────────────────────────────┘
```

**The #1 rule:** Game logic lives in the webview. Reddit/data logic lives in main.tsx. Never cross this line.

---

### The postMessage Bridge — Exact Syntax

**Webview → Blocks (game sending TO Reddit):**
```javascript
// In game.js / index.html
window.parent.postMessage({
  type: 'SCORE_UPDATE',     // always a named constant, never a raw string
  payload: { score: 1500 }
}, '*');
```

**Blocks → Webview (Reddit sending TO game):**
```typescript
// In main.tsx
context.ui.webView.postMessage('myWebView', {
  type: 'INIT_DATA',
  payload: { username: user.username, highScore: 0 }
});
```

**Receiving in Blocks (main.tsx):**
```typescript
onMessage: (message, context) => {
  switch (message.type) {
    case 'SCORE_UPDATE':
      // handle it
      await context.redis.set(`score:${userId}`, String(message.payload.score));
      break;
    case 'GAME_OVER':
      // handle it
      break;
    default:
      // TypeScript exhaustive check — message satisfies never
      break;
  }
}
```

**Receiving in Webview (game.js):**
```javascript
window.addEventListener('message', (event) => {
  const msg = event.data;
  switch (msg.type) {
    case 'INIT_DATA':
      username = msg.payload.username;
      initGame(msg.payload.highScore);
      break;
  }
});
```

**CRITICAL RULES:**
- Every message type must be a named constant — never `postMessage({ type: 'whatever' })`
- Every sent type must have a matching `case` in the receiver
- Payload must be JSON-serializable (no functions, no DOM elements, no circular refs)
- ArrayBuffers must be base64-encoded (Devvit doesn't support transfer)

---

### Redis — The Only Persistence Layer

**No localStorage. No cookies. No IndexedDB in the blocks layer.**
All persistent game data goes through Redis via main.tsx.

**Naming convention** (always namespace):
```
gameName:userId:keyName
gameName:global:keyName
```

**Common patterns:**
```typescript
// Save a score
await context.redis.set(`wigglers:${userId}:highScore`, String(score));

// Read a score
const raw = await context.redis.get(`wigglers:${userId}:highScore`);
const score = raw ? parseInt(raw) : 0;

// Leaderboard (sorted set)
await context.redis.zAdd('wigglers:global:leaderboard', {
  score: playerScore,
  member: userId
});
const top10 = await context.redis.zRange('wigglers:global:leaderboard', 0, 9, {
  by: 'rank', reverse: true
});

// Store complex object (must stringify)
await context.redis.set(`wigglers:${userId}:state`, JSON.stringify(gameState));
const state = JSON.parse(await context.redis.get(`wigglers:${userId}:state`) ?? '{}');

// TTL (expires in seconds)
await context.redis.expire(`wigglers:${userId}:session`, 3600);

// Atomic increment
await context.redis.incrBy(`wigglers:global:totalPlays`, 1);
```

**Redis types available in Devvit:**
- `get/set` — strings
- `mGet/mSet` — multiple keys at once
- `del` — delete key(s)
- `expire` — set TTL
- `incrBy / decrBy` — atomic integer ops
- `hGet/hSet/hGetAll` — hash fields
- `zAdd/zRange/zScore/zRem` — sorted sets (leaderboards)
- `lPush/lPop/lRange` — lists

---

### Realtime — Live Multiplayer Messaging

For real-time events (scores broadcasting, multiplayer state):
```typescript
// Subscribe (in the webview-mounted component)
const channel = await context.realtime.subscribe('wigglers:game-events', (event) => {
  // forward to webview
  context.ui.webView.postMessage('myWebView', {
    type: 'REALTIME_EVENT',
    payload: event.data
  });
});

// Publish (from main.tsx when handling a webview message)
await context.realtime.send('wigglers:game-events', {
  userId: userId,
  score: newScore,
  event: 'score_update'
});
```

---

### Devvit Context Object — What's Available

```typescript
// context is passed into every handler
context.redis          // ← Redis client (see above)
context.realtime       // ← Realtime pub/sub
context.reddit         // ← Reddit API (get user, post, comment, vote)
context.ui.webView     // ← Send messages to webview
context.ui.showToast() // ← Show a toast notification
context.ui.navigateTo()// ← Open a URL
context.userId         // ← Current user's Reddit ID (t2_xxxxx)
context.postId         // ← Current post's ID (t3_xxxxx)
context.subredditId    // ← Current subreddit's ID
```

---

### Reddit API — What You Can Do from main.tsx

```typescript
// Get current user
const user = await context.reddit.getCurrentUser();
// user.username, user.id, user.createdAt

// Get the current post
const post = await context.reddit.getPostById(context.postId);

// Submit a comment
await context.reddit.submitComment({
  id: context.postId,
  text: `New high score: ${score}!`
});

// Get subreddit info
const subreddit = await context.reddit.getCurrentSubreddit();
```

---

### devvit.yaml — App Configuration

```yaml
name: my-game
version: 0.0.1
permissions:
  - redis        # required for any Redis use
  - realtime     # required for pub/sub
  - reddit_api   # required for Reddit API calls
```

**If a feature isn't working, check devvit.yaml first** — missing permissions are a common silent failure.

---

### main.tsx — Canonical Structure

```typescript
import { Devvit, useState } from '@devvit/public-api';

// 1. Configure permissions
Devvit.configure({ redis: true, realtime: true, redditAPI: true });

// 2. Define the custom post type
Devvit.addCustomPostType({
  name: 'My Game',
  height: 'tall',  // or 'regular'
  render: (context) => {
    // 3. State (triggers re-render)
    const [gameStarted, setGameStarted] = useState(false);

    // 4. WebView message handler
    const handleWebViewMessage = async (message: WebViewMessage) => {
      switch (message.type) {
        case 'READY':
          // Webview loaded — send init data
          const user = await context.reddit.getCurrentUser();
          const highScore = await context.redis.get(`game:${context.userId}:hs`);
          context.ui.webView.postMessage('myWebView', {
            type: 'INIT',
            payload: { username: user?.username, highScore: Number(highScore ?? 0) }
          });
          break;

        case 'SCORE_UPDATE':
          await context.redis.set(`game:${context.userId}:hs`, String(message.payload.score));
          break;
      }
    };

    // 5. Render: either the launch button or the webview
    if (!gameStarted) {
      return (
        <vstack height="100%" width="100%" alignment="center middle">
          <button onPress={() => setGameStarted(true)}>Play Game</button>
        </vstack>
      );
    }

    return (
      <vstack height="100%" width="100%">
        <webview
          id="myWebView"
          url="index.html"
          onMessage={handleWebViewMessage}
          grow
        />
      </vstack>
    );
  },
});

export default Devvit;
```

---

### Common Devvit Bug Patterns

| Symptom | Root cause | Fix |
|---|---|---|
| Message sent but nothing happens | Missing `case` in receiver switch | Add the case |
| Data not persisting | Using localStorage in blocks layer | Use Redis |
| Game works in web, broken in app | `window.localStorage` call in webview | Remove — use postMessage to blocks for persistence |
| Redis returning null unexpectedly | Key namespace typo | Log the exact key string |
| Realtime not firing | Missing `realtime: true` in devvit.yaml | Add permission |
| TypeScript error on build | Missing type on message payload | Add explicit type annotation |
| WebView blank / not loading | Wrong `url` in `<webview>` tag | Check file path in webroot/ |
| `context.reddit` undefined | Missing `redditAPI: true` in configure | Add to Devvit.configure() |
| Score resets on every load | Not loading from Redis on READY | Add Redis get in READY handler |
| ArrayBuffer postMessage fails | Devvit doesn't support transfer | Convert to base64 string first |

---

### File Layout — Wigglers Room (Your Project)

```
Wigglers_Room/
├── src/
│   └── main.tsx              ← Blocks layer (Reddit/Redis/Realtime)
├── webroot/
│   ├── index.html            ← Game HTML shell
│   └── game.js               ← Game logic (canvas, physics, render)
├── devvit.yaml               ← Permissions config
├── package.json              ← build: tsc --noEmit && devvit build
└── .github/workflows/
    └── deploy.yml            ← Build check on every push (~52s)
```

**What lives where:**
- Player input, canvas rendering, game physics → `game.js`
- User identity, save data, leaderboard → `main.tsx` via Redis
- Any fetch/HTTP call → `main.tsx` (webview fetch is blocked by Reddit's CSP)

---

## Code Style Rules — Match, Don't Impose

```bash
# Check var style
grep -m5 "^  var\|^  let\|^  const" game.js

# Check comment style
grep -m5 "// \|/\*" game.js

# Check function naming
grep -m10 "function " game.js
```

Mirror it exactly. Their style wins.

---

## What Contractors Do NOT Do

- ❌ Refactor code that works
- ❌ Rename variables for clarity
- ❌ Reorganize file structure
- ❌ Suggest architecture changes
- ❌ Fix bugs not in the ticket
- ❌ Cross the webview/blocks boundary without explicit need
- ❌ Add Redis keys with a different namespace than the project uses

---

## Version Bump Rule

Every output file gets a version bump. Find it:
```bash
grep -m1 "V[0-9]\|version\|VERSION" /mnt/user-data/uploads/game.html
```
Increment it. Add a one-line changelog comment.

---

## When to Escalate to Lead Dev

Flag this if:
- The ticket requires touching 5+ unrelated systems
- The bug is architectural (wrong side of the postMessage bridge)
- A new subsystem is needed, not just a new function

"This ticket has grown beyond a surgical fix — want me to put on the Lead Dev hat?"

---
