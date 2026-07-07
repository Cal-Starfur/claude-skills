---
name: PNG Canvas Art Optimizer
description: Use this skill ONLY when the user uploads a PNG, JPG, JPEG, or GIF file and wants HTML5 canvas drawing code. Triggers on .png, .jpg, .jpeg, .gif files and phrases like "convert this image to canvas", "make canvas code from this PNG", "recreate this sprite in canvas", "trace this into canvas code". Do NOT use for SVG files — those go to the Canvas Art Optimizer skill instead. Best for flat illustrated art, pixel art, and icons with clear shapes. Will not work well for photorealistic images (photos, AI-generated art with complex textures). Default method: a validated Node.js pipeline (color clustering, connected components, Moore-Neighbor contour tracing, topological hole detection, even-odd fill) ported directly from a real iterated web tool. Fallback method: Claude vision API iteration loop, for photos/complex gradients where the deterministic pipeline doesn't apply.
---

# PNG/JPG Canvas Art Optimizer

You are converting a PNG/JPG into HTML5 canvas drawing code that matches it as closely as a flat-vector-fill approach can.

**There are two methods. Try Method A first for anything flat/illustrated (icons, sprites, pixel art, flat-color game assets). Only fall back to Method B (vision-guessing loop) for photos or complex gradients where contour tracing genuinely doesn't apply.**

Method A is deterministic and runs entirely in Node — it traces the actual pixels, so results are reproducible and don't depend on a model re-guessing the shape each round. It's the exact engine from a real project ([png-canvas-tracer](https://github.com/Cal-Starfur/png-canvas-tracer)) that was iterated through many concrete, verified bug fixes — use it as-is rather than re-deriving the algorithm from scratch.

---

## Method A — Node Engine (default, use this first)

### Step 1 — Bootstrap the scripts

```python
python3 << 'FETCH'
import urllib.request, json, base64
from pathlib import Path
TOKEN = "your_pat_here"
headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json", "User-Agent": "GHSync/1.0"}
base = "https://api.github.com/repos/Cal-Starfur/claude-skills/contents/skills/user/png-canvas-art-optimizer/scripts"
for fname in ["trace_engine.js", "trace_cli.js"]:
    req = urllib.request.Request(f"{base}/{fname}", headers=headers)
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    Path(f"/tmp/png-trace/{fname}").parent.mkdir(parents=True, exist_ok=True)
    Path(f"/tmp/png-trace/{fname}").write_text(base64.b64decode(data["content"]).decode("utf-8"))
    print(f"✓ {fname}")
FETCH
```

### Step 2 — Ensure pngjs is available

```bash
cd /tmp/png-trace && npm install pngjs --silent
```

### Step 3 — Run the trace

```bash
node /tmp/png-trace/trace_cli.js /path/to/input.png /tmp/png-trace/output.js --preview /tmp/png-trace/preview.png
```

Prints a JSON summary: dimensions, clusters found, holes detected, and — critically — a **foreground-only accuracy score**. This score only counts pixels where either image actually has content; a whole-canvas average would let background agreement mask a genuinely bad trace (this was a real bug found and fixed in the source project — don't reintroduce a naive scoring method).

Default flags: `--colors 6 --epsilon 0.4`. These are validated defaults, not arbitrary:
- `--epsilon 0.4`: the original default of 0.8 was over-simplifying contours and measurably cutting accuracy (~79% → ~80%+ on simple assets just from this one change). Lower (down to ~0.1–0.3) traces with more fidelity at the cost of more points; there's a fidelity plateau around 0.1–0.3 where further reduction stops mattering.
- `--colors 6`: raising this alone often recovers **nothing** — the real bottleneck for interior detail is the color-merge distance inside `extractColors`, not the count cap. If the preview looks flatter/more blob-like than the source (real shading merged into 1-2 colors), that's the merge threshold being too coarse for that specific asset, not something the `--colors` flag can fix by itself.

### Step 4 — Inspect the preview, iterate if needed

View `/tmp/png-trace/preview.png` next to the original. Check specifically for:
- **A detail color painted over by a larger one** — the default draw order (largest pixel-count first) isn't always correct z-order; if a small detail disappeared, that region needs to draw later. `generateCode`'s `order` argument controls this — it's just an array of cluster indices, reorder it and regenerate.
- **A flat blob where the source has real shading** — texture/gradient loss is a genuine limitation of flat-fill tracing, not always fixable by parameter tuning. Textured assets (many close-but-distinct shading tones) have a real, lower ceiling than simple flat-silhouette assets — don't chase 90%+ on something like a shaded floret pattern.
- **A hole that got filled solid** — should already be handled (the engine detects background pixels topologically enclosed by foreground and fills with the even-odd rule), but confirm in the preview if the source has any coiled/ring-shaped silhouette.

Don't blindly re-run with different flags hoping for improvement — check *what specifically* is wrong in the preview first, then pick the lever that actually addresses it (epsilon for contour fidelity, manual reorder for z-order, accept the ceiling for genuine texture loss).

### Step 5 — Deliver

Present the generated `.js` file (containing `function drawArt(canvas) {...}`) to the user. Mention the foreground accuracy score honestly — don't round up or imply near-100% is typical; most real assets land in the 70-90% range, textured ones lower.

---

## Method B — Vision API Iteration Loop (fallback only)

Use only when Method A doesn't apply: photorealistic photos, AI-generated art with complex textures/gradients, or anything where flat color-region contouring genuinely doesn't describe the image (soft shading, photographic gradients, noise).

The Claude vision API is called **inside an HTML artifact** using `fetch` — auth is handled automatically in the browser.

```html
<!DOCTYPE html>
<html>
<head><style>
body { margin: 0; background: #111; color: #eee; font-family: monospace; padding: 20px; }
.row { display: flex; gap: 20px; align-items: flex-start; }
canvas { border: 1px solid #333; }
#log { font-size: 11px; line-height: 1.6; max-width: 400px; white-space: pre-wrap; }
#score { font-size: 24px; font-weight: bold; color: #4caf50; margin: 10px 0; }
</style></head>
<body>
<h3>Canvas Art Optimizer — PNG Mode</h3>
<div id="score">Analyzing...</div>
<div class="row">
  <div><p>Reference</p><img id="ref" src="data:image/png;base64,BASE64_HERE" style="max-width:256px"></div>
  <div><p>Canvas Attempt</p><canvas id="canvas" width="W" height="H"></canvas></div>
</div>
<div id="log"></div>

<script>
const log = t => { document.getElementById('log').textContent += t + '\n'; };
const scoreEl = document.getElementById('score');

async function score(canvas, refImg) {
  const w = canvas.width, h = canvas.height;
  const offRef = new OffscreenCanvas(w, h);
  const ctxRef = offRef.getContext('2d');
  ctxRef.drawImage(refImg, 0, 0, w, h);
  const refData = ctxRef.getImageData(0, 0, w, h).data;
  const attData = canvas.getContext('2d').getImageData(0, 0, w, h).data;
  let fgTotal = 0, fgGood = 0;
  for (let p = 0; p < refData.length; p += 4) {
    const refA = refData[p+3], attA = attData[p+3];
    if (refA <= 20 && attA <= 20) continue; // foreground-only, same lesson as Method A
    fgTotal++;
    const dr = Math.abs(attData[p]-refData[p]), dg = Math.abs(attData[p+1]-refData[p+1]),
          db = Math.abs(attData[p+2]-refData[p+2]), da = Math.abs(attA-refA);
    if (dr<=25 && dg<=25 && db<=25 && da<=25) fgGood++;
  }
  const similarity = fgTotal === 0 ? 1 : fgGood/fgTotal;
  return { similarity, pass: similarity >= 0.80 };
}

async function analyzeWithVision(base64img, previousAttempt, previousScore) {
  const prompt = previousAttempt
    ? `Here is the reference image and my previous canvas attempt score was ${(previousScore*100).toFixed(1)}%.
My previous canvas code was:
\`\`\`javascript
${previousAttempt}
\`\`\`
The pixel diff shows errors. Analyze the reference image carefully and provide improved canvas drawing code.`
    : `Analyze this image for HTML5 canvas reconstruction. Describe every shape, color, and layer needed to recreate it as canvas drawing code.`;

  const resp = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'anthropic-version': '2023-06-01' },
    body: JSON.stringify({
      model: 'claude-sonnet-4-6',
      max_tokens: 4000,
      messages: [{
        role: 'user',
        content: [
          { type: 'image', source: { type: 'base64', media_type: 'image/png', data: base64img } },
          { type: 'text', text: prompt + '\n\nRespond with ONLY a JavaScript function called drawArt(canvas) that recreates this image. No explanation, just the function.' }
        ]
      }]
    })
  });
  const data = await resp.json();
  return data.content[0].text;
}

function executeCanvasCode(code, canvas) {
  try {
    const clean = code.replace(/```javascript|```js|```/g, '').trim();
    const fn = new Function('canvas', `
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ${clean.includes('function drawArt') ? clean + '\ndrawArt(canvas);' : clean}
    `);
    fn(canvas);
    return true;
  } catch(e) {
    log('Execution error: ' + e.message);
    return false;
  }
}

async function optimize() {
  const refImg = document.getElementById('ref');
  const canvas = document.getElementById('canvas');
  const BASE64 = 'BASE64_HERE';

  await new Promise(r => refImg.complete ? r() : refImg.onload = r);

  let bestCode = null, bestScore = 0, attempt = 0;
  const MAX = 6;

  while (attempt < MAX) {
    attempt++;
    log(`\n── Iteration ${attempt}/${MAX} ──`);
    scoreEl.textContent = `Iteration ${attempt}/${MAX}...`;

    const code = await analyzeWithVision(BASE64, bestCode, bestScore);
    log('Got canvas code (' + code.length + ' chars)');

    const ok = executeCanvasCode(code, canvas);
    if (!ok) { log('Skipping — code error'); continue; }

    const result = await score(canvas, refImg);
    log(`Score: ${(result.similarity*100).toFixed(1)}%`);
    scoreEl.textContent = `${(result.similarity*100).toFixed(1)}% match`;
    scoreEl.style.color = result.similarity >= 0.80 ? '#4caf50' : result.similarity > 0.6 ? '#ff9800' : '#f44336';

    if (result.similarity > bestScore) { bestScore = result.similarity; bestCode = code; }

    if (result.pass) {
      log('✓ PASSED — done!');
      scoreEl.textContent = `✓ ${(bestScore*100).toFixed(1)}% — Complete!`;
      document.getElementById('finalCode').textContent = bestCode;
      document.getElementById('output').style.display = 'block';
      break;
    }
  }

  if (bestScore < 0.80) {
    log(`Best achieved: ${(bestScore*100).toFixed(1)}% after ${MAX} iterations`);
    scoreEl.textContent = `Best: ${(bestScore*100).toFixed(1)}% (${MAX} iterations)`;
    document.getElementById('finalCode').textContent = bestCode;
    document.getElementById('output').style.display = 'block';
  }
}

optimize();
</script>

<div id="output" style="display:none; margin-top:20px;">
  <h4>Final Canvas Code:</h4>
  <textarea id="finalCode" style="width:100%;height:300px;background:#1a1a1a;color:#eee;font-family:monospace;font-size:11px;border:1px solid #333;padding:10px;"></textarea>
</div>
</body>
</html>
```

**Key variables to substitute before saving:** `BASE64_HERE` → the base64 of the reference image (both spots), `W`/`H` → image dimensions.

**Known limitation:** this method plateaus on organic/irregular silhouettes because each iteration re-guesses the shape from a text description rather than the actual pixel boundary — that's exactly why Method A exists and should always be tried first for anything flat-illustrated. If a Method B run is stuck and the source is flat-colored, stop iterating and switch to Method A; more rounds will not fix it.

---

## Choosing Between Methods — Quick Reference

| Image type | Method |
|---|---|
| Flat illustrated icon (game sprite, item, UI element) | A |
| Pixel art | A (add a note to the vision prompt if ever falling back to B: `ctx.imageSmoothingEnabled = false`, grid-scale aware) |
| Simple flat-color character/creature | A |
| Ring/coiled/donut-shaped silhouette (topological holes) | A — handled correctly via even-odd fill |
| Photo | B |
| AI-generated art with painterly/photographic texture | B |
| Complex gradients, soft shadows, lighting effects | B |

---

## Environment Notes

- Node + `pngjs` (pure JS, no native deps) does the PNG decode — no OpenCV, no PIL, no Python needed for Method A at all.
- `trace_engine.js` and `trace_cli.js` live in this skill's `scripts/` folder in the repo and are fetched at session start via the bootstrap block above.
- PNG/JPG uploads land at `/mnt/user-data/uploads/`; work in `/tmp/png-trace/`; final deliverable goes to `/mnt/user-data/outputs/`.
- Method B (browser artifact) still needs the Anthropic vision API and only applies to photos/complex textures — don't reach for it on flat art just because Method A's score isn't 95%+; that's usually a real ceiling (texture loss), not a reason to switch methods.
