"""Indexing operations for Qdrant vector store."""

import logging
from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from ..config import (
    QDRANT_URL,
    EMBED_COLLECTION_NAME,
    EMBED_COLLECTION_CONTENT,
)
from .embeddings import get_service, embed_text
from .chunking import chunk_text
from .extraction import extract_text_from_bytes

logger = logging.getLogger("rag-server.indexing")


def ensure_collection(
    client: QdrantClient, 
    name: str, 
    vector_size: Optional[int] = None
) -> None:
    """Ensure Qdrant collection exists with appropriate vector size."""
    collections = client.get_collections().collections
    exists = any(c.name == name for c in collections)
    
    if not exists:
        service = get_service()
        size = vector_size or (service.dimension if service else 1536)
        
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=size, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection '{name}' with size {size}")


def index_filename(payload: Dict[str, Any]) -> bool:
    """
    Index upload by filename in Qdrant.
    
    Args:
        payload: Dict with 'id', 'filename', 'stored_path', etc.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_collection(client, EMBED_COLLECTION_NAME)
        
        vector = embed_text(payload.get("filename", ""))
        
        point = PointStruct(
            id=payload["id"],
            vector=vector,
            payload={
                "filename": payload.get("filename"),
                "path": payload.get("stored_path"),
                "size_bytes": payload.get("size_bytes"),
                "content_type": payload.get("content_type"),
                "created_at": payload.get("created_at"),
            },
        )
        
        client.upsert(collection_name=EMBED_COLLECTION_NAME, points=[point])
        logger.info(f"Indexed filename for file_id={payload['id']}")
        return True
        
    except Exception as exc:
        logger.warning(f"Failed to index filename: {exc}")
        return False


def index_content(
    payload: Dict[str, Any], 
    data: bytes, 
    content_type: str
) -> Dict[str, Any]:
    """
    Index document content chunks in Qdrant.
    
    Args:
        payload: Dict with file metadata
        data: Raw file bytes
        content_type: MIME type
    
    Returns:
        Dict with indexing status: success, chunks_indexed, error
    """
    result = {"success": False, "chunks_indexed": 0, "error": None}
    
    service = get_service()
    if not service:
        result["error"] = "No embedding service available"
        return result
    
    filename = payload.get("filename", "unknown")
    file_id = payload.get("id", 0)
    
    # Extract text
    text = extract_text_from_bytes(data, content_type, filename)
    
    # Validate content
    if not text or len(text.strip()) < 10:
        logger.warning(
            f"Empty or insufficient content from file_id={file_id} ({filename}). "
            f"Text length: {len(text) if text else 0}"
        )
        result["error"] = f"No searchable content extracted from {filename}"
        return result
    
    logger.info(f"Extracted {len(text)} chars from {filename}")
    
    # Chunk text
    chunks = chunk_text(text)
    if not chunks:
        result["error"] = f"No chunks generated from {filename}"
        return result
    
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_collection(client, EMBED_COLLECTION_CONTENT)
        
        points = []
        for chunk_data in chunks:
            chunk_text_str = chunk_data["text"]
            vector = embed_text(chunk_text_str)
            
            point = PointStruct(
                id=file_id * 1000 + chunk_data["chunk_index"],
                vector=vector,
                payload={
                    "file_id": file_id,
                    "filename": filename,
                    "path": payload.get("stored_path"),
                    "size_bytes": payload.get("size_bytes"),
                    "content_type": payload.get("content_type"),
                    "created_at": payload.get("created_at"),
                    "chunk": chunk_text_str[:300],
                    "chunk_index": chunk_data["chunk_index"],
                    "total_chunks": chunk_data["total_chunks"],
                    "chunk_type": chunk_data["type"],
                },
            )
            points.append(point)
        
        client.upsert(collection_name=EMBED_COLLECTION_CONTENT, points=points)
        logger.info(f"Indexed {len(points)} chunks for file_id={file_id}")
        
        result["success"] = True
        result["chunks_indexed"] = len(points)
        return result
        
    except Exception as exc:
        logger.warning(f"Failed to index content: {exc}")
        result["error"] = str(exc)
        return result
