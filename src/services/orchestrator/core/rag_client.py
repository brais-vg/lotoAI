"""RAG client for fetching context from RAG server."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from ..config import RAG_SERVER_URL, RAG_MIN_SCORE, RAG_CONTEXT_CHARS

logger = logging.getLogger("orchestrator.rag_client")


async def fetch_rag_context(query: str) -> List[Dict[str, Any]]:
    """
    Fetch relevant context from RAG server.
    
    Args:
        query: User's question/query
    
    Returns:
        List of relevant documents/chunks, empty list if none found.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Try advanced search first
            response = await client.post(
                f"{RAG_SERVER_URL}/search/advanced",
                json={"text": query, "limit": 5, "num_variants": 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                # Filter by minimum score
                filtered = [
                    r for r in results 
                    if r.get("score", 0) >= RAG_MIN_SCORE
                ]
                
                logger.info(f"RAG returned {len(filtered)}/{len(results)} results (min_score={RAG_MIN_SCORE})")
                return filtered
            else:
                logger.warning(f"RAG search failed with status {response.status_code}")
                
    except Exception as exc:
        logger.warning(f"RAG context fetch failed: {exc}")
    
    return []


def format_context(results: List[Dict[str, Any]]) -> str:
    """
    Format RAG results into context string for the LLM.
    
    Args:
        results: List of RAG search results
    
    Returns:
        Formatted context string with citations.
    """
    if not results:
        return ""
    
    context_parts = []
    
    for i, r in enumerate(results, 1):
        filename = r.get("filename", "documento")
        chunk = r.get("chunk", "")[:RAG_CONTEXT_CHARS]
        score = r.get("score", 0)
        
        # Build citation
        part = f"[{i}] {filename} (relevancia: {score:.2f}):\n{chunk}"
        context_parts.append(part)
    
    return "\n\n".join(context_parts)


def get_source_citations(results: List[Dict[str, Any]]) -> str:
    """
    Build source citations string for response.
    
    Args:
        results: List of RAG search results
    
    Returns:
        Formatted citations string.
    """
    if not results:
        return ""
    
    citations = []
    seen = set()
    
    for i, r in enumerate(results, 1):
        filename = r.get("filename", "documento")
        if filename not in seen:
            citations.append(f"[{i}] {filename}")
            seen.add(filename)
    
    return "Fuentes: " + ", ".join(citations)
