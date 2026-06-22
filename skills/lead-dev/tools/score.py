"""
tools/score.py — Shared Pixel Diff Scorer
Used by canvas art optimizer skills and any visual comparison task.

Import:
    import sys; sys.path.insert(0, '/mnt/skills/user/lead-dev')
    from tools.score import pixel_diff, score_svgs, load_image
"""

import io
import numpy as np
from PIL import Image

# ── Image Loading ─────────────────────────────────────────────────────────

def load_image(source):
    """
    Load image from filepath, bytes, or PIL Image.
    Always returns RGBA PIL Image.
    """
    if isinstance(source, Image.Image):
        return source.convert('RGBA')
    elif isinstance(source, (bytes, bytearray)):
        return Image.open(io.BytesIO(source)).convert('RGBA')
    elif isinstance(source, str):
        return Image.open(source).convert('RGBA')
    else:
        raise ValueError(f"Unsupported source type: {type(source)}")

def resize_to_match(img1, img2):
    """Resize img2 to match img1's dimensions if needed."""
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.LANCZOS)
    return img1, img2

# ── Core Pixel Diff ───────────────────────────────────────────────────────

def pixel_diff(reference, attempt, threshold=25):
    """
    Compare two images pixel by pixel.
    
    Args:
        reference: filepath, bytes, or PIL Image — the ground truth
        attempt:   filepath, bytes, or PIL Image — what we produced
        threshold: pixel difference (0-255) to count as a "problem pixel"
    
    Returns dict:
        similarity:     0.0 to 1.0 (1.0 = perfect match)
        problem_pct:    fraction of pixels above threshold
        worst_quadrant: 'TL' | 'TR' | 'BL' | 'BR'
        channel_errors: {'R': n, 'G': n, 'B': n, 'A': n}
        passed:         bool (similarity >= 0.95)
        diff_arr:       numpy array of per-pixel differences (for heatmap)
    """
    ref_img = load_image(reference)
    att_img = load_image(attempt)
    ref_img, att_img = resize_to_match(ref_img, att_img)

    ref_arr = np.array(ref_img).astype(float)
    att_arr = np.array(att_img).astype(float)

    diff = np.abs(ref_arr - att_arr)
    total_possible = 255.0 * 4 * ref_arr.shape[0] * ref_arr.shape[1]
    similarity = 1.0 - (diff.sum() / total_possible)

    diff_gray = diff.mean(axis=2)
    problem_mask = diff_gray > threshold
    problem_pct = problem_mask.sum() / diff_gray.size

    # Quadrant breakdown — find worst area
    h, w = diff_gray.shape
    quadrants = {
        'TL': diff_gray[:h//2, :w//2].mean(),
        'TR': diff_gray[:h//2, w//2:].mean(),
        'BL': diff_gray[h//2:, :w//2].mean(),
        'BR': diff_gray[h//2:, w//2:].mean(),
    }
    worst_quad = max(quadrants, key=quadrants.get)

    # Per-channel errors
    channel_errors = {
        'R': float(diff[:,:,0].mean()),
        'G': float(diff[:,:,1].mean()),
        'B': float(diff[:,:,2].mean()),
        'A': float(diff[:,:,3].mean()),
    }

    return {
        'similarity': float(similarity),
        'problem_pct': float(problem_pct),
        'worst_quadrant': worst_quad,
        'quadrant_scores': {k: float(v) for k, v in quadrants.items()},
        'channel_errors': channel_errors,
        'passed': similarity >= 0.95,
        'diff_arr': diff_gray,
        'ref_size': ref_img.size,
    }

# ── SVG Comparison ────────────────────────────────────────────────────────

def score_svgs(reference_svg, attempt_svg, size=(512, 512)):
    """
    Compare two SVG strings by rendering them to PNG then diffing.
    Requires cairosvg.
    
    Returns same dict as pixel_diff().
    """
    try:
        import cairosvg
    except ImportError:
        raise ImportError("cairosvg required for SVG comparison: pip install cairosvg --break-system-packages")

    w, h = size
    ref_bytes = cairosvg.svg2png(bytestring=reference_svg.encode(), output_width=w, output_height=h)
    att_bytes = cairosvg.svg2png(bytestring=attempt_svg.encode(), output_width=w, output_height=h)
    return pixel_diff(ref_bytes, att_bytes)

# ── Dominant Color Extraction ─────────────────────────────────────────────

def dominant_colors(image_source, n=10, bucket_size=16):
    """
    Extract the N most common colors from an image.
    bucket_size: quantization level (smaller = more precise but more colors)
    
    Returns list of (hex_color, pixel_count) tuples.
    """
    from collections import Counter
    img = load_image(image_source)
    arr = np.array(img)
    pixels = arr.reshape(-1, 4)
    # Only count visible pixels
    visible = pixels[pixels[:, 3] > 128]
    # Quantize
    quantized = (visible[:, :3] // bucket_size * bucket_size)
    counts = Counter(map(tuple, quantized.tolist()))
    top = counts.most_common(n)
    return [(f'#{r:02x}{g:02x}{b:02x}', count) for (r,g,b), count in top]

# ── Content Analysis ──────────────────────────────────────────────────────

def analyze_image(image_source):
    """
    Full analysis of an image for canvas reconstruction planning.
    Returns dict with size, palette, content bounds, edge density, type guess.
    """
    from PIL import ImageFilter
    img = load_image(image_source)
    w, h = img.size
    arr = np.array(img)

    # Content bounding box (non-transparent pixels)
    alpha = arr[:,:,3]
    rows = np.any(alpha > 0, axis=1)
    cols = np.any(alpha > 0, axis=0)
    if rows.any():
        rmin, rmax = int(np.where(rows)[0][0]), int(np.where(rows)[0][-1])
        cmin, cmax = int(np.where(cols)[0][0]), int(np.where(cols)[0][-1])
        bounds = {'x': cmin, 'y': rmin, 'w': cmax-cmin, 'h': rmax-rmin}
    else:
        bounds = {'x': 0, 'y': 0, 'w': w, 'h': h}

    # Edge density (high = complex shapes, low = flat regions)
    gray = img.convert('L')
    edges = np.array(gray.filter(ImageFilter.FIND_EDGES))
    edge_density = float((edges > 30).sum() / edges.size)

    # Unique color count
    pixels = arr.reshape(-1, 4)
    visible = pixels[pixels[:,3] > 128]
    unique_colors = len(set(map(tuple, visible[:,:3].tolist())))

    # Guess image type
    if unique_colors < 32 and edge_density > 0.05:
        image_type = 'pixel_art'
    elif unique_colors < 100:
        image_type = 'flat_illustration'
    elif edge_density < 0.03:
        image_type = 'photorealistic_smooth'
    else:
        image_type = 'photorealistic_detailed'

    return {
        'size': (w, h),
        'bounds': bounds,
        'unique_colors': unique_colors,
        'edge_density': edge_density,
        'image_type': image_type,
        'palette': dominant_colors(img, n=8),
        'has_transparency': bool((arr[:,:,3] < 255).any()),
        'is_canvas_feasible': image_type in ('pixel_art', 'flat_illustration'),
    }

# ── Heatmap Generator ─────────────────────────────────────────────────────

def save_diff_heatmap(diff_arr, output_path, colorize=True):
    """
    Save a visual diff heatmap from a diff array (output of pixel_diff).
    Red = big difference, dark = small difference.
    """
    normalized = (diff_arr / diff_arr.max() * 255).astype(np.uint8) if diff_arr.max() > 0 else diff_arr.astype(np.uint8)
    if colorize:
        # Red channel = error, makes it easy to see
        heatmap = np.zeros((*normalized.shape, 3), dtype=np.uint8)
        heatmap[:,:,0] = normalized  # Red
        heatmap[:,:,1] = 0
        heatmap[:,:,2] = 0
        img = Image.fromarray(heatmap, 'RGB')
    else:
        img = Image.fromarray(normalized, 'L')
    img.save(output_path)
    return output_path

