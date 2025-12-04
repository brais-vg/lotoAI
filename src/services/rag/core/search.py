"""Search operations including vector search, reranking, and RRF."""

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient

from ..config import (
    QDRANT_URL,
    EMBED_COLLECTION_NAME,
    EMBED_COLLECTION_CONTENT,
    DEFAULT_SEARCH_LIMIT,
    DEFAULT_RERANK_TOP_K,
    RRF_K,
)
from .embeddings import embed_text

logger = logging.getLogger("rag-server.search")


def vector_search(
    query: str,
    collection: str = EMBED_COLLECTION_CONTENT,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search.
    
    Args:
        query: Search query text
        collection: Qdrant collection name
        limit: Max results to return
    
    Returns:
        List of results with score and payload.
    """
    try:
        client = QdrantClient(url=QDRANT_URL)
        query_vector = embed_text(query)
        
        results = client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
        )
        
        return [
            {
                "id": hit.payload.get("file_id", hit.id),
                "filename": hit.payload.get("filename"),
                "chunk": hit.payload.get("chunk", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "chunk_type": hit.payload.get("chunk_type", "unknown"),
                "score": hit.score,
                "created_at": hit.payload.get("created_at"),
                "content_type": hit.payload.get("content_type"),
                "size_bytes": hit.payload.get("size_bytes"),
            }
            for hit in results
        ]
    except Exception as exc:
        logger.warning(f"Vector search failed: {exc}")
        return []


def search_filenames(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search by filename similarity."""
    return vector_search(query, EMBED_COLLECTION_NAME, limit)


def search_content(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search by content similarity."""
    return vector_search(query, EMBED_COLLECTION_CONTENT, limit)


def rerank_results(
    query: str,
    results: List[Dict[str, Any]],
    top_k: int = DEFAULT_RERANK_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Rerank search results using cross-encoder model.
    
    Args:
        query: Original search query
        results: List of search results to rerank
        top_k: Number of top results to return
    
    Returns:
        Reranked results with updated scores.
    """
    if not results:
        return []
    
    try:
        from sentence_transformers import CrossEncoder
        
        reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Prepare pairs
        pairs = []
        for r in results:
            text = r.get("chunk") or r.get("filename") or ""
            pairs.append([query, text])
        
        # Get rerank scores
        scores = reranker.predict(pairs)
        
        # Add scores and sort
        for i, r in enumerate(results):
            r["rerank_score"] = float(scores[i])
            r["original_score"] = r.get("score", 0)
        
        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        return reranked[:top_k]
        
    except ImportError:
        logger.warning("CrossEncoder not available, skipping rerank")
        return results[:top_k]
    except Exception as exc:
        logger.warning(f"Reranking failed: {exc}")
        return results[:top_k]


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = RRF_K,
) -> List[Dict[str, Any]]:
    """
    Fuse multiple result lists using Reciprocal Rank Fusion.
    
    RRF score = sum(1 / (rank + k)) for each document across lists.
    
    Args:
        results_list: List of result lists to fuse
        k: RRF constant (default 60)
    
    Returns:
        Fused and sorted results.
    """
    fused_scores: Dict[int, float] = {}
    doc_data: Dict[int, Dict[str, Any]] = {}
    
    for results in results_list:
        for rank, doc in enumerate(results):
            doc_id = doc.get("id", 0)
            score = 1 / (rank + k)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0) + score
            
            # Keep the best scoring version of each doc
            if doc_id not in doc_data or doc.get("score", 0) > doc_data[doc_id].get("score", 0):
                doc_data[doc_id] = doc
    
    # Create final results
    final_results = []
    for doc_id, rrf_score in sorted(fused_scores.items(), key=lambda x: x[1], reverse=True):
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = rrf_score
        doc["score"] = rrf_score  # Use RRF as primary score
        final_results.append(doc)
    
    return final_results


def hybrid_search(
    query: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
    rerank: bool = True,
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search combining content and filename search.
    
    Args:
        query: Search query
        limit: Max results
        rerank: Whether to apply reranking
    
    Returns:
        Combined and deduplicated results.
    """
    # Search both collections
    content_results = search_content(query, limit * 2)
    filename_results = search_filenames(query, limit)
    
    # Mark filename matches
    filename_ids = {r["id"] for r in filename_results}
    for r in content_results:
        r["name_match"] = r["id"] in filename_ids
    
    # Fuse results
    fused = reciprocal_rank_fusion([content_results, filename_results])
    
    # Optionally rerank
    if rerank and fused:
        fused = rerank_results(query, fused, limit)
    
    return fused[:limit]
