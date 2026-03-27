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
