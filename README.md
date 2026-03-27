# ocr-to-md

Converts an image to a structured Markdown file using Tesseract OCR and OpenCV. Useful for feeding image content to AI tools that work with text.

## What it does

Given an image, it produces a `.md` file with five sections:

- **Summary** — filename, dimensions, and whether text was detected
- **Extracted Text** — raw OCR output via Tesseract
- **Visual Structure** — contour/shape/line analysis via OpenCV
- **Metadata** — file size, dimensions, language used

## Requirements

### Tesseract binary

Install Tesseract and make sure it's on your `PATH`:

- Windows: download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki), then add `C:\Program Files\Tesseract-OCR` to PATH
- macOS: `brew install tesseract`
- Linux: `sudo apt-get install -y tesseract-ocr`

Verify with: `tesseract --version`

For extra language packs (e.g. French):
- macOS: `brew install tesseract-lang`
- Linux: `sudo apt-get install -y tesseract-ocr-fra`

### Python dependencies

```bash
pip install -r requirements.txt
```

## Usage

```bash
python image_to_markdown.py <image> [--output <path>] [--lang <code>]
```

- `image` — path to the input image (jpg, jpeg, png, gif, webp, tiff, bmp)
- `--output` — optional output `.md` path (defaults to `<image_stem>.md` in the same directory)
- `--lang` — Tesseract language code (default: `eng`)

### Examples

```bash
# Basic usage — outputs screenshot.md
python image_to_markdown.py screenshot.png

# Custom output path
python image_to_markdown.py diagram.jpg --output docs/diagram.md

# French OCR
python image_to_markdown.py document.png --lang fra
```

## Running tests

```bash
pytest test_image_to_markdown.py
```
