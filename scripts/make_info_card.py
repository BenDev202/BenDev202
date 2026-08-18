#!/usr/bin/env python3
"""
make_info_card.py — Generate a neofetch-style info card SVG.

Creates a terminal-themed panel with a title bar (three colored circles)
and key/value rows that fade/slide in with SMIL animation.

Usage:
    python scripts/make_info_card.py           # animated
    STATIC=1 python scripts/make_info_card.py  # frozen frame, no animation

Output: info-card.svg
"""

import os
import sys
import xml.etree.ElementTree as ET

# ── Dimensions ──────────────────────────────────────────────────────
SVG_W = 490
SVG_H = 300
BG_COLOR = "#0d1117"
BORDER_COLOR = "#30363d"
TITLE_BAR_H = 36
CORNER_R = 8

# ── Typography ──────────────────────────────────────────────────────
FONT = "Consolas, 'Courier New', monospace"
FONT_SIZE = 13
LINE_H = 28
LABEL_COLOR = "#7ee787"  # green accent
VALUE_COLOR = "#c9d1d9"  # muted white
TITLE_COLOR = "#c9d1d9"
SEPARATOR_COLOR = "#30363d"

# ── Content ─────────────────────────────────────────────────────────
# The user should customise these rows with their own real content.


def get_repo_username() -> str:
    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo and "/" in repo:
        return repo.split("/")[1]
    folder = os.path.basename(os.getcwd())
    if folder in ("app", "workspace", "", "github"):
        return "BenDev202"
    return folder


TITLE = f"{get_repo_username()}@github:~"
ROWS = [
    ("Name",     "Armand Benjamin"),
    ("Role",     "Full-Stack Developer"),
    ("Location", "Kigali, Rwanda"),
    ("Work",     "GadaPlus (gadaplus.com)"),
    ("Stack",    "React · Next.js · Node · PHP · Tauri"),
    ("Status",   "Open for freelance & full-time"),
    ("Contact",  "armandbenjamin30@gmail.com"),
]

# ── Animation ───────────────────────────────────────────────────────
STAGGER = 0.25   # seconds between each row's animation start
FADE_DUR = 0.4   # duration of each row's fade-in
SLIDE_PX = 15    # pixels to slide from right


def is_static() -> bool:
    return os.environ.get("STATIC", "").strip() in ("1", "true", "yes")


def build_svg() -> str:
    static = is_static()
    parts = []

    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {SVG_W} {SVG_H}" '
        f'width="{SVG_W}" height="{SVG_H}">'
    )

    # ── Outer frame with rounded corners ──
    parts.append(
        f'  <rect x="0.5" y="0.5" width="{SVG_W - 1}" height="{SVG_H - 1}" '
        f'rx="{CORNER_R}" ry="{CORNER_R}" '
        f'fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1"/>'
    )

    # ── Title bar ──
    parts.append(
        f'  <rect x="0.5" y="0.5" width="{SVG_W - 1}" height="{TITLE_BAR_H}" '
        f'rx="{CORNER_R}" ry="{CORNER_R}" fill="#161b22"/>'
    )
    # Flatten the bottom corners of the title bar
    parts.append(
        f'  <rect x="0.5" y="{TITLE_BAR_H - CORNER_R}" '
        f'width="{SVG_W - 1}" height="{CORNER_R}" fill="#161b22"/>'
    )

    # Three circles (close/minimize/maximize)
    cx_start = 20
    cy = TITLE_BAR_H // 2 + 1
    for i, color in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
        cx = cx_start + i * 20
        parts.append(f'  <circle cx="{cx}" cy="{cy}" r="6" fill="{color}"/>')

    # Title text
    parts.append(
        f'  <text x="{cx_start + 80}" y="{cy + 4}" '
        f'font-family="{FONT}" font-size="{FONT_SIZE}" '
        f'fill="{TITLE_COLOR}" font-weight="bold">{TITLE}</text>'
    )

    # ── Separator line under title bar ──
    sep_y = TITLE_BAR_H + 1
    parts.append(
        f'  <line x1="1" y1="{sep_y}" x2="{SVG_W - 1}" y2="{sep_y}" '
        f'stroke="{SEPARATOR_COLOR}" stroke-width="1"/>'
    )

    # ── Key/value rows ──
    content_y_start = TITLE_BAR_H + 24
    for i, (label, value) in enumerate(ROWS):
        y = content_y_start + i * LINE_H
        begin_t = i * STAGGER

        if static:
            # No animation — just render in place
            parts.append(
                f'  <g>'
            )
        else:
            # Animated: fade-in + slide from right
            parts.append(
                f'  <g opacity="0">'
            )
            parts.append(
                f'    <animate attributeName="opacity" '
                f'from="0" to="1" begin="{begin_t:.2f}s" '
                f'dur="{FADE_DUR}s" fill="freeze"/>'
            )
            parts.append(
                f'    <animateTransform attributeName="transform" '
                f'type="translate" from="{SLIDE_PX} 0" to="0 0" '
                f'begin="{begin_t:.2f}s" dur="{FADE_DUR}s" fill="freeze"/>'
            )

        # Label (green)
        parts.append(
            f'    <text x="28" y="{y}" '
            f'font-family="{FONT}" font-size="{FONT_SIZE}" '
            f'fill="{LABEL_COLOR}" font-weight="bold">'
            f'{escape_xml(label)}</text>'
        )
        # Separator
        parts.append(
            f'    <text x="{28 + 80}" y="{y}" '
            f'font-family="{FONT}" font-size="{FONT_SIZE}" '
            f'fill="{SEPARATOR_COLOR}">│</text>'
        )
        # Value (muted white)
        parts.append(
            f'    <text x="{28 + 96}" y="{y}" '
            f'font-family="{FONT}" font-size="{FONT_SIZE}" '
            f'fill="{VALUE_COLOR}">{escape_xml(value)}</text>'
        )
        parts.append(f'  </g>')

    # ── Bottom accent line ──
    accent_y = SVG_H - 20
    colors = ["#ff5f57", "#febc2e", "#28c840", "#2ea5ff", "#a06cd5", "#ff6ac1"]
    seg_w = (SVG_W - 56) / len(colors)
    for i, c in enumerate(colors):
        x = 28 + i * seg_w
        parts.append(
            f'  <rect x="{x:.1f}" y="{accent_y}" '
            f'width="{seg_w:.1f}" height="3" rx="1.5" fill="{c}"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def validate_xml(svg_str: str) -> bool:
    try:
        ET.fromstring(svg_str)
        return True
    except ET.ParseError as e:
        print(f"[ERROR] SVG is not well-formed XML: {e}", file=sys.stderr)
        return False


def main():
    mode = "STATIC" if is_static() else "ANIMATED"
    print(f"Generating info card ({mode} mode)...")

    svg_str = build_svg()

    print("Validating XML...")
    if not validate_xml(svg_str):
        sys.exit(1)

    out_path = "info-card.svg"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    print(f"Done → {out_path} ({len(svg_str):,} bytes)")


if __name__ == "__main__":
    main()

