"""
Tests for embedding service abstraction.
"""

import pytest
from unittest.mock import Mock, patch
from app.embedding_service import (
    OpenAIEmbeddingService,
    LocalEmbeddingService,
    get_embedding_service,
)


def test_openai_embedding_service_init():
    """Test OpenAI embedding service initialization."""
    with patch("app.embedding_service.OpenAI") as mock_openai:
        service = OpenAIEmbeddingService(api_key="test-key", model="text-embedding-3-small")
        
        assert service.get_model_name() == "openai:text-embedding-3-small"
        assert service.get_dimension() == 1536


def test_openai_embedding_service_embed():
    """Test OpenAI embedding generation."""
    with patch("app.embedding_service.OpenAI") as mock_openai_class:
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock the embeddings response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_client.embeddings.create.return_value = mock_response
        
        service = OpenAIEmbeddingService(api_key="test-key")
        embedding = service.embed("test text")
        
        assert embedding == [0.1, 0.2, 0.3]
        mock_client.embeddings.create.assert_called_once()


def test_local_embedding_service_init():
    """Test local embedding service initialization."""
    with patch("app.embedding_service.SentenceTransformer") as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        service = LocalEmbeddingService(model_name="all-MiniLM-L6-v2")
        
        assert service.get_model_name() == "local:all-MiniLM-L6-v2"
        assert service.get_dimension() == 384


def test_local_embedding_service_embed():
    """Test local embedding generation."""
    with patch("app.embedding_service.SentenceTransformer") as mock_st:
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_model.encode.return_value = Mock(tolist=lambda: [0.4, 0.5, 0.6])
        mock_st.return_value = mock_model
        
        service = LocalEmbeddingService()
        embedding = service.embed("test text")
        
        assert embedding == [0.4, 0.5, 0.6]


def test_get_embedding_service_openai():
    """Test factory returns OpenAI service when configured."""
    with patch("app.embedding_service.os.getenv") as mock_getenv, \
         patch("app.embedding_service.OpenAI"):
        
        def getenv_side_effect(key, default=None):
            if key == "EMBEDDING_PROVIDER":
                return "openai"
            elif key == "OPENAI_API_KEY":
                return "test-key"
            elif key == "OPENAI_EMBED_MODEL":
                return "text-embedding-3-small"
            return default
        
        mock_getenv.side_effect = getenv_side_effect
        
        service = get_embedding_service()
        
        assert isinstance(service, OpenAIEmbeddingService)


def test_get_embedding_service_local():
    """Test factory returns local service when configured."""
    with patch("app.embedding_service.os.getenv") as mock_getenv, \
         patch("app.embedding_service.SentenceTransformer") as mock_st:
        
        mock_model = Mock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_st.return_value = mock_model
        
        def getenv_side_effect(key, default=None):
            if key == "EMBEDDING_PROVIDER":
                return "local"
            elif key == "LOCAL_EMBEDDING_MODEL":
                return "all-MiniLM-L6-v2"
            return default
        
        mock_getenv.side_effect = getenv_side_effect
        
        service = get_embedding_service()
        
        assert isinstance(service, LocalEmbeddingService)


def test_get_embedding_service_invalid_provider():
    """Test factory raises error for invalid provider."""
    with patch("app.embedding_service.os.getenv") as mock_getenv:
        mock_getenv.return_value = "invalid"
        
        with pytest.raises(ValueError, match="Unknown embedding provider"):
            get_embedding_service()


def test_different_dimensions():
    """Test that different models report correct dimensions."""
    test_cases = [
        ("text-embedding-3-small", 1536),
        ("text-embedding-3-large", 3072),
        ("text-embedding-ada-002", 1536),
    ]
    
    with patch("app.embedding_service.OpenAI"):
        for model, expected_dim in test_cases:
            service = OpenAIEmbeddingService(api_key="test", model=model)
            assert service.get_dimension() == expected_dim
