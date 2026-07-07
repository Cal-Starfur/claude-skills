#!/usr/bin/env node
// Usage: node trace_cli.js input.png output.js [--colors N] [--epsilon E] [--preview preview.png]
//
// Ports the exact validated engine from png-canvas-tracer (github.com/Cal-Starfur/png-canvas-tracer)
// into a CLI usable from Claude's bash sandbox, so a PNG can be traced without opening the web app.

const fs = require('fs');
const path = require('path');
const { PNG } = require('pngjs');
const engine = require('./trace_engine.js');

function parseArgs(argv) {
  const args = { colors: 6, epsilon: 0.4, preview: null, positional: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--colors') args.colors = parseInt(argv[++i], 10);
    else if (a === '--epsilon') args.epsilon = parseFloat(argv[++i]);
    else if (a === '--preview') args.preview = argv[++i];
    else args.positional.push(a);
  }
  args.input = args.positional[0];
  args.output = args.positional[1];
  return args;
}

// Scanline fill supporting outer + hole subpaths together (even-odd rule),
// mirroring exactly what ctx.fill('evenodd') does in the browser.
function fillWithHoles(buf, width, height, outerPolys, holePolys, rgb) {
  const allPolys = [...outerPolys, ...(holePolys || [])];
  for (let y = 0; y < height; y++) {
    const xs = [];
    for (const poly of allPolys) {
      for (let i = 0; i < poly.length; i++) {
        const [x1, y1] = poly[i]; const [x2, y2] = poly[(i + 1) % poly.length];
        if ((y1 <= y && y2 > y) || (y2 <= y && y1 > y)) {
          const t = (y - y1) / (y2 - y1);
          xs.push(x1 + t * (x2 - x1));
        }
      }
    }
    xs.sort((a, b) => a - b);
    for (let i = 0; i < xs.length; i += 2) {
      const xStart = Math.round(xs[i]), xEnd = Math.round(xs[i + 1] ?? xs[i]);
      for (let x = xStart; x <= xEnd; x++) {
        if (x < 0 || x >= width) continue;
        const idx = (y * width + x) * 4;
        buf[idx] = rgb.r; buf[idx + 1] = rgb.g; buf[idx + 2] = rgb.b; buf[idx + 3] = 255;
      }
    }
  }
}

// Foreground-only accuracy — only counts pixels where either image actually
// has content. A whole-canvas average lets background agreement mask a
// genuinely bad trace (this was a real bug found and fixed mid-project).
function fgAccuracy(out, ref) {
  let fgTotal = 0, fgGood = 0;
  for (let p = 0; p < out.length; p += 4) {
    const refA = ref[p + 3], outA = out[p + 3];
    if (refA <= 20 && outA <= 20) continue;
    fgTotal++;
    const dr = Math.abs(out[p] - ref[p]), dg = Math.abs(out[p + 1] - ref[p + 1]),
          db = Math.abs(out[p + 2] - ref[p + 2]), da = Math.abs(outA - refA);
    if (dr <= 25 && dg <= 25 && db <= 25 && da <= 25) fgGood++;
  }
  return fgTotal === 0 ? 100 : 100 * fgGood / fgTotal;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input) {
    console.error('Usage: node trace_cli.js input.png output.js [--colors N] [--epsilon E] [--preview preview.png]');
    process.exit(1);
  }

  const png = PNG.sync.read(fs.readFileSync(args.input));
  const imgData = { data: png.data, width: png.width, height: png.height };

  const regions = engine.traceAllClusters(imgData, args.colors, args.epsilon);
  // Default draw order = cluster order (already sorted largest-first by
  // extractColors), which is a reasonable default but not always correct
  // for overlapping detail colors — flag this in the summary so Claude
  // can manually reorder if the preview shows a detail color hidden.
  const order = regions.map((_, i) => i);

  const out = Buffer.alloc(png.width * png.height * 4);
  for (const i of order) fillWithHoles(out, png.width, png.height, regions[i].polys, regions[i].holePolys, regions[i].color);

  const score = fgAccuracy(out, png.data);
  const code = engine.generateCode(regions, order);

  if (args.output) fs.writeFileSync(args.output, code);

  if (args.preview) {
    const outPng = new PNG({ width: png.width, height: png.height });
    out.copy(outPng.data);
    fs.writeFileSync(args.preview, PNG.sync.write(outPng));
  }

  const totalHoles = regions.reduce((s, r) => s + (r.holePolys ? r.holePolys.length : 0), 0);
  const summary = {
    input: args.input,
    width: png.width,
    height: png.height,
    colors: args.colors,
    epsilon: args.epsilon,
    clustersFound: regions.length,
    holesDetected: totalHoles,
    foregroundAccuracy: Math.round(score * 10) / 10,
    clusters: regions.map(r => ({
      color: engine.hexOf(r.color),
      pixelCount: r.color.count,
      shapeCount: r.polys.length,
      holeCount: r.holePolys ? r.holePolys.length : 0
    })),
    outputWritten: args.output || null,
    previewWritten: args.preview || null
  };
  console.log(JSON.stringify(summary, null, 2));
}

main();
