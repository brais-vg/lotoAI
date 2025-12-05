"""
Tests for reranking functionality in RAG server.
"""

import pytest
from unittest.mock import Mock, patch
from app.main import rerank_results


@pytest.mark.asyncio
async def test_rerank_results_with_reranker():
    """Test reranking with a mocked cross-encoder."""
    query = "test query"
    results = [
        {"id": 1, "filename": "doc1.txt", "chunk": "first document", "score": 0.8},
        {"id": 2, "filename": "doc2.txt", "chunk": "second document", "score": 0.7},
        {"id": 3, "filename": "doc3.txt", "chunk": "third document", "score": 0.6},
    ]
    
    # Mock the reranker to return scores in reverse order
    with patch("app.main.reranker") as mock_reranker:
        mock_reranker.predict.return_value = [0.5, 0.9, 0.7]  # Rerank scores
        
        reranked = rerank_results(query, results, top_k=2)
        
        # Check that results are reordered by rerank_score
        assert len(reranked) == 2
        assert reranked[0]["id"] == 2  # Highest rerank score (0.9)
        assert reranked[1]["id"] == 3  # Second highest (0.7)
        assert "rerank_score" in reranked[0]
        assert "original_score" in reranked[0]


@pytest.mark.asyncio
async def test_rerank_results_without_reranker():
    """Test reranking when reranker is not available."""
    query = "test query"
    results = [
        {"id": 1, "filename": "doc1.txt", "score": 0.8},
        {"id": 2, "filename": "doc2.txt", "score": 0.7},
    ]
    
    with patch("app.main.reranker", None):
        reranked = rerank_results(query, results, top_k=5)
        
        # Should return original results limited to top_k
        assert len(reranked) == 2
        assert reranked == results


@pytest.mark.asyncio
async def test_rerank_results_empty_list():
    """Test reranking with empty results."""
    query = "test query"
    results = []
    
    with patch("app.main.reranker") as mock_reranker:
        reranked = rerank_results(query, results, top_k=10)
        
        assert reranked == []
        mock_reranker.predict.assert_not_called()


@pytest.mark.asyncio
async def test_rerank_uses_chunk_or_filename():
    """Test that reranking uses chunk if available, otherwise filename."""
    query = "test query"
    results = [
        {"id": 1, "filename": "doc1.txt", "chunk": "content here"},
        {"id": 2, "filename": "doc2.txt"},  # No chunk
    ]
    
    with patch("app.main.reranker") as mock_reranker:
        mock_reranker.predict.return_value = [0.8, 0.6]
        
        rerank_results(query, results, top_k=2)
        
        # Check that predict was called with correct pairs
        calls = mock_reranker.predict.call_args[0][0]
        assert calls[0] == [query, "content here"]  # Uses chunk
        assert calls[1] == [query, "doc2.txt"]  # Falls back to filename


@pytest.mark.asyncio
async def test_rerank_error_handling():
    """Test that errors in reranking return original results."""
    query = "test query"
    results = [{"id": 1, "filename": "doc1.txt", "score": 0.8}]
    
    with patch("app.main.reranker") as mock_reranker:
        mock_reranker.predict.side_effect = Exception("Reranker error")
        
        reranked = rerank_results(query, results, top_k=10)
        
        # Should return original results on error
        assert len(reranked) == 1
        assert reranked[0]["id"] == 1
