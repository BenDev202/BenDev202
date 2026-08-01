#!/usr/bin/env python3
"""
render_heatmap_svg.py — Render contribution data as an animated heatmap SVG.

Reads data/contributions.json and produces a 53-week × 7-day contribution
calendar with rounded colored boxes that reveal diagonally via SMIL animation.

Usage:
    python scripts/render_heatmap_svg.py

Input:  data/contributions.json
Output: contrib-heatmap.svg

Palette and level-bucketing are approximations of GitHub's own contribution
graph colors. GitHub's exact internal thresholds are not public.
"""

import json
import math
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# ── Color palette: index 0 = no contributions, 1-5 = low→high ──
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

# ── Grid sizing ──
CELL_SIZE = 13
CELL_GAP = 3
CELL_R = 2           # border-radius
WEEKS = 53
DAYS_PER_WEEK = 7

# ── Layout offsets ──
LEFT_LABEL_W = 36     # space for weekday labels
TOP_LABEL_H = 20      # space for month labels
PADDING = 16
LEGEND_H = 40         # space for bottom legend + stats

# ── Typography ──
FONT = "'Segoe UI', Ubuntu, Roboto, sans-serif"
MONO_FONT = "Consolas, 'Courier New', monospace"
FONT_SIZE = 10
LABEL_COLOR = "#8b949e"
STAT_COLOR = "#c9d1d9"

# ── Animation ──
ANIM_STAGGER = 0.008  # seconds between each cell (diagonal)
ANIM_DUR = 0.15       # duration of each cell's reveal
SLIDE_PX = 5          # slide distance


def load_contributions(path: str) -> dict:
    """Load contributions.json."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def bucket_level(count: int, max_count: int) -> int:
    """
    Bucket a count into 0-5 level relative to the max day count.

    This is an approximation — GitHub's exact thresholds are not public.
    We use quartile-based bucketing on a log-ish scale.
    """
    if count == 0:
        return 0
    if max_count == 0:
        return 0

    ratio = count / max_count

    if ratio <= 0.15:
        return 1
    elif ratio <= 0.35:
        return 2
    elif ratio <= 0.55:
        return 3
    elif ratio <= 0.80:
        return 4
    else:
        return 5


def organize_into_weeks(days: list[dict]) -> list[list[dict | None]]:
    """
    Organize days into a week-column layout matching GitHub's calendar.
    Each week is a list of 7 slots (Sunday=0 through Saturday=6).
    """
    if not days:
        return []

    # Sort by date
    sorted_days = sorted(days, key=lambda d: d["date"])

    # Find the starting Sunday
    first_date = datetime.strptime(sorted_days[0]["date"], "%Y-%m-%d")
    first_weekday = first_date.weekday()  # Monday=0, Sunday=6
    # Convert to Sunday=0
    first_dow_sun = (first_weekday + 1) % 7
    start_sunday = first_date - timedelta(days=first_dow_sun)

    # Build date→day lookup
    date_lookup = {d["date"]: d for d in sorted_days}

    # Fill weeks
    weeks = []
    current = start_sunday
    last_date = datetime.strptime(sorted_days[-1]["date"], "%Y-%m-%d")

    while current <= last_date:
        week = []
        for dow in range(7):
            day_date = current + timedelta(days=dow)
            date_str = day_date.strftime("%Y-%m-%d")
            if date_str in date_lookup:
                week.append(date_lookup[date_str])
            else:
                week.append(None)
        weeks.append(week)
        current += timedelta(days=7)

    # Trim to last 53 weeks
    if len(weeks) > WEEKS:
        weeks = weeks[-WEEKS:]

    return weeks


def get_month_labels(weeks: list[list[dict | None]]) -> list[tuple[int, str]]:
    """Get (week_index, month_name) pairs where a new month starts."""
    labels = []
    prev_month = None

    for wi, week in enumerate(weeks):
        for day in week:
            if day is not None:
                month = day["date"][:7]  # "YYYY-MM"
                if month != prev_month:
                    month_name = datetime.strptime(
                        day["date"], "%Y-%m-%d"
                    ).strftime("%b")
                    labels.append((wi, month_name))
                    prev_month = month
                break

    return labels


def build_svg(data: dict) -> str:
    """Build the heatmap SVG with SMIL diagonal reveal animation."""
    days = data.get("days", [])
    total = data.get("total_last_year", 0)

    if not days:
        # Graceful empty state
        return _build_empty_svg(total)

    # Find max count for bucketing
    max_count = max((d["count"] for d in days), default=0)

    # Organize into week columns
    weeks = organize_into_weeks(days)

    # Calculate SVG dimensions
    grid_w = len(weeks) * (CELL_SIZE + CELL_GAP) - CELL_GAP
    grid_h = DAYS_PER_WEEK * (CELL_SIZE + CELL_GAP) - CELL_GAP
    svg_w = PADDING * 2 + LEFT_LABEL_W + grid_w
    svg_h = PADDING * 2 + TOP_LABEL_H + grid_h + LEGEND_H

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {svg_w} {svg_h}" '
        f'width="{svg_w}" height="{svg_h}">'
    )

    # Background
    parts.append(f'  <rect width="100%" height="100%" fill="#0d1117" rx="6"/>')

    # ── Month labels ──
    month_labels = get_month_labels(weeks)
    for wi, month_name in month_labels:
        x = PADDING + LEFT_LABEL_W + wi * (CELL_SIZE + CELL_GAP)
        y = PADDING + FONT_SIZE + 2
        parts.append(
            f'  <text x="{x}" y="{y}" font-family="{FONT}" '
            f'font-size="{FONT_SIZE}" fill="{LABEL_COLOR}">{month_name}</text>'
        )

    # ── Weekday labels (Mon, Wed, Fri) ──
    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for dow, name in weekday_labels.items():
        y = PADDING + TOP_LABEL_H + dow * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 2
        parts.append(
            f'  <text x="{PADDING}" y="{y}" font-family="{FONT}" '
            f'font-size="{FONT_SIZE}" fill="{LABEL_COLOR}">{name}</text>'
        )

    # ── Calendar cells with diagonal reveal ──
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week):
            if day is None:
                continue

            x = PADDING + LEFT_LABEL_W + wi * (CELL_SIZE + CELL_GAP)
            y = PADDING + TOP_LABEL_H + di * (CELL_SIZE + CELL_GAP)

            level = bucket_level(day["count"], max_count)
            color = PALETTE[level]

            # Diagonal stagger: (week_index + day_index)
            diag = wi + di
            begin_t = diag * ANIM_STAGGER

            parts.append(f'  <rect x="{x}" y="{y}" '
                         f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
                         f'rx="{CELL_R}" ry="{CELL_R}" fill="{color}" opacity="0">')
            parts.append(
                f'    <animate attributeName="opacity" '
                f'from="0" to="1" begin="{begin_t:.3f}s" '
                f'dur="{ANIM_DUR}s" fill="freeze"/>')
            parts.append(
                f'    <animateTransform attributeName="transform" '
                f'type="translate" from="0 {SLIDE_PX}" to="0 0" '
                f'begin="{begin_t:.3f}s" dur="{ANIM_DUR}s" fill="freeze"/>')
            parts.append(f'  </rect>')

    # ── Legend: Less → More ──
    legend_y = PADDING + TOP_LABEL_H + grid_h + 18
    legend_x_start = svg_w - PADDING - 6 * (CELL_SIZE + CELL_GAP) - 60

    parts.append(
        f'  <text x="{legend_x_start}" y="{legend_y + CELL_SIZE - 2}" '
        f'font-family="{FONT}" font-size="{FONT_SIZE}" '
        f'fill="{LABEL_COLOR}">Less</text>'
    )

    swatch_x = legend_x_start + 32
    for i, color in enumerate(PALETTE):
        x = swatch_x + i * (CELL_SIZE + CELL_GAP)
        parts.append(
            f'  <rect x="{x}" y="{legend_y}" '
            f'width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="{CELL_R}" ry="{CELL_R}" fill="{color}"/>'
        )

    more_x = swatch_x + len(PALETTE) * (CELL_SIZE + CELL_GAP) + 4
    parts.append(
        f'  <text x="{more_x}" y="{legend_y + CELL_SIZE - 2}" '
        f'font-family="{FONT}" font-size="{FONT_SIZE}" '
        f'fill="{LABEL_COLOR}">More</text>'
    )

    # ── Footer stat line ──
    footer_y = legend_y + CELL_SIZE + 2
    parts.append(
        f'  <text x="{PADDING + LEFT_LABEL_W}" y="{footer_y}" '
        f'font-family="{MONO_FONT}" font-size="{FONT_SIZE}" '
        f'fill="{STAT_COLOR}">{total:,} contributions in the last year</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


def _build_empty_svg(total: int) -> str:
    """Build a minimal SVG when no contribution data is available."""
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 180" '
        'width="860" height="180">'
        '<rect width="100%" height="100%" fill="#0d1117" rx="6"/>'
        '<text x="430" y="90" text-anchor="middle" font-family="\'Segoe UI\', '
        'sans-serif" font-size="14" fill="#8b949e">'
        f'{total:,} contributions — no calendar data available</text>'
        '</svg>'
    )


def validate_xml(svg_str: str) -> bool:
    try:
        ET.fromstring(svg_str)
        return True
    except ET.ParseError as e:
        print(f"[ERROR] SVG is not well-formed XML: {e}", file=sys.stderr)
        return False


def main():
    input_path = "data/contributions.json"

    if not os.path.isfile(input_path):
        print(f"Error: {input_path} not found. Run fetch_contributions.py first.")
        sys.exit(1)

    print(f"Loading {input_path}...")
    data = load_contributions(input_path)

    total = data.get("total_last_year", 0)
    num_days = len(data.get("days", []))
    print(f"  {num_days} days, {total:,} total contributions")

    print("Building heatmap SVG...")
    svg_str = build_svg(data)

    print("Validating XML...")
    if not validate_xml(svg_str):
        sys.exit(1)

    # Verify footer total matches JSON
    if f"{total:,} contributions" in svg_str:
        print(f"✓ Footer total matches JSON: {total:,}")
    else:
        print(f"⚠ Footer total might not match JSON total ({total:,})")

    out_path = "contrib-heatmap.svg"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(svg_str)
    print(f"Done → {out_path} ({len(svg_str):,} bytes)")


if __name__ == "__main__":
    main()

