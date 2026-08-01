import sys
import os
import cv2
import numpy as np
from PIL import Image

def prep_photo(photo_path, output_path="source-prepped.png"):
    # First, import rembg (only when needed, so we don't crash if it's not present for daily jobs)
    try:
        from rembg import remove
    except ImportError as e:
        print("Error: rembg is required for prep_photo.py. Install it using scripts/requirements.txt", file=sys.stderr)
        raise e

    print(f"Loading image from {photo_path}...")
    if not os.path.exists(photo_path):
        print(f"Error: {photo_path} does not exist.", file=sys.stderr)
        sys.exit(1)

    # Open image with PIL
    input_image = Image.open(photo_path)

    print("Removing background with rembg...")
    # rembg expects a PIL image or numpy array and returns same type
    no_bg_image = remove(input_image)

    print("Compositing onto a pure white background...")
    # Create white canvas of the same size
    white_bg = Image.new("RGBA", no_bg_image.size, (255, 255, 255, 255))
    # Paste the transparent subject image onto the white background
    # using the transparent image itself as the alpha mask
    white_bg.paste(no_bg_image, (0, 0), no_bg_image)

    # Convert to grayscale numpy array for OpenCV CLAHE processing
    gray_image = cv2.cvtColor(np.array(white_bg), cv2.COLOR_RGBA2GRAY)

    print("Applying CLAHE contrast enhancement...")
    # Apply CLAHE to boost contrast locally
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray_image)

    # Save output image
    cv2.imwrite(output_path, enhanced)
    print(f"Successfully saved prepped photo to {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <photo_path> [output_path]")
        sys.exit(1)

    photo_input = sys.argv[1]
    photo_output = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"
    prep_photo(photo_input, photo_output)

