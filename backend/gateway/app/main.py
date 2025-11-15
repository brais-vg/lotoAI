import logging
import os
from typing import Any, Dict

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


def configure_logging() -> None:
    log_path = os.getenv("LOG_PATH", "./logs/app.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


configure_logging()
logger = logging.getLogger("gateway")

ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://agent-orchestrator:8090")
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://rag-server:8000")
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app = FastAPI(title="lotoAI Gateway", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/info")
async def info() -> Dict[str, Any]:
    return {
        "name": "lotoAI Gateway",
        "services": ["orchestrator", "rag"],
        "auth": "none (pilot)",
    }


@app.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    """Proxy hacia el agente orquestador."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{ORCHESTRATOR_URL}/chat", json=req.model_dump())
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error llamando a orquestador: %s", exc)
        raise HTTPException(status_code=502, detail="Error con agente orquestador")
    return resp.json()


@app.post("/api/upload")
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
        return data
    except Exception as exc:
        logger.exception("Error subiendo archivo a RAG: %s", exc)
        raise HTTPException(status_code=502, detail="Error al subir archivo al RAG")
