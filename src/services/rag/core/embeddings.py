"""Embedding service abstraction layer."""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

logger = logging.getLogger("rag-server.embeddings")


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Generate embedding vector for text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service implementation."""
    
    DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
            self._dimension = self.DIMENSIONS.get(model, 1536)
            logger.info(f"OpenAI embedding service initialized with model {model}")
        except ImportError:
            raise ImportError("openai package required for OpenAI embeddings")
    
    def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class SentenceTransformerEmbeddingService(EmbeddingService):
    """Local sentence-transformer embedding service."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self._dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"SentenceTransformer loaded: {model_name}")
        except ImportError:
            raise ImportError("sentence-transformers package required")
    
    def embed(self, text: str) -> List[float]:
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts).tolist()
    
    @property
    def dimension(self) -> int:
        return self._dimension


def get_embedding_service() -> Optional[EmbeddingService]:
    """
    Factory function to get the configured embedding service.
    
    Tries OpenAI first if API key is available, falls back to local model.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    
    if openai_key:
        try:
            return OpenAIEmbeddingService(openai_key, openai_model)
        except Exception as exc:
            logger.warning(f"Failed to init OpenAI embeddings: {exc}")
    
    # Fallback to local model
    try:
        return SentenceTransformerEmbeddingService()
    except Exception as exc:
        logger.warning(f"Failed to init local embeddings: {exc}")
    
    logger.error("No embedding service available")
    return None


# Global instance (lazy initialized)
_embedding_service: Optional[EmbeddingService] = None


def get_service() -> Optional[EmbeddingService]:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = get_embedding_service()
    return _embedding_service


def embed_text(text: str) -> List[float]:
    """Convenience function to embed text using the global service."""
    service = get_service()
    if service is None:
        raise RuntimeError("No embedding service available")
    return service.embed(text)
