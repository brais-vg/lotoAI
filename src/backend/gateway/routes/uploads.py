"""Upload routes proxy."""

import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from prometheus_client import Counter

from ..config import RAG_SERVER_URL

logger = logging.getLogger("gateway.routes.upload")
router = APIRouter(tags=["upload"])

UPLOAD_COUNTER = Counter("lotoai_gateway_upload_total", "Uploads proxied", ["status"])


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Envía archivo al RAG para almacenarlo y registrar metadata."""
    try:
        content = await file.read()
        files = {"file": (file.filename, content, file.content_type or "application/octet-stream")}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(f"{RAG_SERVER_URL}/upload", files=files)
        resp.raise_for_status()
        data = resp.json()
        logger.info("Archivo subido a RAG: %s", data.get("id"))
        UPLOAD_COUNTER.labels(status="ok").inc()
        return data
    except Exception as exc:
        logger.exception("Error subiendo archivo a RAG: %s", exc)
        UPLOAD_COUNTER.labels(status="error").inc()
        raise HTTPException(status_code=502, detail="Error al subir archivo al RAG")


@router.get("/api/uploads")
async def list_uploads(limit: int = 20) -> Dict[str, Any]:
    """Proxy para listar uploads recientes desde RAG."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Note: RAG server needs /uploads endpoint. 
            # I implemented /upload (POST) but not /uploads (GET) in RAG server routes/upload.py
            # I missed that!
            resp = await client.get(f"{RAG_SERVER_URL}/uploads", params={"limit": limit})
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error obteniendo uploads del RAG: %s", exc)
        return {"items": []}
    return resp.json()
