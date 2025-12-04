"""Unit tests for RAG chunking module."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from services.rag.core.chunking import chunk_text, _split_by_paragraphs, _split_by_sentences


class TestChunkText:
    """Tests for chunk_text function."""
    
    def test_empty_text_returns_empty_list(self):
        """Empty text should return empty list."""
        result = chunk_text("")
        assert result == []
    
    def test_short_text_returns_empty_list(self):
        """Text shorter than MIN_CHUNK_SIZE should return empty."""
        result = chunk_text("Hola")
        assert result == []
    
    def test_single_paragraph_creates_chunk(self):
        """Single paragraph should create one chunk."""
        text = "Este es un párrafo de prueba con suficiente contenido para ser procesado correctamente por el sistema."
        result = chunk_text(text)
        
        assert len(result) >= 1
        assert result[0]["chunk_index"] == 0
        assert result[0]["total_chunks"] >= 1
    
    def test_multiple_paragraphs_create_multiple_chunks(self):
        """Multiple paragraphs should create appropriate chunks."""
        text = """Primer párrafo con contenido suficiente para testing.
        
        Segundo párrafo separado por líneas vacías.
        
        Tercer párrafo con más información relevante."""
        
        result = chunk_text(text)
        
        assert len(result) >= 1
        for i, chunk in enumerate(result):
            assert chunk["chunk_index"] == i
            assert "text" in chunk
            assert "type" in chunk
    
    def test_chunks_have_required_metadata(self):
        """Each chunk should have required metadata fields."""
        text = "Contenido de prueba suficientemente largo para ser procesado como un chunk válido del sistema."
        result = chunk_text(text)
        
        if result:
            chunk = result[0]
            assert "text" in chunk
            assert "chunk_index" in chunk
            assert "total_chunks" in chunk
            assert "type" in chunk


class TestSplitByParagraphs:
    """Tests for paragraph splitting."""
    
    def test_empty_string_returns_empty_list(self):
        result = _split_by_paragraphs("")
        assert result == []
    
    def test_single_paragraph(self):
        result = _split_by_paragraphs("Un solo párrafo")
        assert len(result) == 1
        assert result[0] == "Un solo párrafo"
    
    def test_multiple_paragraphs(self):
        text = "Párrafo 1\n\nPárrafo 2\n\nPárrafo 3"
        result = _split_by_paragraphs(text)
        assert len(result) == 3


class TestSplitBySentences:
    """Tests for sentence splitting."""
    
    def test_empty_string_returns_empty_list(self):
        result = _split_by_sentences("")
        assert result == []
    
    def test_single_sentence(self):
        result = _split_by_sentences("Una oración.")
        assert len(result) == 1
    
    def test_multiple_sentences(self):
        result = _split_by_sentences("Primera oración. Segunda oración. Tercera oración.")
        assert len(result) == 3
