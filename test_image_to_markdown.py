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
