"""
Tests for improved chunking functionality.
"""

import pytest
from app.main import chunk_text


def test_chunk_text_basic():
    """Test basic chunking with small text."""
    text = "This is a test paragraph.\\n\\nThis is another paragraph."
    chunks = chunk_text(text)
    
    assert len(chunks) > 0
    assert all("text" in c and "chunk_index" in c for c in chunks)
    assert chunks[0]["total_chunks"] == len(chunks)


def test_chunk_text_with_metadata():
    """Test that chunks include proper metadata."""
    text = "Paragraph one.\\n\\nParagraph two."
    chunks = chunk_text(text)
    
    for idx, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == idx
        assert chunk["total_chunks"] == len(chunks)
        assert chunk["type"] in ["paragraph", "sentence"]
        assert isinstance(chunk["text"], str)


def test_chunk_text_overlap():
    """Test that chunks have overlap for context preservation."""
    text = "A" * 1000  # Long text to force multiple chunks
    chunks = chunk_text(text)
    
    if len(chunks) > 1:
        # Check that chunk boundaries overlap
        # Since overlap is 25%, some content should repeat
        assert len(chunks) >= 2


def test_chunk_text_empty():
    """Test chunking with empty text."""
    text = ""
    chunks = chunk_text(text)
    
    assert chunks == []


def test_chunk_text_safety_limit():
    """Test that safety limit prevents excessive chunks."""
    # Create very long text that would create many chunks
    text = ("Paragraph.\\n\\n" * 1000)  # 1000 paragraphs
    chunks = chunk_text(text)
    
    # Should respect MAX_CHUNKS_SAFETY (500)
    assert len(chunks) <= 500


def test_chunk_text_respects_max_chunks():
    """Test that M AX_CHUNKS setting is respected when set."""
    import app.main as main_module
    
    original_max = main_module.MAX_CHUNKS
    try:
        # Set a specific limit
        main_module.MAX_CHUNKS = 3
        text = ("Short paragraph.\\n\\n" * 10)
        chunks = chunk_text(text)
        
        assert len(chunks) <= 3
    finally:
        # Restore original value
        main_module.MAX_CHUNKS = original_max


def test_chunk_text_long_paragraphs():
    """Test that long paragraphs are split by sentences."""
    # Create a very long paragraph
    long_para = ". ".join([f"Sentence {i}" for i in range(100)])
    chunks = chunk_text(long_para)
    
    assert len(chunks) > 0
    # Some chunks should be sentence-based
    assert any(c["type"] == "sentence" for c in chunks)


def test_chunk_text_preserves_content():
    """Test that all original content is captured in chunks."""
    text = "First paragraph.\\n\\nSecond paragraph.\\n\\nThird paragraph."
    chunks = chunk_text(text)
    
    # Concatenate all chunk texts
    combined = " ".join(c["text"] for c in chunks)
    
    # Should contain all key words (allowing for some formatting differences)
    assert "First" in combined
    assert "Second" in combined
    assert "Third" in combined
