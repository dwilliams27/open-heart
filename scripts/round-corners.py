#!/usr/bin/env python3
"""Apply rounded corner transparency to a sprite PNG.

Usage:
  round-corners.py <input.png> [--radius PIXELS] [--card-size WxH]

Default radius is auto-scaled: 8px for 2x (142x190), 4px for 1x (71x95).

With --card-size: rounds corners of the input image (assumed square), then
centers it on a transparent canvas of the given dimensions.
"""

import sys
from PIL import Image, ImageDraw


def round_corners(img, radius=None):
    """Apply rounded corner transparency to an RGBA image. Returns new image."""
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

    img = img.copy()
    img.putalpha(mask)
    return img


def process(path, radius=None, card_size=None):
    img = Image.open(path).convert("RGBA")

    # Round corners of the image
    img = round_corners(img, radius)

    if card_size:
        # Center the (rounded) image on a transparent canvas
        cw, ch = card_size
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        iw, ih = img.size
        x = (cw - iw) // 2
        y = (ch - ih) // 2
        canvas.paste(img, (x, y), img)
        img = canvas

    img.save(path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: round-corners.py <input.png> [--radius PIXELS] [--card-size WxH]", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    radius = None
    card_size = None

    if "--radius" in sys.argv:
        idx = sys.argv.index("--radius")
        radius = int(sys.argv[idx + 1])

    if "--card-size" in sys.argv:
        idx = sys.argv.index("--card-size")
        wh = sys.argv[idx + 1].split("x")
        card_size = (int(wh[0]), int(wh[1]))

    process(path, radius, card_size)
