"""Chat history management."""

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from threading import Lock

from ..config import CHAT_HISTORY_LENGTH

logger = logging.getLogger("orchestrator.chat_history")


@dataclass
class ChatMessage:
    """Single chat message."""
    role: str  # "user" or "bot"
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }
    
    def to_openai_format(self) -> dict:
        """Convert to OpenAI message format."""
        role = "assistant" if self.role == "bot" else self.role
        return {"role": role, "content": self.message}


class ChatHistoryManager:
    """
    Thread-safe in-memory chat history manager.
    
    Uses session IDs to separate conversations.
    Implements LRU eviction when history exceeds limit.
    """
    
    def __init__(self, max_messages: int = CHAT_HISTORY_LENGTH * 2):
        self._history: Dict[str, List[ChatMessage]] = defaultdict(list)
        self._lock = Lock()
        self._max_messages = max_messages
    
    def add_message(
        self,
        session_id: str,
        role: str,
        message: str,
    ) -> ChatMessage:
        """
        Add a message to the session history.
        
        Args:
            session_id: Session identifier
            role: Message role ("user" or "bot")
            message: Message content
        
        Returns:
            The created ChatMessage.
        """
        msg = ChatMessage(role=role, message=message)
        
        with self._lock:
            self._history[session_id].append(msg)
            
            # Evict old messages if limit exceeded
            if len(self._history[session_id]) > self._max_messages:
                self._history[session_id] = self._history[session_id][-self._max_messages:]
        
        return msg
    
    def get_history(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ChatMessage]:
        """
        Get chat history for a session.
        
        Args:
            session_id: Session identifier
            limit: Max messages to return
            offset: Number of messages to skip
        
        Returns:
            List of ChatMessage objects.
        """
        with self._lock:
            messages = self._history.get(session_id, [])
            return list(reversed(messages[offset:offset + limit]))
    
    def get_context_messages(
        self,
        session_id: str,
        num_messages: int = CHAT_HISTORY_LENGTH,
    ) -> List[dict]:
        """
        Get recent messages in OpenAI format for context.
        
        Args:
            session_id: Session identifier
            num_messages: Number of recent message pairs to include
        
        Returns:
            List of message dicts in OpenAI format.
        """
        with self._lock:
            messages = self._history.get(session_id, [])
            recent = messages[-(num_messages * 2):]  # Pairs of user/bot
            return [m.to_openai_format() for m in recent]
    
    def clear_history(self, session_id: str) -> None:
        """Clear all history for a session."""
        with self._lock:
            self._history[session_id] = []
    
    def get_all_sessions(self) -> List[str]:
        """Get all active session IDs."""
        with self._lock:
            return list(self._history.keys())


# Global instance
_history_manager: Optional[ChatHistoryManager] = None


def get_history_manager() -> ChatHistoryManager:
    """Get or create the global history manager."""
    global _history_manager
    if _history_manager is None:
        _history_manager = ChatHistoryManager()
    return _history_manager
