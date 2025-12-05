"""Chat routes proxy."""

import logging
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter

from ..config import ORCHESTRATOR_URL

logger = logging.getLogger("gateway.routes.chat")
router = APIRouter(tags=["chat"])

CHAT_COUNTER = Counter("lotoai_gateway_chat_total", "Chat proxied", ["status"])
LOGS_COUNTER = Counter("lotoai_gateway_logs_total", "Lecturas de logs", ["status"])


class ChatRequest(BaseModel):
    message: str


@router.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    """Proxy hacia el agente orquestador."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{ORCHESTRATOR_URL}/chat", json=req.model_dump())
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error llamando a orquestador: %s", exc)
        CHAT_COUNTER.labels(status="error").inc()
        raise HTTPException(status_code=502, detail="Error con agente orquestador")
    CHAT_COUNTER.labels(status="ok").inc()
    return resp.json()


@router.get("/api/chat/logs")
async def chat_logs(limit: int = 20) -> Dict[str, Any]:
    """Proxy de logs del orquestador."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(f"{ORCHESTRATOR_URL}/chat/logs", params={"limit": limit})
        resp.raise_for_status()
    except Exception as exc:
        logger.exception("Error obteniendo logs del orquestador: %s", exc)
        LOGS_COUNTER.labels(status="error").inc()
        return {"items": []}
    LOGS_COUNTER.labels(status="ok").inc()
    return resp.json()


# Chat History Endpoints
@router.get("/api/chat/history")
async def get_chat_history(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Obtiene historial de chat del orquestador."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{ORCHESTRATOR_URL}/chat/history",
                params={"limit": limit, "offset": offset}
            )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Error obteniendo historial: %s", exc)
        return {"messages": [], "total": 0}


@router.post("/api/chat/history")
async def send_chat_message(req: ChatRequest) -> Dict[str, Any]:
    """Envía mensaje y guarda en historial."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Note: Orchestrator expects "message" and "session_id"
            # Gateway's ChatRequest only has "message"
            # We'll forward it as is, orchestrator will use default session
            resp = await client.post(
                f"{ORCHESTRATOR_URL}/chat",  # Use /chat endpoint which handles history
                json=req.model_dump()
            )
        resp.raise_for_status()
        CHAT_COUNTER.labels(status="ok").inc()
        
        # Adapt response to what frontend expects if needed
        # Frontend expects: { user_message: {...}, bot_message: {...} } or similar?
        # Let's check frontend code.
        # ChatPage.jsx: 
        # const data = await api.chatHistory.sendMessage(userText);
        # setMessages((prev) => [..., { role: "user", text: data.user_message.message }, { role: "bot", text: data.bot_message.message }]);
        
        # Orchestrator /chat returns: { response: str, citations: str, history: List[dict] }
        # This is a BREAKING CHANGE for frontend if I don't adapt it.
        
        # Wait, the original gateway code called:
        # resp = await client.post(f"{ORCHESTRATOR_URL}/chat/history", json=req.model_dump())
        # The original orchestrator had /chat/history POST endpoint.
        # My new orchestrator has /chat POST endpoint.
        
        # I should adapt the response here to match what frontend expects OR update frontend.
        # Since I am refactoring backend, I should try to maintain API compatibility if possible,
        # or update frontend.
        
        # Let's see what the original orchestrator /chat/history returned.
        # It's hard to see without the code, but based on frontend:
        # data.user_message.message and data.bot_message.message
        
        data = resp.json()
        
        # New orchestrator returns: { response: "...", citations: "...", history: [...] }
        # I need to map this to old format for frontend compatibility
        
        return {
            "user_message": {"message": req.message},
            "bot_message": {"message": data["response"]}
        }
        
    except Exception as exc:
        logger.exception("Error en chat con historial: %s", exc)
        CHAT_COUNTER.labels(status="error").inc()
        raise HTTPException(status_code=502, detail="Error procesando mensaje")


@router.delete("/api/chat/history")
async def clear_chat_history() -> Dict[str, Any]:
    """Limpia el historial de chat."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.delete(f"{ORCHESTRATOR_URL}/chat/history")
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Error limpiando historial: %s", exc)
        return {"deleted": 0, "message": "Error clearing history"}
