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
