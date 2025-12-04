"""RAG Server configuration module."""

import os
from pathlib import Path

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lotoai")

# Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
EMBED_COLLECTION_NAME = "uploads"
EMBED_COLLECTION_CONTENT = "uploads-content"

# Embedding
ENABLE_CONTENT_EMBED = os.getenv("ENABLE_CONTENT_EMBED", "1") == "1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# File storage
UPLOAD_DIR = Path(os.getenv("RAG_UPLOAD_DIR", "/app/data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Chunking
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
MIN_CHUNK_SIZE = 50

# Search
DEFAULT_SEARCH_LIMIT = 10
DEFAULT_RERANK_TOP_K = 5
RRF_K = 60
