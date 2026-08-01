#!/usr/bin/env python3
"""
make_ascii_svg.py — Convert source-prepped.png into a self-typing SVG.

The SVG uses SMIL <animate> inside <clipPath> rects to create a
left-to-right "typing" wipe, staggered top-to-bottom, that plays
once and then freezes.

Usage:
    python scripts/make_ascii_svg.py

Input:  source-prepped.png (or a synthetic gradient for testing)
Output: avi-ascii.svg

If source-prepped.png doesn't exist, creates a synthetic gradient
test image so the pipeline can be validated without a real photo.
"""

import os
import sys
import xml.etree.ElementTree as ET
from PIL import Image
import numpy as np

# ASCII density ramp: bright (sparse) → dark (dense); leading space = blank
RAMP = " .`:-=+*cs#%@"

# Grid dimensions
COLS = 100
ROWS = 53

# Monochrome fill color (GitHub dark theme text)
FILL_COLOR = "#c9d1d9"

# SVG character sizing
CHAR_W = 7.2     # approximate width of a monospace character
CHAR_H = 13      # line height
FONT_SIZE = 11
FONT_FAMILY = "Consolas, 'Courier New', monospace"

# Animation timing
ROW_STAGGER = 0.05   # seconds between each row's start
ROW_DUR = 0.5        # duration of each row's reveal


def create_synthetic_test_image(path: str):
    """Create a gradient test image when no real photo is available."""
    print("[!] No source-prepped.png found — generating synthetic gradient for testing")
    w, h = 400, 212  # roughly 2:1 matching COLS:ROWS aspect
    arr = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        for x in range(w):
            # Diagonal gradient
            arr[y, x] = int(255 * ((x / w) * 0.5 + (y / h) * 0.5))
    img = Image.fromarray(arr, mode="L")
    img.save(path)
    print(f"    Saved synthetic image to {path}")


def image_to_ascii_grid(img_path: str) -> list[list[str]]:
    """Load an image and convert to a 2D grid of ASCII characters."""
    img = Image.open(img_path).convert("L")
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    pixels = np.array(img)

    grid = []
    for row in pixels:
        line = []
        for brightness in row:
            # Map 0-255 brightness to ramp index (bright=space, dark=@)
            idx = int((255 - brightness) / 255 * (len(RAMP) - 1))
            idx = max(0, min(idx, len(RAMP) - 1))
            line.append(RAMP[idx])
        grid.append(line)
    return grid


def escape_xml(ch: str) -> str:
    """Escape special XML characters."""
    if ch == "&":
        return "&amp;"
    if ch == "<":
        return "&lt;"
    if ch == ">":
        return "&gt;"
    if ch == '"':
        return "&quot;"
    if ch == "'":
        return "&apos;"
    return ch


def build_svg(grid: list[list[str]]) -> str:
    """Build the SVG string with SMIL clip-path typing animation."""
    svg_w = COLS * CHAR_W + 20   # small padding
    svg_h = ROWS * CHAR_H + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w:.1f} {svg_h:.1f}" '
        f'width="{svg_w:.0f}" height="{svg_h:.0f}">'
    )

    # Background
    parts.append(f'  <rect width="100%" height="100%" fill="#0d1117"/>')

    # Defs: one clipPath per row
    parts.append("  <defs>")
    for row_idx in range(len(grid)):
        y = 10 + row_idx * CHAR_H
        row_w = COLS * CHAR_W
        begin_t = row_idx * ROW_STAGGER
        clip_id = f"clip-r{row_idx}"

        parts.append(f'    <clipPath id="{clip_id}">')
        parts.append(f'      <rect x="10" y="{y}" width="0" height="{CHAR_H}">')
        parts.append(
            f'        <animate attributeName="width" '
            f'from="0" to="{row_w:.1f}" '
            f'begin="{begin_t:.2f}s" dur="{ROW_DUR}s" '
            f'fill="freeze"/>'
        )
        parts.append(f'      </rect>')
        parts.append(f'    </clipPath>')
    parts.append("  </defs>")

    # Text rows, each clipped
    for row_idx, row in enumerate(grid):
        clip_id = f"clip-r{row_idx}"
        y = 10 + row_idx * CHAR_H + FONT_SIZE  # baseline offset
        line_text = "".join(escape_xml(ch) for ch in row)

        parts.append(
            f'  <text x="10" y="{y}" '
            f'clip-path="url(#{clip_id})" '
            f'font-family="{FONT_FAMILY}" '
            f'font-size="{FONT_SIZE}" '
            f'fill="{FILL_COLOR}" '
            f'xml:space="preserve">{line_text}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def validate_xml(svg_str: str) -> bool:
    """Parse the SVG as XML to confirm it's well-formed."""
    try:
        ET.fromstring(svg_str)
        return True
    except ET.ParseError as e:
        print(f"[ERROR] SVG is not well-formed XML: {e}", file=sys.stderr)
        return False


def main():
    input_path = "source-prepped.png"

    if not os.path.isfile(input_path):
        create_synthetic_test_image(input_path)

    print(f"Loading {input_path}...")
    grid = image_to_ascii_grid(input_path)
    print(f"Grid: {len(grid[0])} cols × {len(grid)} rows")

    print("Building SVG...")
    svg_str = build_svg(grid)

    print("Validating XML...")
    if not validate_xml(svg_str):
        sys.exit(1)

    out_path = "avi-ascii.svg"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    print(f"Done → {out_path} ({len(svg_str):,} bytes)")


if __name__ == "__main__":
    main()
