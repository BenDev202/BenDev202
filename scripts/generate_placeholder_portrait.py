from PIL import Image, ImageDraw, ImageFont

def draw_placeholder_portrait(output_path="source-prepped.png"):
    # Create a 400x400 image
    # We want strong contrast (white on black/gray) so it maps beautifully to ASCII density
    # White = space (no char), Dark = dense chars (@, %, #)
    img = Image.new("L", (400, 400), color=255) # Pure white background (maps to spaces)
    draw = ImageDraw.Draw(img)

    # Let's draw a stylized coder face/headset icon
    # Draw a circular head (dark gray / black)
    draw.ellipse([100, 80, 300, 280], fill=0) # Black head

    # Draw glasses
    draw.line([130, 160, 270, 160], fill=255, width=8) # Bridge
    draw.ellipse([135, 135, 195, 195], outline=255, width=12) # Left lens
    draw.ellipse([205, 135, 265, 195], outline=255, width=12) # Right lens

    # Draw mouth/smile
    draw.arc([160, 190, 240, 250], start=0, end=180, fill=255, width=10)

    # Draw body/shoulders
    draw.ellipse([40, 300, 360, 480], fill=30)

    # Draw sleek developer laptop with braces `{}`
    # Laptop base
    draw.rectangle([80, 330, 320, 390], fill=80)
    # Braces in white
    # Since we might not have custom font, let's draw braces using lines
    # Left brace {
    draw.line([170, 345, 160, 345], fill=255, width=6)
    draw.line([160, 345, 160, 375], fill=255, width=6)
    draw.line([160, 360, 153, 360], fill=255, width=6)
    # Right brace }
    draw.line([230, 345, 240, 345], fill=255, width=6)
    draw.line([240, 345, 240, 375], fill=255, width=6)
    draw.line([240, 360, 247, 360], fill=255, width=6)

    # Save the image
    img.save(output_path)
    print(f"Generated a gorgeous placeholder developer portrait at {output_path}")

if __name__ == "__main__":
    draw_placeholder_portrait()
