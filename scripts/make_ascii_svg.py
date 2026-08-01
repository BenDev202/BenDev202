import sys
import os
from PIL import Image

RAMP = " .`:-=+*cs#%@"  # Bright (index 0, space) to dark (index len-1, '@')

def make_ascii_svg(image_path, output_path="avi-ascii.svg", cols=100, rows=53, text_color="#c9d1d9", bg_color="#0d1117"):
    """
    Converts prepped photo (or synthetic image) into a self-typing ASCII SVG.
    """
    print(f"Opening image: {image_path}")
    if not os.path.exists(image_path):
        print(f"Error: {image_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    img = Image.open(image_path).convert("L")  # Ensure grayscale

    # Resize image tocols x rows
    # SVG typical font-aspect ratio is about 0.6 (height of character is larger than width),
    # but let's downsample exactly to cols x rows so we get exactly that aspect ratio grid.
    img_resized = img.resize((cols, rows), Image.Resampling.LANCZOS)

    ascii_rows = []
    ramp_len = len(RAMP)

    for y in range(rows):
        row_chars = []
        for x in range(cols):
            pixel = img_resized.getpixel((x, y))
            # Map 0-255 to RAMP index. Note that RAMP has bright (space) first, dark (dense) last.
            # 255 (white) should map to 0 (space). 0 (black) should map to ramp_len - 1 (@).
            val = int((255 - pixel) * (ramp_len - 1) / 255.0)
            # clamp just in case
            val = max(0, min(ramp_len - 1, val))
            row_chars.append(RAMP[val])
        ascii_rows.append("".join(row_chars))

    # We will output as an SVG file.
    # To support monospace text layout properly:
    # Font size: e.g., 12px, spacing, etc.
    # We want exact sizing. Let's make font-size 12px.
    # Character width is around 7.2px, height around 14px.
    # So width = cols * 7.2, height = rows * 14.
    char_width = 7.2
    char_height = 14.0
    svg_width = cols * char_width
    svg_height = rows * char_height

    # Let's escape the characters for XML compatibility.
    escaped_rows = []
    for row in ascii_rows:
        escaped = row.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;")
        escaped_rows.append(escaped)

    # Generate the self-typing SVG animation.
    # For each row, we wrap it in a <g> with a clip-path.
    # The clip-path contains a <rect> whose width animates from 0 to svg_width.
    # Animations are staggered: row_index * 0.05s, dur="0.5s", fill="freeze".

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="{svg_width}" height="{svg_height}">')
    svg_lines.append(f'  <rect width="100%" height="100%" fill="{bg_color}" />')

    # Clip paths definition
    svg_lines.append('  <defs>')
    for i in range(rows):
        begin_time = f"{i * 0.05:.3f}s"
        svg_lines.append(f'    <clipPath id="cp-{i}">')
        svg_lines.append(f'      <rect x="0" y="{i * char_height:.1f}" width="0" height="{char_height:.1f}">')
        svg_lines.append(f'        <animate attributeName="width" from="0" to="{svg_width}" begin="{begin_time}" dur="0.5s" fill="freeze" />')
        svg_lines.append('      </rect>')
        svg_lines.append('    </clipPath>')
    svg_lines.append('  </defs>')

    # Text container
    svg_lines.append(f'  <text xml:space="preserve" font-family="Courier New, Courier, monospace" font-size="12" font-weight="bold" fill="{text_color}">')
    for i, row_text in enumerate(escaped_rows):
        y_pos = (i + 1) * char_height - 3  # Adjust vertical baseline slightly
        # We wrap the tspan inside a g that references the clip-path
        svg_lines.append(f'    <tspan x="0" y="{y_pos:.1f}" clip-path="url(#cp-{i})">{row_text}</tspan>')
    svg_lines.append('  </text>')

    svg_lines.append('</svg>')

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg_lines))

    print(f"Successfully generated {output_path} with {cols} columns and {rows} rows.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Convert an image to a self-typing ASCII SVG.")
    parser.add_argument("image_path", help="Path to input image (e.g. source-prepped.png)")
    parser.add_argument("--output", default="avi-ascii.svg", help="Output SVG path")
    parser.add_argument("--cols", type=int, default=100, help="Number of columns in ASCII art")
    parser.add_argument("--rows", type=int, default=53, help="Number of rows in ASCII art")
    args = parser.parse_args()

    make_ascii_svg(args.image_path, args.output, args.cols, args.rows)
