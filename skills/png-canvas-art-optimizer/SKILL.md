---
name: PNG Canvas Art Optimizer
description: Use this skill ONLY when the user uploads a PNG, JPG, JPEG, or GIF file and wants HTML5 canvas drawing code. Triggers on .png, .jpg, .jpeg, .gif files and phrases like "convert this image to canvas", "make canvas code from this PNG", "recreate this sprite in canvas". Do NOT use for SVG files — those go to the Canvas Art Optimizer skill instead. Best for flat illustrated art, pixel art, and icons with clear shapes. Will not work well for photorealistic images (photos, AI-generated art with complex textures). Uses Claude vision API to reverse-engineer shapes, iterates until ≥95% similarity, outputs HTML preview artifact + JS file.
---

# PNG/JPG Canvas Art Optimizer

You are running an **internal vision + optimization loop**. The user uploaded a PNG or JPG. Your job: produce canvas code that matches it at ≥95% pixel similarity. Run the full loop yourself. Output a rendered HTML preview artifact + JS file. Never ask the user anything.

---

## Key Difference from SVG Skill

SVG gives you XML structure — you know exactly what every shape is. PNG/JPG gives you only pixels. You must **reverse-engineer** the shapes using Claude's vision capabilities via the Anthropic API, then score with pixel diff.

---

## Phase 1 — Extract Reference Data

```python
from PIL import Image, ImageFilter, ImageStat
import numpy as np, base64, io

# Load the uploaded image
img = Image.open('/mnt/user-data/uploads/filename.png').convert('RGBA')
w, h = img.size
arr = np.array(img).astype(float)

# Save to /tmp for scoring
img.save('/tmp/ref.png')

# Extract palette (quantize to buckets of 16 for cleaner colors)
from collections import Counter
pixels = np.array(img).reshape(-1, 4)
visible = pixels[pixels[:,3] > 128]
quantized = (visible[:,:3] // 16 * 16)
palette = Counter(map(tuple, quantized.tolist())).most_common(12)
print("Palette:", [f'#{r:02x}{g:02x}{b:02x}({n})' for (r,g,b),n in palette])

# Detect if pixel art (low unique color count + sharp edges)
unique_colors = len(set(map(tuple, visible[:,:3].tolist())))
gray = img.convert('L')
edges = np.array(gray.filter(ImageFilter.FIND_EDGES))
edge_pct = (edges > 30).sum() / edges.size
is_pixel_art = unique_colors < 32 and edge_pct > 0.05
print(f"Type: {'pixel art' if is_pixel_art else 'illustrated'} | colors: {unique_colors} | edges: {edge_pct:.2%}")

# Content bounding box
alpha = arr[:,:,3]
rows = np.any(alpha > 0, axis=1)
cols = np.any(alpha > 0, axis=0)
if rows.any():
    rmin, rmax = np.where(rows)[0][[0,-1]]
    cmin, cmax = np.where(cols)[0][[0,-1]]
    print(f"Content: x={cmin}-{cmax}, y={rmin}-{rmax}")

# Base64 encode for vision API
buf = io.BytesIO()
img.save(buf, format='PNG')
img_b64 = base64.b64encode(buf.getvalue()).decode()
```

---

## Phase 2 — Vision Analysis (Build the Artifact)

The Claude vision API is called **inside an HTML artifact** using `fetch` — auth is handled automatically in the browser. Build the optimization artifact like this:

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

// ── Scoring: pixel diff between reference img and canvas ──
async function score(canvas, refImg) {
  const w = canvas.width, h = canvas.height;
  const offRef = new OffscreenCanvas(w, h);
  const ctxRef = offRef.getContext('2d');
  ctxRef.drawImage(refImg, 0, 0, w, h);
  const refData = ctxRef.getImageData(0, 0, w, h).data;
  const attData = canvas.getContext('2d').getImageData(0, 0, w, h).data;
  let totalDiff = 0, problemPixels = 0;
  const len = refData.length;
  for (let i = 0; i < len; i++) {
    const d = Math.abs(refData[i] - attData[i]);
    totalDiff += d;
    if (i % 4 === 0 && d > 25) problemPixels++;
  }
  const similarity = 1 - totalDiff / (255 * len);
  return { similarity, problemPixels, total: len / 4, pass: similarity >= 0.95 };
}

// ── Claude API: vision analysis ──
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

// ── Execute canvas code safely ──
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

// ── Main optimization loop ──
async function optimize() {
  const refImg = document.getElementById('ref');
  const canvas = document.getElementById('canvas');
  const BASE64 = 'BASE64_HERE'; // same base64 as the img src

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
    log(`Score: ${(result.similarity*100).toFixed(1)}% | problem px: ${result.problemPixels}/${result.total}`);
    scoreEl.textContent = `${(result.similarity*100).toFixed(1)}% match`;
    scoreEl.style.color = result.pass ? '#4caf50' : result.similarity > 0.85 ? '#ff9800' : '#f44336';

    if (result.similarity > bestScore) {
      bestScore = result.similarity;
      bestCode = code;
    }

    if (result.pass) {
      log('✓ PASSED — done!');
      scoreEl.textContent = `✓ ${(bestScore*100).toFixed(1)}% — Complete!`;
      document.getElementById('finalCode').textContent = bestCode;
      document.getElementById('output').style.display = 'block';
      break;
    }
  }

  if (bestScore < 0.95) {
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

**Key variables to substitute before saving:**
- `BASE64_HERE` → the actual base64 string of the reference image (both in `<img src>` and in the JS `const BASE64`)
- `W` / `H` → the image dimensions

---

## Phase 3 — Generate the Artifact

```python
# Read the image and build the artifact
import base64, io
from PIL import Image

img = Image.open('/mnt/user-data/uploads/filename.png').convert('RGBA')
w, h = img.size
buf = io.BytesIO()
img.save(buf, format='PNG')
b64 = base64.b64encode(buf.getvalue()).decode()

# Load the HTML template above
html = open('/path/to/template').read()
html = html.replace('BASE64_HERE', b64)
html = html.replace(' width="W"', f' width="{w}"')
html = html.replace(' height="H"', f' height="{h}"')

with open('/mnt/user-data/outputs/artname_optimizer.html', 'w') as f:
    f.write(html)
```

Then `present_files(['/mnt/user-data/outputs/artname_optimizer.html'])` — the user opens it and the loop runs live in their browser.

---

## Phase 4 — What the Artifact Does

The artifact runs the full loop in the user's browser:

1. Displays reference image + live canvas side by side
2. Calls Claude vision API (auth auto-handled) to analyze and generate canvas code
3. Executes the code on the canvas
4. Pixel-diffs via `OffscreenCanvas` + `getImageData`
5. Feeds score + previous code back into next Claude call
6. Stops when ≥95% or after 6 iterations
7. Shows the final canvas code in a copyable textarea

**The user watches it iterate in real time.** No friction — just open the artifact.

---

## Iteration Loop — How It Works

The artifact runs this loop automatically in the browser. Claude does not loop in bash — the whole loop runs client-side:

```
MAX_ITERATIONS = 6
PASS_THRESHOLD = 0.95 (95% pixel similarity)

iteration 1:
  → call Claude vision API with raw image
  → prompt: "analyze and write drawArt(canvas) to recreate this image"
  → execute code on canvas
  → pixel diff via OffscreenCanvas
  → if score ≥ 0.95: DONE

iteration 2–6 (if not done):
  → call Claude vision API again with SAME image
  → prompt includes: previous score + previous code
  → "your last attempt scored X%. Here is what you drew. Improve it."
  → execute → score → check threshold

after MAX_ITERATIONS:
  → present best result regardless of score
  → show final score in UI
  → user can copy the best canvas code from textarea
```

**Fallback when ≥95% is not reached:**
- After 6 iterations, the artifact shows the best result achieved with its score (e.g. "Best: 88.4% after 6 iterations")
- The final canvas code is still shown in the textarea — the user can copy and refine manually
- Claude adds a note: "The optimizer reached X% similarity. For photorealistic images or complex gradients, this is expected — canvas has fundamental limits. Copy the code and tweak manually, or I can try a different approach."
- **Do not re-run the optimizer loop** — if it didn't converge in 6 iterations it won't converge in 6 more

**When to skip the optimizer entirely:**
- Photorealistic photos → canvas cannot represent these accurately; tell the user upfront
- AI-generated art with complex textures → same limitation
- Images > 1024px → resize to max 512px before encoding to reduce API payload

---

## Phase 5 — Output

After the artifact is delivered:

1. **Present the optimizer artifact** — user opens it, watches it run, copies the final code
2. **One-line summary** — "Open the artifact — it will analyze your image and iterate until it matches. Copy the final canvas code from the textarea when done."

---

## Pixel Art Special Handling

If `is_pixel_art == True` (detected in Phase 1), add this instruction to the vision prompt:

> "This is pixel art. Use `ctx.imageSmoothingEnabled = false`. Draw each pixel as a filled rectangle at the correct grid scale. Identify the pixel grid size first (e.g., 16x16 logical pixels displayed at 256x256 = scale factor 16)."

---

## Environment Notes

- PIL / numpy / cairosvg available in bash for pre-processing
- Claude vision API called **inside the artifact** via fetch (auth auto-handled)  
- PNG/JPG uploads land at `/mnt/user-data/uploads/`
- Output artifacts go to `/mnt/user-data/outputs/`
- Base64 encode the image in bash, inject into the HTML template
- The artifact is self-contained — all logic runs client-side in the browser
