import sys
import os

def generate_info_card(output_path="info-card.svg", static_mode=False):
    # Constants
    width = 490
    height = 300
    bg_color = "#0d1117"
    border_color = "#30363d"
    text_color = "#c9d1d9"
    accent_color = "#58a6ff"  # Soft blue
    label_color = "#7d8590"   # Grayish

    # User-specific information
    info_rows = [
        ("User", "BenDev202 (Rukizangabo Armand Benjamin)"),
        ("Role", "Full-Stack Developer @ GadaPlus"),
        ("Location", "Kigali, Rwanda"),
        ("Focus", "Next.js, React, Node.js, Tauri (Desktop)"),
        ("Stack", "TypeScript, PHP, Python, Supabase, MySQL"),
        ("Email", "armandbenjamin30@gmail.com"),
        ("Status", "Building digital solutions for African businesses!"),
    ]

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')

    # Styles
    svg.append('  <style>')
    svg.append('    .terminal-title { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 13px; fill: #8b949e; font-weight: bold; }')
    svg.append('    .terminal-text { font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, Liberation Mono, monospace; font-size: 13px; }')
    svg.append('  </style>')

    # Card Background with border
    svg.append(f'  <rect width="{width}" height="{height}" rx="8" fill="{bg_color}" stroke="{border_color}" stroke-width="1.5" />')

    # Terminal Title Bar Separator
    svg.append(f'  <line x1="0" y1="36" x2="{width}" y2="36" stroke="{border_color}" stroke-width="1.5" />')

    # Window Buttons (Red, Yellow, Green)
    svg.append('  <circle cx="20" cy="18" r="6" fill="#ff5f56" />')
    svg.append('  <circle cx="40" cy="18" r="6" fill="#ffbd2e" />')
    svg.append('  <circle cx="60" cy="18" r="6" fill="#27c93f" />')

    # Terminal Title Text
    title_text = "armand@github:~$"
    svg.append(f'  <text x="80" y="22" class="terminal-title">{title_text}</text>')

    # Content rows
    start_y = 65
    row_height = 30

    for i, (label, val) in enumerate(info_rows):
        y_pos = start_y + i * row_height

        # We wrap each row in a `<g>` group. If static_mode is False, we animate the group.
        group_attrs = ""
        animation_elements = ""

        if not static_mode:
            # We fade in and slide up slightly (from y+5 to y)
            delay = f"{i * 0.25:.2f}s"
            group_attrs = ' opacity="0"'
            animation_elements = (
                f'    <animate attributeName="opacity" from="0" to="1" begin="{delay}" dur="0.4s" fill="freeze" />\n'
                f'    <animateTransform attributeName="transform" type="translate" from="0 8" to="0 0" begin="{delay}" dur="0.4s" fill="freeze" />'
            )

        svg.append(f'  <g class="terminal-text"{group_attrs}>')
        if animation_elements:
            svg.append(animation_elements)

        # Draw key and value
        # Prompt symbol e.g., "❯"
        svg.append(f'    <text x="25" y="{y_pos}" fill="{accent_color}">❯</text>')
        # Label
        svg.append(f'    <text x="42" y="{y_pos}" fill="{label_color}" font-weight="bold">{label}:</text>')
        # Value. Position depends on max label length. Maximum label length is 8 ("Location").
        # At 13px font, character width is ~8px. 42 + 8 * 8 + 10 = 116px is a safe start for value.
        svg.append(f'    <text x="115" y="{y_pos}" fill="{text_color}">{val}</text>')
        svg.append('  </g>')

    svg.append('</svg>')

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(svg))

    print(f"Successfully generated info-card SVG at {output_path} (static={static_mode})")

if __name__ == "__main__":
    static_env = os.environ.get("STATIC") == "1"
    generate_info_card("info-card.svg", static_mode=static_env)
