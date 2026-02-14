#!/usr/bin/env python3
"""Apply rounded corner transparency to a sprite PNG.

Usage: round-corners.py <input.png> [--radius PIXELS]

Default radius is auto-scaled: 8px for 2x (142x190), 4px for 1x (71x95).
"""

import sys
from PIL import Image, ImageDraw

def round_corners(path, radius=None):
    img = Image.open(path).convert("RGBA")
    w, h = img.size

    if radius is None:
        # Auto-scale: 8px at 142w (2x), 4px at 71w (1x)
        radius = max(2, round(8 * w / 142))

    # Render mask at 4x resolution to avoid pixel alignment issues,
    # then downscale with antialiasing for clean edges
    scale = 4
    sw, sh, sr = w * scale, h * scale, radius * scale
    big_mask = Image.new("L", (sw, sh), 0)
    draw = ImageDraw.Draw(big_mask)
    draw.rounded_rectangle([(0, 0), (sw - 1, sh - 1)], radius=sr, fill=255)
    mask = big_mask.resize((w, h), Image.LANCZOS)

    # Apply mask to alpha channel
    img.putalpha(mask)
    img.save(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: round-corners.py <input.png> [--radius PIXELS]", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    radius = None
    if "--radius" in sys.argv:
        idx = sys.argv.index("--radius")
        radius = int(sys.argv[idx + 1])

    round_corners(path, radius)
