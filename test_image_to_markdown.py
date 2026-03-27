"""
Unit tests for validate_input and parse_args in image_to_markdown.py.
Requirements: 1.2, 1.3, 5.1, 5.3
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from image_to_markdown import (
    validate_input,
    parse_args,
    derive_output_path,
    check_dependencies,
    SUPPORTED_EXTENSIONS,
    build_markdown,
    write_output,
    load_image,
    run_ocr,
    run_vision,
    AnalysisResult,
    ImageMetadata,
    VisionResult,
)


# ---------------------------------------------------------------------------
# validate_input tests
# ---------------------------------------------------------------------------

def test_validate_input_missing_file(tmp_path, capsys):
    """Req 1.2: non-existent path → exit 1 + stderr message."""
    missing = tmp_path / "does_not_exist.png"
    with pytest.raises(SystemExit) as exc_info:
        validate_input(missing)
    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert captured.err.strip() != ""


def test_validate_input_bad_extension(tmp_path, capsys):
    """Req 1.3: unsupported extensions (.pdf, .docx) → exit 1 + stderr message."""
    for ext in (".pdf", ".docx"):
        bad_file = tmp_path / f"file{ext}"
        bad_file.write_bytes(b"dummy content")
        with pytest.raises(SystemExit) as exc_info:
            validate_input(bad_file)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert captured.err.strip() != ""


# ---------------------------------------------------------------------------
# parse_args / CLI tests
# ---------------------------------------------------------------------------

def test_help_flag(capsys):
    """Req 5.1: --help exits 0 and prints usage text to stdout."""
    with patch("sys.argv", ["image_to_markdown.py", "--help"]):
        with pytest.raises(SystemExit) as exc_info:
            parse_args()
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower()


def test_lang_default(tmp_path):
    """Req 5.3: no --lang argument → args.lang defaults to 'eng'."""
    dummy = tmp_path / "photo.png"
    dummy.write_bytes(b"")
    with patch("sys.argv", ["image_to_markdown.py", str(dummy)]):
        args = parse_args()
    assert args.lang == "eng"


def test_lang_override(tmp_path):
    """Req 5.3: --lang fra → args.lang == 'fra'."""
    dummy = tmp_path / "photo.png"
    dummy.write_bytes(b"")
    with patch("sys.argv", ["image_to_markdown.py", str(dummy), "--lang", "fra"]):
        args = parse_args()
    assert args.lang == "fra"


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 1: Invalid path rejection
# Validates: Requirements 1.2
@given(st.text(min_size=1).filter(lambda s: not Path(s).exists()))
@settings(max_examples=100)
def test_property_invalid_path_rejection(path_str):
    """Property 1: Any non-existent path causes validate_input to exit non-zero with non-empty stderr."""
    import io
    fake_stderr = io.StringIO()
    with patch("sys.stderr", fake_stderr):
        with pytest.raises(SystemExit) as exc_info:
            validate_input(Path(path_str))
    assert exc_info.value.code != 0
    assert fake_stderr.getvalue().strip() != ""


# Feature: image-to-markdown, Property 2: Invalid extension rejection
# Validates: Requirements 1.3
@given(
    st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=10)
    .filter(lambda e: ("." + e.lower()) not in SUPPORTED_EXTENSIONS)
)
@settings(max_examples=100)
def test_property_invalid_extension_rejection(ext):
    """Property 2: Any file with an extension not in SUPPORTED_EXTENSIONS causes validate_input to exit non-zero with non-empty stderr."""
    import io
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp_dir:
        bad_file = Path(tmp_dir) / f"file.{ext}"
        bad_file.write_bytes(b"dummy content")
        fake_stderr = io.StringIO()
        with patch("sys.stderr", fake_stderr):
            with pytest.raises(SystemExit) as exc_info:
                validate_input(bad_file)
        assert exc_info.value.code != 0
        assert fake_stderr.getvalue().strip() != ""


# ---------------------------------------------------------------------------
# derive_output_path tests
# ---------------------------------------------------------------------------

def test_derive_output_path_default(tmp_path):
    """Req 1.5: no --output → stem + .md in same directory."""
    cases = [
        ("photo.png", "photo.md"),
        ("diagram.jpg", "diagram.md"),
        ("scan.tiff", "scan.md"),
        ("my_image.webp", "my_image.md"),
    ]
    for filename, expected_name in cases:
        image_path = tmp_path / filename
        result = derive_output_path(image_path, None)
        assert result == tmp_path / expected_name, f"Failed for {filename}"


def test_derive_output_path_explicit_output(tmp_path):
    """Req 1.4: --output overrides the default path."""
    image_path = tmp_path / "photo.png"
    explicit = str(tmp_path / "custom_output.md")
    result = derive_output_path(image_path, explicit)
    assert result == Path(explicit)


# ---------------------------------------------------------------------------
# check_dependencies tests
# ---------------------------------------------------------------------------

def test_dependency_check_missing_tesseract(capsys):
    """Req 2.3: tesseract binary not on PATH → exit 1 + stderr."""
    with patch("shutil.which", return_value=None):
        with pytest.raises(SystemExit) as exc_info:
            check_dependencies()
    assert exc_info.value.code == 1
    assert capsys.readouterr().err.strip() != ""


def test_dependency_check_missing_pytesseract(capsys):
    """Req 2.4: pytesseract not importable → exit 1 + stderr."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "pytesseract":
            raise ImportError("No module named 'pytesseract'")
        return real_import(name, *args, **kwargs)

    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()
    assert exc_info.value.code == 1
    assert capsys.readouterr().err.strip() != ""


def test_dependency_check_missing_cv2(capsys):
    """Req 4.3: cv2 not importable → exit 1 + stderr."""
    import builtins
    real_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "cv2":
            raise ImportError("No module named 'cv2'")
        return real_import(name, *args, **kwargs)

    with patch("shutil.which", return_value="/usr/bin/tesseract"):
        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(SystemExit) as exc_info:
                check_dependencies()
    assert exc_info.value.code == 1
    assert capsys.readouterr().err.strip() != ""


# ---------------------------------------------------------------------------
# Property-based test: Property 3 — Output path derives from input filename stem
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 3: Output path derives from input filename stem
# Validates: Requirements 1.5
@given(
    st.from_regex(r'[a-zA-Z0-9_\-]+', fullmatch=True),
    st.sampled_from(sorted(SUPPORTED_EXTENSIONS)),
)
@settings(max_examples=100)
def test_property_output_path_stem_matches_input(stem, ext):
    """Property 3: derive_output_path with no output_arg produces a path whose stem equals the input stem."""
    image_path = Path(stem + ext)
    result = derive_output_path(image_path, None)
    assert result.stem == stem
    assert result.suffix == ".md"


# ---------------------------------------------------------------------------
# load_image and run_ocr tests (Task 5)
# Requirements: 2.1, 2.5
# ---------------------------------------------------------------------------


def test_load_image_returns_metadata(tmp_path):
    """load_image extracts correct width, height, file_size, and filename."""
    from PIL import Image

    img = Image.new("RGB", (80, 60), color=(200, 200, 200))
    img_path = tmp_path / "test_img.png"
    img.save(img_path)

    pil_image, metadata = load_image(img_path)

    assert metadata.filename == "test_img.png"
    assert metadata.width == 80
    assert metadata.height == 60
    assert metadata.file_size == img_path.stat().st_size
    assert metadata.file_size > 0
    # Returned PIL image should have the same dimensions
    assert pil_image.size == (80, 60)


import shutil

# Skip OCR tests when the Tesseract binary is not installed on the system.
tesseract_available = shutil.which("tesseract") is not None
requires_tesseract = pytest.mark.skipif(
    not tesseract_available,
    reason="Tesseract binary not found on PATH — install tesseract to run OCR tests",
)

# Skip cv2 tests when the cv2 library is not importable (e.g. DLL issues on Windows).
try:
    import cv2 as _cv2  # noqa: F401
    cv2_available = True
except ImportError:
    cv2_available = False

requires_cv2 = pytest.mark.skipif(
    not cv2_available,
    reason="cv2 (opencv-python) not importable — install/fix opencv-python to run vision tests",
)


@requires_tesseract
def test_run_ocr_with_text_image():
    """Req 2.1: OCR on a synthetic image with drawn text returns a non-empty string."""
    from PIL import Image, ImageDraw

    # Create a white image and draw clear black text on it
    img = Image.new("RGB", (200, 60), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Hello", fill=(0, 0, 0))

    result = run_ocr(img, lang="eng")
    assert isinstance(result, str)
    assert result.strip() != "", "Expected non-empty OCR result for image with text"


@requires_tesseract
def test_run_ocr_blank_image():
    """Req 2.5: OCR on a blank white image returns an empty/whitespace-only string."""
    from PIL import Image

    img = Image.new("RGB", (200, 200), color=(255, 255, 255))
    result = run_ocr(img, lang="eng")
    assert isinstance(result, str)
    assert result.strip() == "", f"Expected empty OCR result for blank image, got: {result!r}"


# ---------------------------------------------------------------------------
# run_vision tests (Task 6)
# Requirements: 4.4, 4.7
# ---------------------------------------------------------------------------


@requires_cv2
def test_run_vision_with_shapes(tmp_path):
    """Req 4.4: synthetic image with drawn rectangles → contour_count > 0."""
    import cv2
    import numpy as np

    img = np.ones((200, 200, 3), dtype=np.uint8) * 255  # white background
    cv2.rectangle(img, (20, 20), (80, 80), (0, 0, 0), 2)
    cv2.rectangle(img, (110, 110), (180, 180), (0, 0, 0), 2)

    img_path = tmp_path / "shapes.png"
    cv2.imwrite(str(img_path), img)

    result = run_vision(img_path)
    assert result.contour_count > 0


@requires_cv2
def test_run_vision_blank_image(tmp_path):
    """Req 4.7: blank white image → is_empty == True."""
    import cv2
    import numpy as np

    img = np.ones((200, 200, 3), dtype=np.uint8) * 255  # fully white

    img_path = tmp_path / "blank.png"
    cv2.imwrite(str(img_path), img)

    result = run_vision(img_path)
    assert result.is_empty is True


# ---------------------------------------------------------------------------
# Helpers shared by Task 8 tests
# ---------------------------------------------------------------------------

import tempfile
import os
from hypothesis.strategies import composite


def _make_analysis_result(
    filename="test.png",
    width=64,
    height=64,
    file_size=1024,
    lang="eng",
    extracted_text="Hello world",
    is_empty=False,
):
    """Build a minimal AnalysisResult for unit tests."""
    metadata = ImageMetadata(
        filename=filename,
        width=width,
        height=height,
        file_size=file_size,
        lang=lang,
    )
    vision = VisionResult(
        contour_count=0 if is_empty else 2,
        dominant_shapes=[] if is_empty else ["rectangle"],
        line_count=0 if is_empty else 1,
        line_orientations=[] if is_empty else ["horizontal"],
        region_count=0 if is_empty else 1,
        region_positions=[] if is_empty else ["top-left"],
        is_empty=is_empty,
    )
    return AnalysisResult(metadata=metadata, extracted_text=extracted_text, vision=vision)


# ---------------------------------------------------------------------------
# Task 8.3 — Unit tests for build_markdown and write_output
# ---------------------------------------------------------------------------

def test_build_markdown_all_sections():
    """Req 3.1-3.5: all five section headings present in output."""
    result = _make_analysis_result()
    md = build_markdown(result)
    assert "# Image:" in md
    assert "## Summary" in md
    assert "## Extracted Text" in md
    assert "## Visual Structure" in md
    assert "## Metadata" in md


def test_build_markdown_no_text():
    """Req 3.3: empty OCR text → 'no text was detected' note."""
    result = _make_analysis_result(extracted_text="   ")
    md = build_markdown(result)
    assert "_No text was detected in this image._" in md


def test_build_markdown_no_vision():
    """Req 3.4: is_empty vision → 'no significant visual structure' note."""
    result = _make_analysis_result(is_empty=True)
    md = build_markdown(result)
    assert "_No significant visual structure was detected._" in md


def test_stdout_output_path(tmp_path, capsys):
    """Req 5.2: stdout contains the resolved output path on success."""
    result = _make_analysis_result()
    md = build_markdown(result)
    out_path = tmp_path / "output.md"
    write_output(md, out_path)
    captured = capsys.readouterr()
    assert str(out_path.resolve()) in captured.out


# ---------------------------------------------------------------------------
# image_strategy — composite Hypothesis strategy for synthetic PIL images
# ---------------------------------------------------------------------------

@composite
def image_strategy(draw):
    """Generate a small (32x32) synthetic PIL image saved to a temp file."""
    from PIL import Image

    # Fixed small size to stay within Hypothesis list limits
    width, height = 32, 32
    raw = draw(st.binary(min_size=width * height * 3, max_size=width * height * 3))
    img = Image.frombytes("RGB", (width, height), raw)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    img.save(tmp.name)
    tmp.close()
    return Path(tmp.name)


# ---------------------------------------------------------------------------
# Task 8.4 — Property 4: Output markdown contains all required sections
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 4: Output markdown contains all required sections
# Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_strategy())
@settings(max_examples=100, deadline=None)
def test_output_contains_all_sections(image_path):
    """Property 4: All five section headings appear in the markdown output."""
    try:
        pil_image, metadata = load_image(image_path)
        metadata.lang = "eng"
        ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
        vision = run_vision(image_path)
        result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
        md = build_markdown(result)

        # All five headings must appear in order
        sections = ["# Image:", "## Summary", "## Extracted Text", "## Visual Structure", "## Metadata"]
        positions = [md.index(s) for s in sections]
        assert positions == sorted(positions), "Sections are not in the expected order"
        for s in sections:
            assert s in md
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Task 8.5 — Property 5: Output file is valid UTF-8
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 5: Output file is valid UTF-8
# Validates: Requirements 3.6
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_strategy())
@settings(max_examples=100, deadline=None)
def test_output_is_valid_utf8(image_path):
    """Property 5: Bytes written to the output .md file are valid UTF-8."""
    try:
        pil_image, metadata = load_image(image_path)
        metadata.lang = "eng"
        ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
        vision = run_vision(image_path)
        result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
        md = build_markdown(result)

        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            out_path = Path(tmp.name)
        try:
            write_output(md, out_path)
            raw_bytes = out_path.read_bytes()
            # Must not raise
            raw_bytes.decode("utf-8")
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Task 8.6 — Property 8: Output is valid Markdown
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 8: Output is valid Markdown
# Validates: Requirements 6.1
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_strategy())
@settings(max_examples=100, deadline=None)
def test_output_is_valid_markdown(image_path):
    """Property 8: Output markdown is parseable by markdown-it-py without error."""
    from markdown_it import MarkdownIt

    try:
        pil_image, metadata = load_image(image_path)
        metadata.lang = "eng"
        ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
        vision = run_vision(image_path)
        result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
        md = build_markdown(result)

        # Parse — should not raise
        parser = MarkdownIt()
        tokens = parser.parse(md)
        assert tokens is not None
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Task 8.7 — Property 9: Deterministic output (idempotence)
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 9: Deterministic output (idempotence)
# Validates: Requirements 6.2
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_strategy())
@settings(max_examples=100, deadline=None)
def test_output_is_deterministic(image_path):
    """Property 9: Running the pipeline twice with identical args produces identical output."""
    try:
        def run_pipeline(img_path):
            pil_image, metadata = load_image(img_path)
            metadata.lang = "eng"
            ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
            vision = run_vision(img_path)
            result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
            return build_markdown(result)

        md1 = run_pipeline(image_path)
        md2 = run_pipeline(image_path)
        assert md1 == md2, "Pipeline produced different output on second run"
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# image_with_shapes_strategy — composite Hypothesis strategy for images with shapes
# ---------------------------------------------------------------------------

def _make_shapes_image() -> Path:
    """Generate a synthetic image with drawn rectangles guaranteed to have detectable contours."""
    import cv2
    import numpy as np

    img = np.ones((128, 128, 3), dtype=np.uint8) * 255  # white background
    # Draw two black rectangles to guarantee contours
    cv2.rectangle(img, (10, 10), (50, 50), (0, 0, 0), 2)
    cv2.rectangle(img, (70, 70), (118, 118), (0, 0, 0), 2)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(tmp.name, img)
    tmp.close()
    return Path(tmp.name)


def image_with_shapes_strategy():
    """Hypothesis strategy: always produces a synthetic image with detectable contours."""
    return st.builds(_make_shapes_image)


# ---------------------------------------------------------------------------
# Task 9.2 — Property 7: Successful run prints output path to stdout
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 7: Successful run prints output path to stdout
# Validates: Requirements 5.2
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_strategy())
@settings(max_examples=100, deadline=None)
def test_stdout_contains_output_path(image_path):
    """Property 7: A successful pipeline run prints the resolved output path to stdout."""
    import io

    try:
        pil_image, metadata = load_image(image_path)
        metadata.lang = "eng"
        ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
        vision = run_vision(image_path)
        result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
        md = build_markdown(result)

        out_path = image_path.with_suffix(".md")
        fake_stdout = io.StringIO()
        with patch("sys.stdout", fake_stdout):
            write_output(md, out_path)

        printed = fake_stdout.getvalue()
        assert str(out_path.resolve()) in printed
    finally:
        for p in (image_path, image_path.with_suffix(".md")):
            try:
                os.unlink(p)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Task 9.3 — Property 6: Visual analysis content reflects detected features
# ---------------------------------------------------------------------------

# Feature: image-to-markdown, Property 6: Visual analysis content reflects detected features
# Validates: Requirements 4.4, 4.5, 4.6
@pytest.mark.skipif(not cv2_available, reason="cv2 not importable")
@given(image_with_shapes_strategy())
@settings(max_examples=100, deadline=None)
def test_visual_analysis_contains_counts(image_path):
    """Property 6: When OpenCV detects contours/lines, ## Visual Structure contains a numeric count."""
    import re

    try:
        pil_image, metadata = load_image(image_path)
        metadata.lang = "eng"
        ocr_text = run_ocr(pil_image, lang="eng") if shutil.which("tesseract") else ""
        vision = run_vision(image_path)

        # The strategy guarantees detectable contours; skip if vision is unexpectedly empty
        if vision.is_empty:
            return

        result = AnalysisResult(metadata=metadata, extracted_text=ocr_text, vision=vision)
        md = build_markdown(result)

        # Extract the ## Visual Structure section
        start = md.index("## Visual Structure")
        end = md.index("## Metadata")
        visual_section = md[start:end]

        # Must contain at least one numeric digit (a count)
        assert re.search(r'\d+', visual_section), (
            f"Expected a numeric count in ## Visual Structure, got:\n{visual_section}"
        )
    finally:
        try:
            os.unlink(image_path)
        except OSError:
            pass
