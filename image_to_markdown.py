# image_to_markdown.py
#
# Converts an image to a structured Markdown file using Tesseract OCR and OpenCV.
#
# ============================================================
# INSTALL INSTRUCTIONS: Tesseract Binary
# ============================================================
#
# This script requires the Tesseract OCR binary to be installed
# and available on your system PATH.
#
# Windows:
#   Download the installer from:
#   https://github.com/UB-Mannheim/tesseract/wiki
#   After installation, add the Tesseract directory to your PATH,
#   e.g. C:\Program Files\Tesseract-OCR
#
# macOS (via Homebrew):
#   brew install tesseract
#
# Linux (Debian/Ubuntu via apt):
#   sudo apt-get update && sudo apt-get install -y tesseract-ocr
#
# For additional language packs (e.g. French):
#   macOS:  brew install tesseract-lang
#   Linux:  sudo apt-get install -y tesseract-ocr-fra
#
# Verify installation:
#   tesseract --version
#
# Python dependencies (install via pip):
#   pip install -r requirements.txt
# ============================================================

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".tif", ".bmp"}


@dataclass
class ImageMetadata:
    filename: str
    width: int
    height: int
    file_size: int  # bytes
    lang: str       # Tesseract language code used


@dataclass
class VisionResult:
    contour_count: int
    dominant_shapes: list[str]   # e.g. ["rectangle", "circle"]
    line_count: int
    line_orientations: list[str] # e.g. ["horizontal", "vertical"]
    region_count: int
    region_positions: list[str]  # e.g. ["top-left", "center"]
    is_empty: bool               # True when no significant structure detected


@dataclass
class AnalysisResult:
    metadata: ImageMetadata
    extracted_text: str  # raw OCR output, may be empty
    vision: VisionResult


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert an image to a structured Markdown file using Tesseract OCR and OpenCV."
    )
    parser.add_argument("image", help="path to input image file")
    parser.add_argument("--output", help="path for output .md file")
    parser.add_argument("--lang", default="eng", help="Tesseract language code")
    return parser.parse_args()


def derive_output_path(image_path: Path, output_arg: str | None) -> Path:
    """Return the output .md path: explicit --output arg or stem-based default."""
    if output_arg:
        return Path(output_arg)
    return image_path.parent / (image_path.stem + ".md")


def check_dependencies():
    """Fail fast if required binaries or Python packages are missing."""
    if shutil.which("tesseract") is None:
        print(
            "Error: Tesseract not found. Install from https://github.com/tesseract-ocr/tesseract",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import pytesseract  # noqa: F401
    except ImportError:
        print(
            "Error: pytesseract not installed. Run: pip install pytesseract",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import cv2  # noqa: F401
    except ImportError:
        print(
            "Error: opencv-python not installed. Run: pip install opencv-python",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        import PIL  # noqa: F401
    except ImportError:
        print(
            "Error: Pillow not installed. Run: pip install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)


def validate_input(image_path: Path):
    if not image_path.exists():
        print(f"Error: File not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        ext = image_path.suffix.lower()
        print(
            f"Error: Unsupported file type '{ext}'. Supported: jpg, jpeg, png, gif, webp, tiff, tif, bmp",
            file=sys.stderr,
        )
        sys.exit(1)


def load_image(image_path: Path):
    """Open image with Pillow and return (PIL.Image, ImageMetadata)."""
    from PIL import Image

    image = Image.open(image_path)
    width, height = image.size
    metadata = ImageMetadata(
        filename=image_path.name,
        width=width,
        height=height,
        file_size=image_path.stat().st_size,
        lang="eng",  # default; caller may override after construction
    )
    return image, metadata


def run_ocr(image, lang: str) -> str:
    """Run Tesseract OCR on a PIL image and return the extracted text."""
    import pytesseract

    return pytesseract.image_to_string(image, lang=lang)


def run_vision(image_path: Path) -> VisionResult:
    """Analyze image visual structure using OpenCV and return a VisionResult."""
    import cv2
    import numpy as np
    import math

    img = cv2.imread(str(image_path))
    if img is None:
        return VisionResult(
            contour_count=0,
            dominant_shapes=[],
            line_count=0,
            line_orientations=[],
            region_count=0,
            region_positions=[],
            is_empty=True,
        )

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_count = len(contours)

    # Classify dominant shapes
    shape_counts: dict[str, int] = {}
    region_positions: list[str] = []
    h_img, w_img = img.shape[:2]
    area_threshold = 100

    for cnt in contours:
        area = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        if peri == 0:
            continue
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        vertices = len(approx)

        if vertices == 4:
            shape = "rectangle"
        else:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / h if h != 0 else 0
            if 0.85 <= aspect_ratio <= 1.15:
                # Check circularity
                circularity = (4 * math.pi * area) / (peri * peri) if peri > 0 else 0
                shape = "circle" if circularity > 0.7 else "polygon"
            else:
                shape = "polygon"

        shape_counts[shape] = shape_counts.get(shape, 0) + 1

        # Compute region positions for large contours
        if area > area_threshold:
            x, y, w, h = cv2.boundingRect(cnt)
            cx = x + w / 2
            cy = y + h / 2
            mid_x = w_img / 2
            mid_y = h_img / 2
            if cx < mid_x and cy < mid_y:
                pos = "top-left"
            elif cx >= mid_x and cy < mid_y:
                pos = "top-right"
            elif cx < mid_x and cy >= mid_y:
                pos = "bottom-left"
            elif cx >= mid_x and cy >= mid_y:
                pos = "bottom-right"
            else:
                pos = "center"
            # Use "center" for contours near the middle
            if abs(cx - mid_x) < w_img * 0.1 and abs(cy - mid_y) < h_img * 0.1:
                pos = "center"
            if pos not in region_positions:
                region_positions.append(pos)

    # Sort shapes by frequency, return top shapes
    dominant_shapes = [s for s, _ in sorted(shape_counts.items(), key=lambda x: -x[1])]

    # Detect lines with HoughLinesP
    lines = cv2.HoughLinesP(edges, 1, math.pi / 180, threshold=50, minLineLength=30, maxLineGap=10)
    line_count = 0
    orientation_set: set[str] = set()

    if lines is not None:
        line_count = len(lines)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            dx = x2 - x1
            dy = y2 - y1
            angle = abs(math.degrees(math.atan2(dy, dx))) % 180
            if angle < 20 or angle > 160:
                orientation_set.add("horizontal")
            elif 70 < angle < 110:
                orientation_set.add("vertical")
            else:
                orientation_set.add("diagonal")

    line_orientations = sorted(orientation_set)
    is_empty = contour_count == 0 and line_count == 0

    return VisionResult(
        contour_count=contour_count,
        dominant_shapes=dominant_shapes,
        line_count=line_count,
        line_orientations=line_orientations,
        region_count=len(region_positions),
        region_positions=region_positions,
        is_empty=is_empty,
    )
