"""Pydantic models for RAG API."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    """Response model for file upload."""
    id: int
    filename: str
    stored_path: str
    size_bytes: int
    content_type: Optional[str]
    created_at: str
    indexing: Optional[Dict[str, Any]] = None


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    text: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)
    rerank: bool = Field(default=True)


class AdvancedSearchRequest(BaseModel):
    """Request model for advanced search with query variants."""
    text: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)
    num_variants: int = Field(default=3, ge=1, le=5)


class SearchResult(BaseModel):
    """Single search result."""
    id: int
    filename: str
    chunk: Optional[str] = None
    chunk_index: int = 0
    chunk_type: str = "unknown"
    score: float
    created_at: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    name_match: bool = False
    rerank_score: Optional[float] = None
    original_score: Optional[float] = None
    rrf_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Response model for search endpoints."""
    query: str
    results: List[SearchResult]


class UploadListItem(BaseModel):
    """Item in upload list response."""
    id: int
    filename: str
    size_bytes: int
    content_type: Optional[str]
    created_at: str


class UploadListResponse(BaseModel):
    """Response model for list uploads endpoint."""
    items: List[UploadListItem]
    total: int
    limit: int
    offset: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = "ok"
    service: str = "rag-server"
    version: str = "0.3.0"
