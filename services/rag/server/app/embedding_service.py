"""
Embedding service abstraction layer for RAG server.
Supports both OpenAI API and local Sentence Transformers models.
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger("rag-server.embedding")


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """
        Generate embedding vector for given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """
        Get the dimensionality of embeddings produced by this service.
        
        Returns:
            Integer dimension of embedding vectors
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name/identifier of the embedding model.
        
        Returns:
            String identifier for the model
        """
        pass


class OpenAIEmbeddingService(EmbeddingService):
    """Embedding service using OpenAI API."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        Initialize OpenAI embedding service.
        
        Args:
            api_key: OpenAI API key
            model: Model name to use (default: text-embedding-3-small)
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed")
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self._dimension = self._detect_dimension()
        logger.info(f"Initialized OpenAI embedding service with model: {model}")

    def _detect_dimension(self) -> int:
        """Detect embedding dimension based on model name."""
        # Known OpenAI embedding model dimensions
        model_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        return model_dims.get(self.model, 1536)  # Default to 1536

    def embed(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API."""
        # Truncate to avoid context length issues
        text = text[:8000]
        
        result = self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return result.data[0].embedding  # type: ignore[attr-defined]

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_model_name(self) -> str:
        """Get model name."""
        return f"openai:{self.model}"


class LocalEmbeddingService(EmbeddingService):
    """Embedding service using local Sentence Transformers models."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize local embedding service.
        
        Args:
            model_name: Sentence Transformers model name
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise RuntimeError("sentence-transformers package not installed")
        
        logger.info(f"Loading local embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        self._dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Loaded model with dimension: {self._dimension}")

    def embed(self, text: str) -> List[float]:
        """Generate embedding using local model."""
        # Truncate to avoid memory issues
        text = text[:8000]
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self._dimension

    def get_model_name(self) -> str:
        """Get model name."""
        return f"local:{self.model_name}"


def get_embedding_service() -> EmbeddingService:
    """
    Factory function to create appropriate embedding service based on configuration.
    
    Environment variables:
        EMBEDDING_PROVIDER: "openai" or "local" (default: "openai")
        OPENAI_API_KEY: Required if provider is "openai"
        OPENAI_EMBED_MODEL: OpenAI model name (default: "text-embedding-3-small")
        LOCAL_EMBEDDING_MODEL: Local model name (default: "all-MiniLM-L6-v2")
    
    Returns:
        Configured EmbeddingService instance
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    
    if provider == "local":
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Using local embedding provider with model: {model_name}")
        return LocalEmbeddingService(model_name=model_name)
    
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable required for OpenAI embeddings"
            )
        model = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        logger.info(f"Using OpenAI embedding provider with model: {model}")
        return OpenAIEmbeddingService(api_key=api_key, model=model)
    
    else:
        raise ValueError(
            f"Unknown embedding provider: {provider}. Use 'openai' or 'local'"
        )
