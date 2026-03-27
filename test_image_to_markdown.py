"""
Unit tests for validate_input and parse_args in image_to_markdown.py.
Requirements: 1.2, 1.3, 5.1, 5.3
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from image_to_markdown import validate_input, parse_args


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
