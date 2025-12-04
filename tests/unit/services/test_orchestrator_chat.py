"""Unit tests for orchestrator chat history module."""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from services.orchestrator.core.chat_history import (
    ChatMessage,
    ChatHistoryManager,
)


class TestChatMessage:
    """Tests for ChatMessage dataclass."""
    
    def test_creation_with_defaults(self):
        msg = ChatMessage(role="user", message="Hola")
        assert msg.role == "user"
        assert msg.message == "Hola"
        assert msg.timestamp is not None
    
    def test_to_dict(self):
        msg = ChatMessage(role="bot", message="Respuesta")
        result = msg.to_dict()
        
        assert result["role"] == "bot"
        assert result["message"] == "Respuesta"
        assert "timestamp" in result
    
    def test_to_openai_format_user(self):
        msg = ChatMessage(role="user", message="Pregunta")
        result = msg.to_openai_format()
        
        assert result["role"] == "user"
        assert result["content"] == "Pregunta"
    
    def test_to_openai_format_bot(self):
        msg = ChatMessage(role="bot", message="Respuesta")
        result = msg.to_openai_format()
        
        # Bot should be converted to assistant
        assert result["role"] == "assistant"
        assert result["content"] == "Respuesta"


class TestChatHistoryManager:
    """Tests for ChatHistoryManager class."""
    
    @pytest.fixture
    def manager(self):
        """Create a fresh history manager for each test."""
        return ChatHistoryManager(max_messages=10)
    
    def test_add_message(self, manager):
        msg = manager.add_message("session1", "user", "Hola")
        
        assert msg.role == "user"
        assert msg.message == "Hola"
    
    def test_get_history_empty(self, manager):
        result = manager.get_history("nonexistent")
        assert result == []
    
    def test_get_history_after_add(self, manager):
        manager.add_message("session1", "user", "Mensaje 1")
        manager.add_message("session1", "bot", "Respuesta 1")
        
        result = manager.get_history("session1")
        
        assert len(result) == 2
    
    def test_history_isolation_between_sessions(self, manager):
        manager.add_message("session1", "user", "Mensaje session 1")
        manager.add_message("session2", "user", "Mensaje session 2")
        
        history1 = manager.get_history("session1")
        history2 = manager.get_history("session2")
        
        assert len(history1) == 1
        assert len(history2) == 1
        assert history1[0].message != history2[0].message
    
    def test_clear_history(self, manager):
        manager.add_message("session1", "user", "Mensaje")
        manager.clear_history("session1")
        
        result = manager.get_history("session1")
        assert result == []
    
    def test_max_messages_eviction(self, manager):
        # Add more messages than max
        for i in range(15):
            manager.add_message("session1", "user", f"Mensaje {i}")
        
        result = manager.get_history("session1", limit=100)
        
        # Should only keep max_messages (10)
        assert len(result) <= 10
    
    def test_get_context_messages(self, manager):
        manager.add_message("session1", "user", "Pregunta 1")
        manager.add_message("session1", "bot", "Respuesta 1")
        manager.add_message("session1", "user", "Pregunta 2")
        manager.add_message("session1", "bot", "Respuesta 2")
        
        result = manager.get_context_messages("session1", num_messages=2)
        
        # Should return last 4 messages (2 pairs) in OpenAI format
        assert len(result) == 4
        assert all("role" in msg and "content" in msg for msg in result)
    
    def test_get_all_sessions(self, manager):
        manager.add_message("session1", "user", "Msg")
        manager.add_message("session2", "user", "Msg")
        manager.add_message("session3", "user", "Msg")
        
        sessions = manager.get_all_sessions()
        
        assert "session1" in sessions
        assert "session2" in sessions
        assert "session3" in sessions
