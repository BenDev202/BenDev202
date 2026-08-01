#!/usr/bin/env python3
"""
prep_photo.py — Prepare a photo for ASCII conversion.

Removes the background, composites onto white, converts to grayscale,
and applies CLAHE contrast enhancement to make the image convert
to legible ASCII art.

Usage:
    python scripts/prep_photo.py source-photo.jpg

Output:
    source-prepped.png

Dependencies (local only, NOT needed in CI):
    pip install pillow numpy opencv-python rembg

NOTE: rembg downloads a ~170 MB ONNX model on first run.
      This requires network access to GitHub release assets.
"""

import sys
import os
import numpy as np
import cv2
from PIL import Image
from rembg import remove


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <photo_path>")
        sys.exit(1)

    photo_path = sys.argv[1]
    if not os.path.isfile(photo_path):
        print(f"Error: file not found: {photo_path}")
        sys.exit(1)

    print(f"[1/4] Loading {photo_path}...")
    with open(photo_path, "rb") as f:
        input_bytes = f.read()

    print("[2/4] Removing background (rembg)...")
    output_bytes = remove(input_bytes)
    fg = Image.open(__import__("io").BytesIO(output_bytes)).convert("RGBA")

    # Composite onto pure white background so the background maps
    # to the blank/space end of the ASCII density ramp.
    print("[3/4] Compositing onto white background...")
    white_bg = Image.new("RGBA", fg.size, (255, 255, 255, 255))
    composite = Image.alpha_composite(white_bg, fg).convert("L")  # grayscale

    # Convert to numpy for OpenCV CLAHE
    gray = np.array(composite)

    print("[4/4] Applying CLAHE contrast enhancement...")
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    out_path = "source-prepped.png"
    cv2.imwrite(out_path, enhanced)
    print(f"Done → {out_path} ({enhanced.shape[1]}x{enhanced.shape[0]})")


if __name__ == "__main__":
    main()
