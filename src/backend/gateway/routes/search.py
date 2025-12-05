"""Search routes proxy."""

import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter
from pydantic import BaseModel
from prometheus_client import Counter

from ..config import RAG_SERVER_URL

logger = logging.getLogger("gateway.routes.search")
router = APIRouter(tags=["search"])

SEARCH_COUNTER = Counter("lotoai_gateway_search_total", "Busquedas proxied", ["status"])


class SearchRequest(BaseModel):
    text: str


@router.post("/api/search")
async def search(req: SearchRequest) -> Dict[str, Any]:
    """Proxy de busquedas al RAG."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{RAG_SERVER_URL}/search", json=req.model_dump())
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error buscando en RAG: %s", exc)
        SEARCH_COUNTER.labels(status="error").inc()
        return {"query": req.text, "results": []}
    SEARCH_COUNTER.labels(status="ok").inc()
    return resp.json()


@router.post("/api/search/advanced")
async def search_advanced(req: SearchRequest) -> Dict[str, Any]:
    """Proxy de búsqueda avanzada al RAG."""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{RAG_SERVER_URL}/search/advanced", json=req.model_dump())
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error en búsqueda avanzada RAG: %s", exc)
        SEARCH_COUNTER.labels(status="error").inc()
        return {"query": req.text, "results": [], "mode": "error"}
    SEARCH_COUNTER.labels(status="ok").inc()
    return resp.json()
