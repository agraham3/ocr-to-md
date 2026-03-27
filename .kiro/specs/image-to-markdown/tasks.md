# Implementation Plan: image-to-markdown

## Overview

Implement `image_to_markdown.py` as a single-file Python CLI script that runs Tesseract OCR and OpenCV analysis on an input image and writes a structured Markdown file. Tests live in `test_image_to_markdown.py`.

## Tasks

- [x] 1. Set up project dependencies
  - Create `requirements.txt` listing `pytesseract`, `opencv-python`, `Pillow`, `hypothesis`, and `pytest`
  - Add a comment block at the top of `image_to_markdown.py` with install instructions for the Tesseract binary
  - _Requirements: 2.1, 2.3, 2.4, 4.3_

- [x] 2. Define data models and constants
  - [x] 2.1 Implement `ImageMetadata`, `VisionResult`, and `AnalysisResult` dataclasses
    - Use `@dataclass` with the fields specified in the design
    - Define `SUPPORTED_EXTENSIONS` set: `{".jpg", ".jpeg", ".png", ".gif", ".webp", ".tiff", ".tif", ".bmp"}`
    - _Requirements: 1.3, 3.5_

- [x] 3. Implement CLI and input validation
  - [x] 3.1 Implement `parse_args()`
    - Use `argparse` with positional `image`, optional `--output`, optional `--lang` (default `"eng"`)
    - _Requirements: 1.1, 1.4, 5.1, 5.3_

  - [x] 3.2 Implement `validate_input(image_path: Path)`
    - Exit 1 + stderr if file does not exist
    - Exit 1 + stderr if extension not in `SUPPORTED_EXTENSIONS`
    - _Requirements: 1.2, 1.3_

  - [x] 3.3 Write unit tests for `validate_input` and `parse_args`
    - `test_validate_input_missing_file`: non-existent path → exit 1 + stderr message
    - `test_validate_input_bad_extension`: `.pdf`, `.docx` → exit 1 + stderr message
    - `test_help_flag`: `--help` → exit 0, usage in stdout
    - `test_lang_default`: no `--lang` → `args.lang == "eng"`
    - `test_lang_override`: `--lang fra` → `args.lang == "fra"`
    - _Requirements: 1.2, 1.3, 5.1, 5.3_

  - [x] 3.4 Write property test for invalid path rejection (Property 1)
    - **Property 1: Invalid path rejection**
    - **Validates: Requirements 1.2**
    - Use `@given(st.text(min_size=1).filter(lambda s: not Path(s).exists()))` to generate non-existent paths and assert exit code is non-zero with non-empty stderr

  - [x] 3.5 Write property test for invalid extension rejection (Property 2)
    - **Property 2: Invalid extension rejection**
    - **Validates: Requirements 1.3**
    - Generate extensions not in `SUPPORTED_EXTENSIONS`, create a temp file with that extension, assert exit code is non-zero with non-empty stderr

- [x] 4. Implement `derive_output_path()` and `check_dependencies()`
  - [x] 4.1 Implement `derive_output_path(image_path: Path, output_arg: str | None) -> Path`
    - Return `Path(output_arg)` if provided, else `image_path.parent / (image_path.stem + ".md")`
    - _Requirements: 1.4, 1.5_

  - [x] 4.2 Implement `check_dependencies()`
    - Check `shutil.which("tesseract")` → exit 1 + stderr if None
    - Try importing `pytesseract`, `cv2`, `PIL` → exit 1 + stderr with pip install hint for each
    - _Requirements: 2.3, 2.4, 4.3_

  - [x] 4.3 Write unit tests for `derive_output_path` and `check_dependencies`
    - `test_derive_output_path`: several concrete filenames verify stem-based naming
    - `test_dependency_check_missing_tesseract`: mock `shutil.which` → None, assert exit 1
    - `test_dependency_check_missing_pytesseract`: mock import failure, assert exit 1
    - `test_dependency_check_missing_cv2`: mock import failure, assert exit 1
    - _Requirements: 1.5, 2.3, 2.4, 4.3_

  - [x] 4.4 Write property test for output path derivation (Property 3)
    - **Property 3: Output path derives from input filename stem**
    - **Validates: Requirements 1.5**
    - Use `@given(st.from_regex(r'[a-zA-Z0-9_\-]+', fullmatch=True), st.sampled_from(list(SUPPORTED_EXTENSIONS)))` and assert `derive_output_path(Path(stem+ext), None).stem == stem`

- [x] 5. Implement `load_image()` and `run_ocr()`
  - [x] 5.1 Implement `load_image(image_path: Path) -> tuple[PIL.Image.Image, ImageMetadata]`
    - Open with `PIL.Image.open()`, extract `width`, `height`, `file_size`, `filename`
    - _Requirements: 2.1_

  - [x] 5.2 Implement `run_ocr(image: PIL.Image.Image, lang: str) -> str`
    - Call `pytesseract.image_to_string(image, lang=lang)` and return the result
    - _Requirements: 2.1, 2.2, 2.5, 2.6_

  - [x] 5.3 Write unit tests for `load_image` and `run_ocr`
    - `test_run_ocr_with_text_image`: small synthetic PIL image with known text → non-empty result
    - `test_run_ocr_blank_image`: blank white image → empty string
    - _Requirements: 2.1, 2.5_

- [x] 6. Implement `run_vision()`
  - [x] 6.1 Implement `run_vision(image_path: Path) -> VisionResult`
    - Load with `cv2.imread()`, convert to grayscale, Gaussian blur, Canny edges
    - Find contours with `cv2.findContours()`, classify shapes via `cv2.approxPolyDP` and aspect ratio
    - Detect lines with `cv2.HoughLinesP()`, classify as horizontal / vertical / diagonal
    - Compute bounding boxes for large contours as region positions
    - Set `is_empty=True` when no significant structure detected
    - _Requirements: 4.1, 4.2, 4.4, 4.5, 4.6, 4.7_

  - [x] 6.2 Write unit tests for `run_vision`
    - `test_run_vision_with_shapes`: synthetic image with drawn rectangles → `contour_count > 0`
    - `test_run_vision_blank_image`: blank white image → `VisionResult.is_empty == True`
    - _Requirements: 4.4, 4.7_

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement `build_markdown()` and `write_output()`
  - [x] 8.1 Implement `build_markdown(result: AnalysisResult) -> str`
    - Assemble all five sections in order: `# Image:`, `## Summary`, `## Extracted Text`, `## Visual Structure`, `## Metadata`
    - Use `"_No text was detected in this image._"` when OCR is empty/whitespace
    - Use `"_No significant visual structure was detected._"` when `vision.is_empty`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 8.2 Implement `write_output(markdown: str, output_path: Path)`
    - Write with `encoding="utf-8"`, print resolved path to stdout
    - Exit 1 + stderr on `OSError`
    - _Requirements: 3.6, 5.2_

  - [x] 8.3 Write unit tests for `build_markdown` and `write_output`
    - `test_build_markdown_all_sections`: all five headings present
    - `test_build_markdown_no_text`: "no text was detected" note present
    - `test_build_markdown_no_vision`: "no significant visual structure" note present
    - `test_stdout_output_path`: stdout contains the output path on success
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.2_

  - [x] 8.4 Write property test for required sections (Property 4)
    - **Property 4: Output markdown contains all required sections**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**
    - Use `image_strategy()` (small synthetic PIL images) and assert all five section headings appear in order

  - [x] 8.5 Write property test for UTF-8 output (Property 5)
    - **Property 5: Output file is valid UTF-8**
    - **Validates: Requirements 3.6**
    - Use `image_strategy()`, write output, read bytes back and assert `bytes.decode("utf-8")` does not raise

  - [x] 8.6 Write property test for valid Markdown output (Property 8)
    - **Property 8: Output is valid Markdown**
    - **Validates: Requirements 6.1**
    - Use `image_strategy()`, parse the output with `markdown-it-py` or `mistune` and assert no parse error

  - [x] 8.7 Write property test for deterministic output (Property 9)
    - **Property 9: Deterministic output (idempotence)**
    - **Validates: Requirements 6.2**
    - Use `image_strategy()`, run the pipeline twice with identical args, assert byte-for-byte identical output

- [x] 9. Implement `main()` and wire everything together
  - [x] 9.1 Implement `main()`
    - Call `check_dependencies()`, `parse_args()`, `validate_input()`, `derive_output_path()`, `load_image()`, `run_ocr()`, `run_vision()`, build `AnalysisResult`, `build_markdown()`, `write_output()`
    - _Requirements: 1.1, 2.1, 4.1, 5.2_

  - [x] 9.2 Write property test for stdout output path (Property 7)
    - **Property 7: Successful run prints output path to stdout**
    - **Validates: Requirements 5.2**
    - Use `image_strategy()`, invoke `main()` via subprocess or captured stdout, assert output path appears in stdout

  - [x] 9.3 Write property test for visual analysis content (Property 6)
    - **Property 6: Visual analysis content reflects detected features**
    - **Validates: Requirements 4.4, 4.5, 4.6**
    - Use `image_with_shapes_strategy()` (images with drawn rectangles/circles), assert `## Visual Structure` contains a numeric count

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- `image_strategy()` generates small (64×64 px) synthetic PIL images saved to a temp file
- `image_with_shapes_strategy()` generates images with programmatically drawn shapes to guarantee detectable contours
- Each property test requires `@settings(max_examples=100)`
- All property tests must include a comment: `# Feature: image-to-markdown, Property N: <title>`
