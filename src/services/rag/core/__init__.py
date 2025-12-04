"""RAG core module exports."""

from .chunking import chunk_text
from .embeddings import get_service, embed_text, EmbeddingService
from .extraction import extract_text_from_bytes
from .indexing import index_filename, index_content, ensure_collection
from .search import (
    vector_search,
    search_content,
    search_filenames,
    rerank_results,
    reciprocal_rank_fusion,
    hybrid_search,
)

__all__ = [
    # Chunking
    "chunk_text",
    # Embeddings
    "get_service",
    "embed_text",
    "EmbeddingService",
    # Extraction
    "extract_text_from_bytes",
    # Indexing
    "index_filename",
    "index_content",
    "ensure_collection",
    # Search
    "vector_search",
    "search_content",
    "search_filenames",
    "rerank_results",
    "reciprocal_rank_fusion",
    "hybrid_search",
]
