[Fresh from GitHub: c5d2a5d]

---
name: Canvas Art Optimizer
description: Use this skill ONLY when the user uploads an SVG file and wants HTML5 canvas drawing code. Triggers on .svg files and phrases like "convert this SVG to canvas", "port this SVG to canvas", "make canvas code from this SVG". Do NOT use for PNG, JPG, JPEG, or GIF files — those go to the PNG Canvas Art Optimizer skill instead. This skill parses SVG XML directly, translates every element to canvas calls with exact coordinates and colors, scores via pixel diff, and iterates until ≥95% similarity. Zero friction: user uploads SVG, you iterate silently in bash, user gets finished JS code + HTML preview.
---

# Canvas Art Optimizer — SVG ONLY

**This skill handles SVG files exclusively.**
If the user uploads a PNG, JPG, JPEG, or GIF → stop and use the PNG Canvas Art Optimizer skill instead.

You are running an **internal optimization loop**. Parse the SVG as XML, translate every element to canvas calls, score via pixel diff, iterate until ≥95% similarity. Output a JS file + HTML preview. Never ask the user anything.

---

## Phase 1 — Analyze the SVG

Parse it as XML to extract every element before writing a single line of canvas code.

```python
import xml.etree.ElementTree as ET, json, cairosvg, io
from PIL import Image, ImageStat
import numpy as np

svg_text = open('/mnt/user-data/uploads/filename.svg').read()
tree = ET.fromstring(svg_text)

def extract(el, depth=0):
    tag = el.tag.split('}')[-1]
    return {'tag': tag, 'attribs': dict(el.attrib), 'children': [extract(c) for c in el]}

structure = extract(tree)

# Render to PNG for pixel diff scoring
png_bytes = cairosvg.svg2png(bytestring=svg_text.encode())
ref_img = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
ref_arr = np.array(ref_img).astype(float)
ref_img.save('/tmp/ref.png')
```

**What to extract:**
- `viewBox` / `width` / `height` → canvas dimensions
- `<g>` groups → `ctx.save()` / `ctx.restore()` + `ctx.transform()`
- `transform="translate/rotate/scale"` → explicit ctx calls
- `fill`, `stroke`, `stroke-width`, `opacity`, `fill-opacity` → ctx properties
- `<path d="...">` → translate every M/L/C/Q/A/Z command
- `<circle cx cy r>` → `ctx.arc(cx, cy, r, 0, Math.PI*2)`
- `<rect x y width height rx ry>` → `ctx.roundRect` or manual path
- `<ellipse cx cy rx ry>` → `ctx.ellipse(...)`
- `<polygon points>` → `ctx.moveTo` + `ctx.lineTo` loop
- `<linearGradient>` / `<radialGradient>` → `ctx.createLinearGradient` etc
- `<clipPath>` → `ctx.clip()`

---

## Phase 2 — Write Initial Canvas Code

```javascript
function drawArt(canvas) {
  const ctx = canvas.getContext('2d');
  canvas.width = W;
  canvas.height = H;
  // Draw in exact SVG paint order (back to front)
}
```

**SVG → Canvas translation rules:**

| SVG | Canvas |
|-----|--------|
| `opacity` on element | `ctx.globalAlpha = value` wrapped in save/restore |
| `fill="none"` | skip `ctx.fill()` |
| `stroke` present | add `ctx.strokeStyle` + `ctx.lineWidth` + `ctx.stroke()` |
| `transform="rotate(deg cx cy)"` | `ctx.translate(cx,cy); ctx.rotate(deg*Math.PI/180); ctx.translate(-cx,-cy)` |
| `transform="matrix(a b c d e f)"` | `ctx.transform(a,b,c,d,e,f)` |
| SVG path `A` (arc) command | Use svgArcToCanvas() below |
| `fill-rule="evenodd"` | `ctx.fill('evenodd')` |

**SVG path `A` → Canvas:**
```javascript
function svgArcToCanvas(ctx, x1, y1, rx, ry, xRot, largeArc, sweep, x2, y2) {
  const phi = xRot * Math.PI / 180;
  const dx = (x1 - x2) / 2, dy = (y1 - y2) / 2;
  const x1p = Math.cos(phi)*dx + Math.sin(phi)*dy;
  const y1p = -Math.sin(phi)*dx + Math.cos(phi)*dy;
  const r2 = (rx*rx*ry*ry - rx*rx*y1p*y1p - ry*ry*x1p*x1p) / (rx*rx*y1p*y1p + ry*ry*x1p*x1p);
  const r = Math.sqrt(Math.max(0, r2));
  const sign = (largeArc === sweep) ? -1 : 1;
  const cxp = sign * r * rx * y1p / ry;
  const cyp = -sign * r * ry * x1p / rx;
  const cx = Math.cos(phi)*cxp - Math.sin(phi)*cyp + (x1+x2)/2;
  const cy = Math.sin(phi)*cxp + Math.cos(phi)*cyp + (y1+y2)/2;
  const startAngle = Math.atan2((y1p-cyp)/ry, (x1p-cxp)/rx);
  const endAngle = Math.atan2((-y1p-cyp)/ry, (-x1p-cxp)/rx);
  ctx.ellipse(cx, cy, rx, ry, phi, startAngle, endAngle, sweep === 0);
}
```

---

## Phase 3 — Score the Attempt

Reconstruct an SVG equivalent of what your canvas code draws, render it, pixel-diff against reference:

```python
import cairosvg, io
import numpy as np
from PIL import Image

def score_attempt(ref_arr, attempt_svg):
    png_bytes = cairosvg.svg2png(bytestring=attempt_svg.encode())
    att_img = Image.open(io.BytesIO(png_bytes)).convert('RGBA')
    ref_img = Image.fromarray(ref_arr.astype(np.uint8))
    if att_img.size != ref_img.size:
        att_img = att_img.resize(ref_img.size, Image.LANCZOS)
    att_arr = np.array(att_img).astype(float)
    diff = np.abs(ref_arr - att_arr)
    similarity = 1.0 - (diff.sum() / (255 * 4 * ref_arr.shape[0] * ref_arr.shape[1]))
    diff_gray = diff.mean(axis=2)
    problem_pct = (diff_gray > 25).sum() / diff_gray.size
    h, w = diff_gray.shape
    quadrants = {
        'TL': diff_gray[:h//2,:w//2].mean(), 'TR': diff_gray[:h//2,w//2:].mean(),
        'BL': diff_gray[h//2:,:w//2].mean(), 'BR': diff_gray[h//2:,w//2:].mean(),
    }
    channel_diff = diff.mean(axis=(0,1))
    return {
        'similarity': similarity, 'problem_pct': problem_pct,
        'worst_quadrant': max(quadrants, key=quadrants.get),
        'channel_errors': {'R': channel_diff[0], 'G': channel_diff[1], 'B': channel_diff[2], 'A': channel_diff[3]},
        'pass': similarity >= 0.95
    }
```

---

## Phase 4 — Iterate Until Pass

```
MAX_ITERATIONS = 6  |  PASS_THRESHOLD = 0.95

for each iteration:
    score = score_attempt(ref_arr, svg_equivalent_of_canvas_code)
    if score['pass']: break
    diagnose(score) → fix specific problem → rewrite
```

| Score says | Fix |
|---|---|
| `worst_quadrant: TL` | Wrong position/size in that region |
| `channel_errors.R` high | Wrong red values — recheck hex colors |
| `channel_errors.A` high | Opacity mismatch — check globalAlpha |
| `similarity` < 0.85 | Major structural error — missing shapes or wrong order |
| `similarity` 0.85-0.94 | Fine tuning — coordinates slightly off |
| `problem_pct` > 0.20 | Whole region wrong — likely broken transform stack |

**Fallback when ≥95% is not reached after 6 iterations:**

Present the best result anyway — do not loop indefinitely:

```python
if best_score < 0.95:
    print(f"Best achieved: {best_score*100:.1f}% after {MAX_ITERATIONS} iterations")
    print("Delivering best result — user can refine manually")
    # still output the HTML preview and JS file using best_code
```

Tell the user:
> "The optimizer reached **X%** similarity after 6 iterations. For this SVG, canvas has some fundamental limits (complex gradients, blurred filters, or very fine path detail). Here's the best result — copy the JS file and tweak the specific areas manually."

**Escalation path if score is stuck (< 5% improvement across 3 consecutive iterations):**
- Stop early — further iterations won't help
- Identify the specific failing quadrant from `worst_quadrant`
- Manually inspect that region's SVG elements and rewrite just those paths
- Re-run scoring on the patched version

---

## Phase 5 — Output

Always deliver TWO things:

**1. HTML preview** — save to `/mnt/user-data/outputs/[name]_preview.html`, call `present_files`
```html
<!DOCTYPE html>
<html>
<body style="margin:0;background:#1a1a1a;display:flex;align-items:center;justify-content:center;min-height:100vh;">
  <canvas id="c"></canvas>
  <script>
    const canvas = document.getElementById('c');
    [paste full drawing function here]
    drawArt(canvas);
  </script>
</body>
</html>
```

**2. JS file** — save to `/mnt/user-data/outputs/[name]_canvas.js`, call `present_files`
```javascript
// Art: [filename] | Similarity: 97.3% | Canvas: 512×512
function draw[Name](canvas) {
  const ctx = canvas.getContext('2d');
  canvas.width = W;
  canvas.height = H;
  // [clean drawing code]
}
```

---

## SVG → Canvas Cheat Sheet

```
fill="#rrggbb"          → ctx.fillStyle = '#rrggbb'
fill="none"             → (omit ctx.fill())
stroke="#color"         → ctx.strokeStyle = '#color'
stroke-width="N"        → ctx.lineWidth = N
stroke-linecap="round"  → ctx.lineCap = 'round'
stroke-linejoin="round" → ctx.lineJoin = 'round'
opacity="0.5"           → ctx.globalAlpha = 0.5 (save/restore around element)
fill-opacity="0.5"      → use rgba() color string instead
stroke-dasharray="5,3"  → ctx.setLineDash([5, 3])

M x y    → ctx.moveTo(x, y)
L x y    → ctx.lineTo(x, y)
H x      → ctx.lineTo(x, currentY)
V y      → ctx.lineTo(currentX, y)
C x1 y1 x2 y2 x y → ctx.bezierCurveTo(x1,y1,x2,y2,x,y)
Q x1 y1 x y       → ctx.quadraticCurveTo(x1,y1,x,y)
A ...    → svgArcToCanvas() (see Phase 2)
Z        → ctx.closePath()
Relative commands (lowercase) → add current point to all coords first
```

---

## Environment Notes

- `cairosvg` available: `import cairosvg`
- `PIL` / `numpy` available
- No headless browser — score via SVG reconstruction in bash
- Files land at `/mnt/user-data/uploads/`
- **PNG/JPG/GIF inputs → use PNG Canvas Art Optimizer instead**

---

## Error Handling & Edge Cases

### Corrupted or Unreadable SVG

If the uploaded SVG fails to parse or produces no output from the script:

1. Check the error — most common causes:
   - File is not valid XML (truncated upload, encoding issue, editor artefact)
   - SVG uses unsupported features the parser can't handle (e.g. embedded `<foreignObject>`, CSS animations, `<use>` references to external files)
   - File is actually a different format renamed as .svg (e.g. a PNG or PDF)

2. For XML parse errors — try reading the raw file to see if it's salvageable:
   ```bash
   head -50 /mnt/user-data/uploads/image.svg
   ```
   If the XML is clearly broken, tell the user: "The SVG file appears to be corrupted or truncated — can you re-export it from your design tool?"

3. For unsupported SVG features — fall back to visual inspection via the image tool (Claude can view SVGs as images) and hand-write the canvas translation. Note in the output: "Auto-parse skipped — drew manually from visual reference."

4. Never attempt to fix a corrupted SVG programmatically — ask the user for a clean export.

---

### Large SVG Files (>2MB)

SVGs over 2MB are usually one of: an SVG with embedded base64 images, an extremely complex path file (e.g. exported from Illustrator with thousands of nodes), or an accidentally included asset.

1. Check what's making it large:
   ```bash
   wc -c /mnt/user-data/uploads/image.svg
   grep -c "<path" /mnt/user-data/uploads/image.svg
   grep -c "base64" /mnt/user-data/uploads/image.svg
   ```

2. **Embedded base64 images** — the SVG is wrapping a raster image. Extract the base64 content and decode it to a PNG, then switch to the `png-canvas-art-optimizer` skill instead.

3. **Too many path nodes** (>5,000 `<path>` elements) — the pixel diff iteration will be slow and the canvas output will be impractical. Tell the user: "This SVG has [N] path elements — canvas translation at this complexity isn't practical. Consider simplifying the SVG in your design tool first (merge paths, reduce nodes)."

4. **File simply too large for the API** — resize or simplify before processing. Don't attempt to process a >5MB SVG.
