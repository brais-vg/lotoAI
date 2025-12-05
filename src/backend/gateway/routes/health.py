"""Health check routes."""

from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@router.get("/info")
async def info() -> Dict[str, Any]:
    return {
        "name": "lotoAI Gateway",
        "services": ["orchestrator", "rag"],
        "auth": "none (pilot)",
    }
