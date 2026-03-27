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
