"""RAG Server application factory."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from .routes import upload, search, health
from .core.indexing import ensure_collection
from .config import EMBED_COLLECTION_CONTENT, EMBED_COLLECTION_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rag-server")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events."""
    logger.info("Starting RAG Server...")
    # Initialize DB/Collections if needed
    yield
    logger.info("Shutting down RAG Server...")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="lotoAI RAG Server",
        version="0.3.0",
        lifespan=lifespan,
    )
    
    # Routes
    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(search.router)
    
    # Metrics
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    return app


app = create_app()
