import sys
import os
import json
from datetime import datetime

# Palette: 0 (none) to 5 (maximum contribution intensity)
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

def render_heatmap(json_path="data/contributions.json", output_path="contrib-heatmap.svg"):
    print(f"Loading contributions from {json_path}...")
    if not os.path.exists(json_path):
        print(f"Error: {json_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    days = data.get("days", [])
    total_last_year = data.get("total_last_year", 0)
    username = data.get("username", "developer")

    # Handle empty/missing days list
    if not days:
        print("Warning: Empty contributions list in JSON. Generating fallback SVG.")
        # Create a fallback empty-state SVG so the Action doesn't fail
        generate_fallback_svg(output_path, username)
        return

    # 1. Parse dates and calculate offsets
    # Parse each day's date string into a datetime object
    parsed_days = []
    for day in days:
        try:
            dt = datetime.strptime(day["date"], "%Y-%m-%d")
            parsed_days.append({
                "date": dt,
                "count": day["count"],
                "level": day["level"]
            })
        except Exception as e:
            print(f"Skipping malformed day entry: {day}. Error: {e}", file=sys.stderr)

    if not parsed_days:
        print("Warning: No valid days parsed. Generating fallback SVG.")
        generate_fallback_svg(output_path, username)
        return

    # Sort days chronologically
    parsed_days.sort(key=lambda d: d["date"])

    # Determine first Sunday to anchor the grid (column 0, row 0)
    # weekday() is 0 for Monday, 6 for Sunday.
    # isoweekday() is 7 for Sunday, 1 for Monday.
    # Let's use strftime("%w") which is "0" for Sunday, "1" for Monday, ..., "6" for Saturday.
    first_day = parsed_days[0]["date"]
    first_weekday = int(first_day.strftime("%w")) # 0 = Sunday

    # The Sunday preceding or equal to the first day
    # Subtract first_weekday days from first_day
    from datetime import timedelta
    first_sunday = first_day - timedelta(days=first_weekday)

    # Place days into grid coordinates (col, row)
    grid = {}
    max_col = 0
    max_count = max((d["count"] for d in parsed_days), default=0)

    for d in parsed_days:
        offset = (d["date"] - first_sunday).days
        col = offset // 7
        row = offset % 7 # 0 = Sunday, 6 = Saturday
        grid[(col, row)] = d
        if col > max_col:
            max_col = col

    # Limit to 53 columns (0 to 52) for classic 53-week view
    cols_count = min(53, max_col + 1)

    # 2. Setup SVG specs
    width = 860
    height = 180
    bg_color = "#0d1117"
    border_color = "#30363d"
    text_color = "#c9d1d9"
    sub_text_color = "#8b949e"

    box_size = 11
    gap = 3
    grid_start_x = 60
    grid_start_y = 40

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append('  <style>')
    svg.append('    .heatmap-text { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 11px; }')
    svg.append('    .month-label { fill: #8b949e; }')
    svg.append('    .wday-label { fill: #8b949e; }')
    svg.append('    .stat-text { fill: #c9d1d9; font-weight: bold; font-size: 12px; }')
    svg.append('    .legend-text { fill: #8b949e; font-size: 11px; }')
    svg.append('  </style>')

    # Outer container with border
    svg.append(f'  <rect width="{width}" height="{height}" rx="8" fill="{bg_color}" stroke="{border_color}" stroke-width="1.5" />')

    # Draw Weekday labels (Mon, Wed, Fri) on the left
    # Rows: 1=Mon, 3=Wed, 5=Fri
    wdays = {1: "Mon", 3: "Wed", 5: "Fri"}
    for r_idx, label in wdays.items():
        y_pos = grid_start_y + r_idx * (box_size + gap) + 10
        svg.append(f'  <text x="25" y="{y_pos}" class="heatmap-text wday-label">{label}</text>')

    # Keep track of month labels to place above columns
    # We write a month label when the month changes, but keep spacing
    month_labels = []
    last_month_name = None
    last_month_col = -10

    # Draw Calendar Grid
    for col in range(cols_count):
        # Determine if we should draw a month label for this column
        # Let's check the month name of the first day in this week column
        col_sunday = first_sunday + timedelta(weeks=col)
        # Find if any day in this column starts a new month
        # We look at the date of Wednesday of this column's week for labeling (common standard)
        mid_week_day = col_sunday + timedelta(days=3)
        month_name = mid_week_day.strftime("%b")

        if month_name != last_month_name and (col - last_month_col >= 3):
            month_labels.append((col, month_name))
            last_month_name = month_name
            last_month_col = col

        for row in range(7):
            day_data = grid.get((col, row))

            # Draw box even if no data exists in grid (fill with color 0)
            if day_data:
                count = day_data["count"]
                # Map level (usually 0-4, but let's map safely)
                # GitHub's exact level-bucketing logic is not public, so we approximate
                level = day_data["level"]
                # Clamp level between 0 and 5
                color_idx = max(0, min(len(PALETTE) - 1, level))
            else:
                count = 0
                color_idx = 0

            fill_color = PALETTE[color_idx]

            x_pos = grid_start_x + col * (box_size + gap)
            y_pos = grid_start_y + row * (box_size + gap)

            # Diagonal animation reveal staggered by col + row
            delay = f"{(col + row) * 0.012:.3f}s"

            svg.append(f'  <g opacity="0">')
            svg.append(f'    <animate attributeName="opacity" from="0" to="1" begin="{delay}" dur="0.4s" fill="freeze" />')
            svg.append(f'    <rect x="{x_pos}" y="{y_pos}" width="{box_size}" height="{box_size}" rx="2" ry="2" fill="{fill_color}">')
            svg.append(f'      <title>{count} contributions</title>')
            svg.append(f'    </rect>')
            svg.append('  </g>')

    # Render Month Labels
    for col, m_name in month_labels:
        x_pos = grid_start_x + col * (box_size + gap)
        y_pos = grid_start_y - 10
        svg.append(f'  <text x="{x_pos}" y="{y_pos}" class="heatmap-text month-label">{m_name}</text>')

    # Footer elements
    footer_y = height - 20

    # Stats Line (total, streak, etc.)
    streak_curr = data.get("streak_current", 0)
    streak_long = data.get("streak_longest", 0)
    stat_line = f"{total_last_year:,} contributions in the last year | Current Streak: {streak_curr} days | Longest: {streak_long} days"
    svg.append(f'  <text x="35" y="{footer_y}" class="heatmap-text stat-text">{stat_line}</text>')

    # Legend on the right: "Less" [color 0..4] "More"
    legend_start_x = width - 180
    svg.append(f'  <text x="{legend_start_x - 35}" y="{footer_y}" class="heatmap-text legend-text">Less</text>')

    for i, color in enumerate(PALETTE):
        leg_x = legend_start_x + i * (box_size + 2)
        leg_y = footer_y - 10
        svg.append(f'  <rect x="{leg_x}" y="{leg_y}" width="{box_size}" height="{box_size}" rx="2" ry="2" fill="{color}" />')

    svg.append(f'  <text x="{legend_start_x + len(PALETTE) * (box_size + 2) + 5}" y="{footer_y}" class="heatmap-text legend-text">More</text>')

    svg.append('</svg>')

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    print(f"Successfully rendered contribution heatmap to {output_path}")


def generate_fallback_svg(output_path, username):
    width = 860
    height = 180
    bg_color = "#0d1117"
    border_color = "#30363d"
    text_color = "#c9d1d9"
    sub_text_color = "#8b949e"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append('  <style>')
    svg.append('    .heatmap-text { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 13px; fill: #c9d1d9; }')
    svg.append('  </style>')
    svg.append(f'  <rect width="{width}" height="{height}" rx="8" fill="{bg_color}" stroke="{border_color}" stroke-width="1.5" />')
    svg.append(f'  <text x="40" y="95" class="heatmap-text">Contributions calendar for {username} is currently loading...</text>')
    svg.append('</svg>')

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))


if __name__ == "__main__":
    json_input = "data/contributions.json"
    svg_output = "contrib-heatmap.svg"

    render_heatmap(json_input, svg_output)
