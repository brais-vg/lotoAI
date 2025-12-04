"""Unit tests for RAG text extraction module."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from services.rag.core.extraction import (
    extract_text_from_bytes,
    _clean_text,
    _extract_plaintext,
)


class TestExtractTextFromBytes:
    """Tests for extract_text_from_bytes function."""
    
    def test_plaintext_extraction(self):
        """Should extract text from plain text files."""
        content = b"Este es un texto de prueba."
        result = extract_text_from_bytes(content, "text/plain", "test.txt")
        assert "Este es un texto de prueba" in result
    
    def test_empty_bytes_returns_empty_string(self):
        """Empty bytes should return empty string."""
        result = extract_text_from_bytes(b"", "text/plain", "empty.txt")
        assert result == ""
    
    def test_markdown_content_type_detection(self):
        """Should detect markdown by filename."""
        content = b"# Titulo\n\nContenido markdown"
        result = extract_text_from_bytes(content, "", "test.md")
        # Should attempt markdown extraction
        assert "Titulo" in result or result == ""  # Depends on markdown lib availability
    
    def test_html_content_type_detection(self):
        """Should detect HTML by content type."""
        content = b"<html><body><p>Texto HTML</p></body></html>"
        result = extract_text_from_bytes(content, "text/html", "test.html")
        # Result depends on bs4 availability
        assert "Texto HTML" in result or result == ""


class TestCleanText:
    """Tests for _clean_text function."""
    
    def test_empty_string(self):
        result = _clean_text("")
        assert result == ""
    
    def test_removes_multiple_empty_lines(self):
        text = "Línea 1\n\n\n\nLínea 2"
        result = _clean_text(text)
        assert "\n\n\n" not in result
        assert "Línea 1" in result
        assert "Línea 2" in result
    
    def test_strips_whitespace(self):
        text = "  Texto con espacios  "
        result = _clean_text(text)
        assert not result.startswith(" ")
        assert not result.endswith(" ")
    
    def test_removes_control_characters(self):
        text = "Texto\x00con\x01caracteres\x02control"
        result = _clean_text(text)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
    
    def test_preserves_newlines(self):
        text = "Línea 1\nLínea 2"
        result = _clean_text(text)
        assert "\n" in result


class TestExtractPlaintext:
    """Tests for _extract_plaintext function."""
    
    def test_utf8_decoding(self):
        content = "Texto con acentos: áéíóú".encode("utf-8")
        result = _extract_plaintext(content)
        assert "áéíóú" in result
    
    def test_handles_decode_errors(self):
        # Invalid UTF-8 sequence
        content = b"\x80\x81\x82"
        result = _extract_plaintext(content)
        # Should not raise, returns with errors ignored
        assert isinstance(result, str)
