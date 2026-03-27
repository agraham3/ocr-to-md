# Requirements Document

## Introduction

A Python script that accepts an image file as input, extracts text from it using Tesseract OCR (via pytesseract) locally, and analyzes its visual structure using OpenCV (cv2) locally. It produces a structured Markdown (.md) file combining both analyses: extracted text from Tesseract and visual/structural analysis (shapes, contours, lines, regions) from OpenCV. The output is designed to be consumed by an AI agent as part of a task list, so the Markdown must be well-structured and actionable. All processing runs entirely on the user's machine — no network calls, no external APIs, and no API key is required.

## Glossary

- **Script**: The Python command-line program (`image_to_markdown.py`) that orchestrates the workflow.
- **Image**: An input file in a supported raster format (JPEG, PNG, GIF, WEBP, TIFF, BMP) provided by the user.
- **Tesseract**: The open-source OCR engine (https://github.com/tesseract-ocr/tesseract) used to extract text from images.
- **pytesseract**: The Python wrapper library for Tesseract used by the Script.
- **OpenCV**: The open-source computer vision library (`cv2`) used by the Script to analyze the visual structure of the Image.
- **Visual_Analysis**: The structural description produced by OpenCV, including detected shapes, contours, lines, and bounding regions.
- **Extracted_Text**: The raw text output produced by Tesseract from the Image.
- **Markdown_File**: The `.md` output file containing the structured content derived from the Image, combining Extracted_Text and Visual_Analysis.
- **AI_Agent**: The downstream consumer of the Markdown_File that uses it as part of a task list.

## Requirements

### Requirement 1: Accept Image Input

**User Story:** As a developer, I want to provide an image file path via the command line, so that the Script can process any image I choose.

#### Acceptance Criteria

1. THE Script SHALL accept an image file path as a required command-line argument.
2. WHEN a file path is provided that does not exist, THE Script SHALL exit with a non-zero status code and print a descriptive error message to stderr.
3. WHEN a file path is provided whose extension is not one of `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.tiff`, `.tif`, or `.bmp`, THE Script SHALL exit with a non-zero status code and print a descriptive error message to stderr.
4. WHERE an output file path is specified via an optional `--output` argument, THE Script SHALL write the Markdown_File to that path instead of the default path.
5. WHEN no `--output` argument is provided, THE Script SHALL derive the output path by replacing the image file's extension with `.md` in the same directory.

### Requirement 2: Extract Text with Tesseract OCR

**User Story:** As a developer, I want the Script to use Tesseract OCR locally to extract text from the image, so that all processing happens on my machine without any network calls or API keys.

#### Acceptance Criteria

1. WHEN a valid Image is provided, THE Script SHALL use pytesseract to invoke Tesseract and extract text from the Image.
2. THE Script SHALL NOT make any network calls or require any API key or authentication credentials.
3. WHEN Tesseract is not installed or not found on the system PATH, THE Script SHALL exit with a non-zero status code and print a descriptive error message to stderr that instructs the user to install Tesseract.
4. WHEN pytesseract is not installed, THE Script SHALL exit with a non-zero status code and print a descriptive error message to stderr that instructs the user to install it via `pip install pytesseract`.
5. WHEN Tesseract produces no Extracted_Text from the Image (e.g., the image contains no readable text), THE Script SHALL still generate a valid Markdown_File with an empty `## Extracted Text` section and a note indicating no text was detected.
6. WHERE a language is specified via an optional `--lang` argument, THE Script SHALL pass that language code to Tesseract; otherwise THE Script SHALL default to `eng`.

### Requirement 3: Generate Structured Markdown Output

**User Story:** As an AI agent, I want the Markdown file to be well-structured, so that I can parse and use it effectively in my task list.

#### Acceptance Criteria

1. THE Markdown_File SHALL contain a top-level heading (`# Image: <filename>`) using the image's filename.
2. THE Markdown_File SHALL contain a `## Summary` section with a one-sentence description stating the image filename, dimensions, and whether text was detected.
3. THE Markdown_File SHALL contain an `## Extracted Text` section containing the Extracted_Text verbatim, or a note that no text was detected if Extracted_Text is empty.
4. THE Markdown_File SHALL contain a `## Visual Structure` section containing the Visual_Analysis produced by OpenCV, or a note that no significant visual structure was detected if Visual_Analysis is empty.
5. THE Markdown_File SHALL contain a `## Metadata` section listing the image filename, file size in bytes, image dimensions in pixels, and the Tesseract language used.
6. WHEN the Markdown_File is written, THE Script SHALL use UTF-8 encoding.

### Requirement 4: Analyze Visual Structure with OpenCV

**User Story:** As a developer, I want the Script to use OpenCV locally to analyze the visual structure of the image, so that diagrams, flowcharts, and wireframes are described even when they contain little or no text.

#### Acceptance Criteria

1. WHEN a valid Image is provided, THE Script SHALL use OpenCV (cv2) to analyze the Image and produce a Visual_Analysis describing detected contours, shapes, lines, and bounding regions.
2. THE Script SHALL NOT make any network calls during visual analysis.
3. WHEN opencv-python is not installed, THE Script SHALL exit with a non-zero status code and print a descriptive error message to stderr that instructs the user to install it via `pip install opencv-python`.
4. WHEN OpenCV detects one or more contours in the Image, THE Script SHALL include in the Visual_Analysis the total count of detected contours and a description of the dominant shapes (e.g., rectangles, circles, lines).
5. WHEN OpenCV detects straight lines via Hough line detection, THE Script SHALL include in the Visual_Analysis the count of detected lines and their approximate orientations (horizontal, vertical, diagonal).
6. WHEN OpenCV detects bounding regions that suggest distinct visual blocks (e.g., boxes in a flowchart or wireframe panels), THE Script SHALL include in the Visual_Analysis the count and approximate positions of those regions.
7. WHEN OpenCV produces no significant Visual_Analysis from the Image (e.g., a blank or uniform-color image), THE Script SHALL still generate a valid Markdown_File with an empty `## Visual Structure` section and a note indicating no significant visual structure was detected.
8. WHEN the Image contains no Extracted_Text but OpenCV detects visual structure, THE Script SHALL populate the `## Visual Structure` section with the Visual_Analysis and leave the `## Extracted Text` section with a note that no text was detected.
9. WHEN the Image contains Extracted_Text but OpenCV detects minimal visual structure, THE Script SHALL populate the `## Extracted Text` section with the Extracted_Text and leave the `## Visual Structure` section with a note that no significant visual structure was detected.

### Requirement 5: Command-Line Usability

**User Story:** As a developer, I want a clear and helpful CLI interface, so that I can integrate the Script into automated pipelines.

#### Acceptance Criteria

1. THE Script SHALL provide a `--help` flag that prints usage instructions and exits with status code 0.
2. WHEN the Script completes successfully, THE Script SHALL print the output file path to stdout.
3. THE Script SHALL support a `--lang` optional argument to specify the Tesseract language code, defaulting to `eng`.

### Requirement 6: Round-Trip Consistency

**User Story:** As a developer, I want the output Markdown to be parseable and stable, so that downstream tools can rely on its structure.

#### Acceptance Criteria

1. FOR ALL valid Images processed by the Script, THE Markdown_File SHALL be valid Markdown that can be parsed by a standard Markdown parser without errors.
2. WHEN the same Image is processed twice with identical arguments, THE Markdown_File SHALL contain identical content in both outputs.
