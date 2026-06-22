"""
tools/palette.py — Shared Color & Palette Utilities
Used by canvas art skills, UI tools, and any color-aware task.

Import:
    import sys; sys.path.insert(0, '/mnt/skills/user/lead-dev')
    from tools.palette import hex_to_rgb, rgb_to_hex, closest_color, extract_palette
"""

import re
import math

# ── Color Conversion ──────────────────────────────────────────────────────

def hex_to_rgb(hex_color):
    """'#ff6600' → (255, 102, 0)"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c*2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    """(255, 102, 0) → '#ff6600'"""
    return f'#{r:02x}{g:02x}{b:02x}'

def rgba_to_hex(r, g, b, a=255):
    """(255, 102, 0, 200) → '#ff6600c8'"""
    if a == 255:
        return f'#{r:02x}{g:02x}{b:02x}'
    return f'#{r:02x}{g:02x}{b:02x}{a:02x}'

def hex_to_rgba_string(hex_color, opacity=1.0):
    """'#ff6600' → 'rgba(255, 102, 0, 1.0)'"""
    r, g, b = hex_to_rgb(hex_color)
    return f'rgba({r}, {g}, {b}, {opacity})'

# ── Color Math ────────────────────────────────────────────────────────────

def color_distance(c1, c2):
    """Euclidean distance between two RGB tuples."""
    return math.sqrt(sum((a-b)**2 for a, b in zip(c1, c2)))

def closest_color(target_hex, palette_hexes):
    """
    Find the closest color in a palette to a target color.
    Returns (closest_hex, distance).
    """
    target_rgb = hex_to_rgb(target_hex)
    best = None
    best_dist = float('inf')
    for h in palette_hexes:
        d = color_distance(target_rgb, hex_to_rgb(h))
        if d < best_dist:
            best_dist = d
            best = h
    return best, best_dist

def lighten(hex_color, amount=0.2):
    """Lighten a color by amount (0-1)."""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * amount))
    g = min(255, int(g + (255 - g) * amount))
    b = min(255, int(b + (255 - b) * amount))
    return rgb_to_hex(r, g, b)

def darken(hex_color, amount=0.2):
    """Darken a color by amount (0-1)."""
    r, g, b = hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - amount)))
    g = max(0, int(g * (1 - amount)))
    b = max(0, int(b * (1 - amount)))
    return rgb_to_hex(r, g, b)

def is_dark(hex_color):
    """Returns True if color is perceived as dark."""
    r, g, b = hex_to_rgb(hex_color)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < 128

def contrasting_text_color(bg_hex):
    """Returns '#ffffff' or '#000000' depending on background."""
    return '#ffffff' if is_dark(bg_hex) else '#000000'

# ── Palette Extraction ────────────────────────────────────────────────────

def extract_palette_from_svg(svg_content):
    """Extract all unique colors from an SVG string."""
    colors = set()
    # Named fills
    for m in re.finditer(r'fill=["\']([^"\']+)["\']', svg_content):
        val = m.group(1)
        if val not in ('none', 'inherit', 'transparent') and not val.startswith('url('):
            colors.add(val)
    # Strokes
    for m in re.finditer(r'stroke=["\']([^"\']+)["\']', svg_content):
        val = m.group(1)
        if val not in ('none', 'inherit'):
            colors.add(val)
    # stop-color
    for m in re.finditer(r'stop-color["\s:]+([#\w().,]+)', svg_content):
        colors.add(m.group(1).strip())
    return sorted(colors)

def extract_palette_from_css(css_content):
    """Extract all color values from a CSS string."""
    colors = set()
    # Hex colors
    colors.update(re.findall(r'#[0-9a-fA-F]{3,8}\b', css_content))
    # rgb/rgba
    colors.update(re.findall(r'rgba?\([^)]+\)', css_content))
    return sorted(colors)

def sort_palette_by_hue(hex_colors):
    """Sort a list of hex colors by hue (rainbow order)."""
    def hue_key(hex_c):
        try:
            r, g, b = [x/255 for x in hex_to_rgb(hex_c)]
            mx = max(r, g, b)
            mn = min(r, g, b)
            if mx == mn:
                return (2, 0, -max(r,g,b))  # grays last
            diff = mx - mn
            if mx == r:
                h = (g - b) / diff % 6
            elif mx == g:
                h = (b - r) / diff + 2
            else:
                h = (r - g) / diff + 4
            return (0, h, -max(r,g,b))
        except:
            return (3, 0, 0)
    return sorted(hex_colors, key=hue_key)

# ── Canvas Color Helpers ──────────────────────────────────────────────────

def color_to_canvas(color_string, opacity=1.0):
    """
    Convert any color string to a canvas-ready string.
    Handles: hex, rgb(), rgba(), named colors, fill-opacity combos.
    
    Returns canvas fillStyle/strokeStyle string.
    """
    color = color_string.strip()

    # Already rgba
    if color.startswith('rgba('):
        if opacity < 1.0:
            # Modify existing alpha
            parts = re.findall(r'[\d.]+', color)
            if len(parts) >= 4:
                r, g, b = parts[0], parts[1], parts[2]
                a = float(parts[3]) * opacity
                return f'rgba({r}, {g}, {b}, {a:.3f})'
        return color

    # rgb() → add opacity
    if color.startswith('rgb('):
        if opacity < 1.0:
            parts = re.findall(r'\d+', color)
            if len(parts) >= 3:
                return f'rgba({parts[0]}, {parts[1]}, {parts[2]}, {opacity:.3f})'
        return color

    # Hex → rgba if opacity needed
    if color.startswith('#'):
        if opacity < 1.0:
            try:
                r, g, b = hex_to_rgb(color)
                return f'rgba({r}, {g}, {b}, {opacity:.3f})'
            except:
                pass
        return color

    # Pass through named colors
    return color

def build_gradient_canvas(gradient_type, stops, coords):
    """
    Build canvas gradient creation code string.
    
    gradient_type: 'linear' | 'radial'
    stops: [(offset, color), ...]  e.g. [(0, '#ff0000'), (1, '#0000ff')]
    coords: for linear: (x0, y0, x1, y1)
            for radial: (x0, y0, r0, x1, y1, r1)
    
    Returns JS code string.
    """
    if gradient_type == 'linear':
        x0, y0, x1, y1 = coords
        code = f"const grad = ctx.createLinearGradient({x0}, {y0}, {x1}, {y1});\n"
    else:
        x0, y0, r0, x1, y1, r1 = coords
        code = f"const grad = ctx.createRadialGradient({x0}, {y0}, {r0}, {x1}, {y1}, {r1});\n"

    for offset, color in stops:
        code += f"grad.addColorStop({offset}, '{color}');\n"
    code += "ctx.fillStyle = grad;"
    return code

