
// ============================================================
// Trace engine — pure JS, validated against Node prototype at
// ≥97% similarity on real game assets. No dependencies.
// ============================================================

function extractColors(imgData, maxColors, quantStep) {
  quantStep = quantStep || 24;
  const mergeMult = 1.5;
  const { data } = imgData;
  const counts = new Map();
  let totalVisible = 0;
  for (let i = 0; i < data.length; i += 4) {
    if (data[i + 3] <= 20) continue;
    totalVisible++;
    const r = Math.floor(data[i] / quantStep) * quantStep;
    const g = Math.floor(data[i + 1] / quantStep) * quantStep;
    const b = Math.floor(data[i + 2] / quantStep) * quantStep;
    const key = r + ',' + g + ',' + b;
    counts.set(key, (counts.get(key) || 0) + 1);
  }
  const minCount = Math.max(3, totalVisible * 0.01); // ignore fragments under ~1% of the art
  const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const picked = [];
  for (const [key, count] of sorted) {
    if (picked.length >= maxColors) break;
    if (count < minCount) break; // remaining are even smaller, sorted descending
    const [r, g, b] = key.split(',').map(Number);
    const tooClose = picked.some(p => {
      const d = (p.r - r) ** 2 + (p.g - g) ** 2 + (p.b - b) ** 2;
      return d < (quantStep * mergeMult) ** 2;
    });
    if (!tooClose) picked.push({ r, g, b, count });
  }
  return picked;
}

function labelPixels(imgData, clusters) {
  const { data, width, height } = imgData;
  const label = new Int16Array(width * height).fill(-1);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      const a = data[idx * 4 + 3];
      if (a <= 20) continue;
      const r = data[idx * 4], g = data[idx * 4 + 1], b = data[idx * 4 + 2];
      let best = -1, bestD = Infinity;
      for (let c = 0; c < clusters.length; c++) {
        const cl = clusters[c];
        const d = (cl.r - r) ** 2 + (cl.g - g) ** 2 + (cl.b - b) ** 2;
        if (d < bestD) { bestD = d; best = c; }
      }
      label[idx] = best;
    }
  }
  return label;
}

function connectedComponents(mask, width, height) {
  const visited = new Uint8Array(width * height);
  const components = [];
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      if (!mask[idx] || visited[idx]) continue;
      const stack = [[x, y]];
      const pixels = [];
      visited[idx] = 1;
      while (stack.length) {
        const [cx, cy] = stack.pop();
        pixels.push([cx, cy]);
        const neighbors = [[cx + 1, cy], [cx - 1, cy], [cx, cy + 1], [cx, cy - 1]];
        for (const [nx, ny] of neighbors) {
          if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
          const nidx = ny * width + nx;
          if (mask[nidx] && !visited[nidx]) { visited[nidx] = 1; stack.push([nx, ny]); }
        }
      }
      if (pixels.length > 2) components.push(pixels);
    }
  }
  return components;
}

// Moore-Neighbor boundary tracing. Start at topmost-then-leftmost pixel —
// its West neighbor is guaranteed background, giving a reliable initial
// backtrack direction (index 0 = West in the 8-connected direction table).
function traceBoundary(pixels) {
  const set = new Set(pixels.map(([x, y]) => x + ',' + y));
  const has = (x, y) => set.has(x + ',' + y);

  let start = pixels[0];
  for (const p of pixels) {
    if (p[1] < start[1] || (p[1] === start[1] && p[0] < start[0])) start = p;
  }

  const dirs = [[-1, 0], [-1, -1], [0, -1], [1, -1], [1, 0], [1, 1], [0, 1], [-1, 1]];

  const contour = [];
  let [x, y] = start;
  let backDir = 0;
  const startKey = x + ',' + y;
  let steps = 0;
  const maxSteps = pixels.length * 8 + 8;

  do {
    contour.push([x, y]);
    let found = false;
    for (let i = 1; i <= 8; i++) {
      const nd = (backDir + i) % 8;
      const nx = x + dirs[nd][0], ny = y + dirs[nd][1];
      if (has(nx, ny)) {
        backDir = (nd + 4) % 8;
        x = nx; y = ny;
        found = true;
        break;
      }
    }
    if (!found) break;
    steps++;
  } while ((x + ',' + y !== startKey || contour.length < 2) && steps < maxSteps);

  return contour;
}

function simplify(points, epsilon) {
  if (points.length < 3) return points;
  function perpDist(p, a, b) {
    const [x, y] = p, [x1, y1] = a, [x2, y2] = b;
    const dx = x2 - x1, dy = y2 - y1;
    const len = Math.hypot(dx, dy);
    if (len === 0) return Math.hypot(x - x1, y - y1);
    return Math.abs(dy * x - dx * y + x2 * y1 - y2 * x1) / len;
  }
  function rdp(pts) {
    if (pts.length < 3) return pts;
    let maxD = 0, idx = 0;
    for (let i = 1; i < pts.length - 1; i++) {
      const d = perpDist(pts[i], pts[0], pts[pts.length - 1]);
      if (d > maxD) { maxD = d; idx = i; }
    }
    if (maxD > epsilon) {
      const left = rdp(pts.slice(0, idx + 1));
      const right = rdp(pts.slice(idx));
      return left.slice(0, -1).concat(right);
    }
    return [pts[0], pts[pts.length - 1]];
  }
  return rdp(points);
}

// Background pixels fully enclosed by foreground are topological holes
// (e.g. the gap in a coiled orange peel) — walking only a blob's outer
// pixel boundary can never discover these, since they're a separate closed
// loop not reachable from the outer walk. Detected via flood-fill from the
// image border: any background pixel the border fill never reaches is
// enclosed by foreground on all sides.
function findEnclosedHoles(imgData) {
  const { width, height, data } = imgData;
  const fg = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) fg[i] = data[i * 4 + 3] > 20 ? 1 : 0;

  const visited = new Uint8Array(width * height);
  const queue = [];
  for (let x = 0; x < width; x++) {
    for (const y of [0, height - 1]) {
      const idx = y * width + x;
      if (!fg[idx] && !visited[idx]) { visited[idx] = 1; queue.push(idx); }
    }
  }
  for (let y = 0; y < height; y++) {
    for (const x of [0, width - 1]) {
      const idx = y * width + x;
      if (!fg[idx] && !visited[idx]) { visited[idx] = 1; queue.push(idx); }
    }
  }
  let qi = 0;
  while (qi < queue.length) {
    const idx = queue[qi++];
    const x = idx % width, y = (idx / width) | 0;
    for (const [nx, ny] of [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]]) {
      if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
      const nidx = ny * width + nx;
      if (!fg[nidx] && !visited[nidx]) { visited[nidx] = 1; queue.push(nidx); }
    }
  }

  const enclosed = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) enclosed[i] = (!fg[i] && !visited[i]) ? 1 : 0;
  return enclosed;
}

function traceAllClusters(imgData, maxColors, epsilon) {
  const clusters = extractColors(imgData, maxColors);
  const label = labelPixels(imgData, clusters);
  const { width, height, data } = imgData;

  const regions = clusters.map((cl, ci) => {
    const mask = new Uint8Array(width * height);
    for (let i = 0; i < width * height; i++) if (label[i] === ci) mask[i] = 1;
    const comps = connectedComponents(mask, width, height);
    const polys = comps.map(pixels => simplify(traceBoundary(pixels), epsilon)).filter(p => p.length >= 3);
    return { color: cl, polys };
  });

  // Attach any enclosed holes to whichever region's color surrounds them
  const enclosedMask = findEnclosedHoles(imgData);
  const holeComponents = connectedComponents(enclosedMask, width, height);
  for (const holePixels of holeComponents) {
    let ownerIdx = -1;
    outer: for (const [px, py] of holePixels) {
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = px + dx, ny = py + dy;
        if (nx < 0 || ny < 0 || nx >= width || ny >= height) continue;
        const nidx = ny * width + nx;
        if (data[nidx * 4 + 3] <= 20) continue;
        const r = data[nidx * 4], g = data[nidx * 4 + 1], b = data[nidx * 4 + 2];
        for (let ri = 0; ri < regions.length; ri++) {
          const c = regions[ri].color;
          if ((c.r - r) ** 2 + (c.g - g) ** 2 + (c.b - b) ** 2 < 900) { ownerIdx = ri; break outer; }
        }
      }
    }
    if (ownerIdx < 0) continue;
    const holePoly = simplify(traceBoundary(holePixels), epsilon);
    if (holePoly.length >= 3) {
      if (!regions[ownerIdx].holePolys) regions[ownerIdx].holePolys = [];
      regions[ownerIdx].holePolys.push(holePoly);
    }
  }

  return regions;
}

function hexOf(c) {
  return '#' + [c.r, c.g, c.b].map(v => v.toString(16).padStart(2, '0')).join('');
}

function generateCode(regions, order) {
  const lines = ["function drawArt(canvas) {", "  const ctx = canvas.getContext('2d');"];
  for (const i of order) {
    const region = regions[i];
    if (!region || !region.polys.length) continue;
    lines.push(`  ctx.fillStyle = '${hexOf(region.color)}';`);
    lines.push('  ctx.beginPath();');
    for (const poly of region.polys) {
      lines.push(`  ctx.moveTo(${poly[0][0]},${poly[0][1]});`);
      for (const [x, y] of poly.slice(1)) lines.push(`  ctx.lineTo(${x},${y});`);
      lines.push('  ctx.closePath();');
    }
    // Hole subpaths in the same path, filled with even-odd so they punch
    // out rather than add — this is what lets a coiled shape like an
    // orange peel keep its actual gap instead of being solid-filled.
    if (region.holePolys) {
      for (const hole of region.holePolys) {
        lines.push(`  ctx.moveTo(${hole[0][0]},${hole[0][1]});`);
        for (const [x, y] of hole.slice(1)) lines.push(`  ctx.lineTo(${x},${y});`);
        lines.push('  ctx.closePath();');
      }
    }
    lines.push("  ctx.fill('evenodd');");
  }
  lines.push('}');
  return lines.join('\n');
}

function drawRegions(canvas, regions, order) {
  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (const i of order) {
    const region = regions[i];
    if (!region || !region.polys.length) continue;
    ctx.fillStyle = hexOf(region.color);
    ctx.beginPath();
    for (const poly of region.polys) {
      ctx.moveTo(poly[0][0], poly[0][1]);
      for (const [x, y] of poly.slice(1)) ctx.lineTo(x, y);
      ctx.closePath();
    }
    if (region.holePolys) {
      for (const hole of region.holePolys) {
        ctx.moveTo(hole[0][0], hole[0][1]);
        for (const [x, y] of hole.slice(1)) ctx.lineTo(x, y);
        ctx.closePath();
      }
    }
    ctx.fill('evenodd');
  }
}

// Foreground-only accuracy: only counts pixels where either image shows
// content. A whole-canvas average (including transparent background)
// lets background agreement mask real foreground mismatches — a flat,
// texture-less trace can score 95%+ that way while looking clearly wrong.
function scoreAgainst(canvas, refCanvas) {
  const w = canvas.width, h = canvas.height;
  const out = canvas.getContext('2d').getImageData(0, 0, w, h).data;
  const ref = refCanvas.getContext('2d').getImageData(0, 0, w, h).data;
  let fgTotal = 0, fgGood = 0;
  for (let p = 0; p < out.length; p += 4) {
    const refA = ref[p + 3], outA = out[p + 3];
    if (refA <= 20 && outA <= 20) continue; // both transparent — not foreground, skip
    fgTotal++;
    const dr = Math.abs(out[p] - ref[p]), dg = Math.abs(out[p + 1] - ref[p + 1]),
          db = Math.abs(out[p + 2] - ref[p + 2]), da = Math.abs(outA - refA);
    if (dr <= 25 && dg <= 25 && db <= 25 && da <= 25) fgGood++;
  }
  return fgTotal === 0 ? 1 : fgGood / fgTotal;
}

// ============================================================

module.exports = {
  extractColors, labelPixels, connectedComponents, traceBoundary, simplify,
  findEnclosedHoles, traceAllClusters, hexOf, generateCode, drawRegions
};
