"""Tests for context building and RAG integration improvements."""
import pytest
from app.main import build_context_message, build_conversation_history


class TestContextBuilding:
    """Test suite for context message building with score filtering."""
    
    def test_empty_sources(self):
        """Should return empty string for no sources."""
        result = build_context_message([])
        assert result == ""
    
    def test_filter_low_score_sources(self):
        """Should filter out sources below minimum score."""
        sources = [
            {"filename": "doc1.pdf", "chunk": "Content 1", "score": 0.8},
            {"filename": "doc2.pdf", "chunk": "Content 2", "score": 0.2},  # Below 0.3
            {"filename": "doc3.pdf", "chunk": "Content 3", "score": 0.5},
        ]
        result = build_context_message(sources)
        
        # Should only include doc1 and doc3
        assert "doc1.pdf" in result
        assert "doc3.pdf" in result
        assert "doc2.pdf" not in result
    
    def test_all_sources_below_threshold(self):
        """Should return empty string if all sources below threshold."""
        sources = [
            {"filename": "doc1.pdf", "chunk": "Content 1", "score": 0.1},
            {"filename": "doc2.pdf", "chunk": "Content 2", "score": 0.2},
        ]
        result = build_context_message(sources)
        assert result == ""
    
    def test_context_includes_metadata(self):
        """Should include chunk metadata in context."""
        sources = [
            {
                "filename": "test.pdf",
                "chunk": "Test content",
                "score": 0.9,
                "chunk_index": 2,
                "total_chunks": 10,
                "chunk_type": "paragraph"
            }
        ]
        result = build_context_message(sources)
        
        assert "test.pdf" in result
        assert "relevancia: 0.90" in result
        assert "fragmento 3/10" in result  # chunk_index is 0-based
        assert "tipo: paragraph" in result
        assert "Test content" in result
    
    def test_context_truncates_long_chunks(self):
        """Should truncate chunks to RAG_CONTEXT_CHARS."""
        long_text = "A" * 2000
        sources = [
            {"filename": "doc.pdf", "chunk": long_text, "score": 0.8}
        ]
        result = build_context_message(sources)
        
        # Should be truncated to 1000 chars (default RAG_CONTEXT_CHARS)
        # Plus the header and metadata
        assert len(result) < len(long_text) + 200


class TestConversationHistory:
    """Test suite for conversation history building."""
    
    def test_empty_history(self):
        """Should return empty string for no history."""
        result = build_conversation_history([])
        assert result == ""
    
    def test_max_messages_zero(self):
        """Should return empty string if max_messages is 0."""
        history = [
            {"role": "user", "message": "Hello"},
            {"role": "bot", "message": "Hi there"}
        ]
        result = build_conversation_history(history, max_messages=0)
        assert result == ""
    
    def test_formats_user_and_bot_messages(self):
        """Should format user and bot messages correctly."""
        history = [
            {"role": "user", "message": "What is AI?"},
            {"role": "bot", "message": "AI is artificial intelligence."}
        ]
        result = build_conversation_history(history, max_messages=5)
        
        assert "Usuario: What is AI?" in result
        assert "Asistente: AI is artificial intelligence." in result
    
    def test_limits_to_max_messages(self):
        """Should only include last N messages."""
        history = [
            {"role": "user", "message": "Message 1"},
            {"role": "bot", "message": "Response 1"},
            {"role": "user", "message": "Message 2"},
            {"role": "bot", "message": "Response 2"},
            {"role": "user", "message": "Message 3"},
            {"role": "bot", "message": "Response 3"},
        ]
        result = build_conversation_history(history, max_messages=2)
        
        # Should only include last 2 messages
        assert "Message 1" not in result
        assert "Response 1" not in result
        assert "Message 2" not in result
        assert "Response 2" not in result
        assert "Message 3" in result
        assert "Response 3" in result
    
    def test_includes_conversation_header(self):
        """Should include conversation header."""
        history = [
            {"role": "user", "message": "Hello"}
        ]
        result = build_conversation_history(history, max_messages=5)
        
        assert "Conversación reciente:" in result


class TestIntegration:
    """Integration tests for the improved chat flow."""
    
    def test_context_and_history_together(self):
        """Should be able to build both context and history."""
        sources = [
            {"filename": "doc.pdf", "chunk": "Important info", "score": 0.9}
        ]
        history = [
            {"role": "user", "message": "Previous question"},
            {"role": "bot", "message": "Previous answer"}
        ]
        
        context = build_context_message(sources)
        conv_history = build_conversation_history(history, max_messages=5)
        
        assert context != ""
        assert conv_history != ""
        assert "doc.pdf" in context
        assert "Previous question" in conv_history
