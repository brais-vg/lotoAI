import logging
import os
from typing import Any, Dict, List

import httpx
import psycopg2
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled by requirements
    OpenAI = None  # type: ignore


def configure_logging() -> None:
    log_path = os.getenv("LOG_PATH", "./logs/app.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


configure_logging()
logger = logging.getLogger("agent-orchestrator")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DATABASE_URL = os.getenv("DATABASE_URL", "")
RAG_SERVER_URL = os.getenv("RAG_SERVER_URL", "http://rag-server:8000")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None
MAX_LOG_LENGTH = 500

# Chat configuration
CHAT_TEMPERATURE = float(os.getenv("CHAT_TEMPERATURE", "0.7"))
CHAT_MAX_TOKENS = int(os.getenv("CHAT_MAX_TOKENS", "1500"))
CHAT_HISTORY_LENGTH = int(os.getenv("CHAT_HISTORY_LENGTH", "5"))
RAG_MIN_SCORE = float(os.getenv("RAG_MIN_SCORE", "0.3"))
RAG_CONTEXT_CHARS = int(os.getenv("RAG_CONTEXT_CHARS", "1000"))

CHAT_COUNTER = Counter("lotoai_orchestrator_chat_total", "Solicitudes de chat", ["provider"])
LOGS_COUNTER = Counter("lotoai_orchestrator_logs_total", "Lecturas de logs de chat")

app = FastAPI(title="lotoAI Agent Orchestrator", version="0.2.0")


class ChatRequest(BaseModel):
    message: str
    top_k: int | None = 3


def log_chat(message: str, provider: str, response: str) -> None:
    """Persistencia best-effort de logs de chat en Postgres."""
    if not DATABASE_URL:
        return
    msg = (message or "")[:MAX_LOG_LENGTH]
    resp = (response or "")[:MAX_LOG_LENGTH]
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS chat_logs (
                        id SERIAL PRIMARY KEY,
                        message TEXT NOT NULL,
                        provider TEXT DEFAULT 'stub',
                        response TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
                cur.execute(
                    "INSERT INTO chat_logs (message, provider, response) VALUES (%s, %s, %s);",
                    (msg, provider, resp),
                )
            conn.commit()
    except Exception as exc:  # pragma: no cover - solo advertimos
        logger.warning("No se pudo registrar chat en DB: %s", exc)


async def fetch_rag_context(query: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Busca contexto en RAG usando búsqueda avanzada; degrada a lista vacía si falla."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:  # Más tiempo para advanced
            # Intentar búsqueda avanzada primero
            try:
                resp = await client.post(
                    f"{RAG_SERVER_URL}/search/advanced",
                    json={"text": query, "limit": limit, "num_variants": 3},
                )
                resp.raise_for_status()
                data = resp.json()
                results = data.get("results", [])[:limit]
                if results:
                    logger.info(f"Advanced RAG search returned {len(results)} results")
                    return results
            except Exception as exc:
                logger.warning(f"Advanced search failed, trying normal: {exc}")
                # Fallback a búsqueda normal
                resp = await client.post(
                    f"{RAG_SERVER_URL}/search",
                    json={"text": query, "limit": limit},
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])[:limit]
    except Exception as exc:  # pragma: no cover
        logger.warning("Fallo consultando RAG: %s", exc)
        return []


def build_context_message(sources: List[Dict[str, Any]]) -> str:
    """Construye mensaje de contexto filtrando por relevancia mínima."""
    if not sources:
        return ""
    
    # Filtrar por score mínimo
    relevant_sources = [s for s in sources if s.get("score", 0) >= RAG_MIN_SCORE]
    
    if not relevant_sources:
        logger.info(f"No relevant sources found (all below min_score={RAG_MIN_SCORE})")
        return ""
    
    logger.info(f"Using {len(relevant_sources)}/{len(sources)} sources (min_score={RAG_MIN_SCORE})")
    
    lines = []
    for idx, s in enumerate(relevant_sources, 1):
        name = s.get("filename") or s.get("path") or f"doc-{idx}"
        chunk = (s.get("chunk") or "")[:RAG_CONTEXT_CHARS]
        score = s.get("score", 0)
        chunk_index = s.get("chunk_index")
        total_chunks = s.get("total_chunks")
        chunk_type = s.get("chunk_type", "")
        
        # Construir metadata del chunk
        metadata_parts = [f"relevancia: {score:.2f}"]
        if chunk_index is not None and total_chunks:
            metadata_parts.append(f"fragmento {chunk_index + 1}/{total_chunks}")
        if chunk_type:
            metadata_parts.append(f"tipo: {chunk_type}")
        
        metadata = ", ".join(metadata_parts)
        lines.append(f"[{idx}] {name} ({metadata}):\n{chunk}")
    
    return "Contexto recuperado de documentos:\n" + "\n\n".join(lines)


def build_conversation_history(history: List[Dict[str, Any]], max_messages: int = 5) -> str:
    """Construye historial conversacional reciente para contexto."""
    if not history or max_messages <= 0:
        return ""
    
    # Tomar últimos N mensajes
    recent = history[-max_messages:] if len(history) > max_messages else history
    
    lines = []
    for msg in recent:
        role = msg.get("role", "unknown")
        text = msg.get("message", "")
        if role == "user":
            lines.append(f"Usuario: {text}")
        elif role == "bot":
            lines.append(f"Asistente: {text}")
    
    if lines:
        return "Conversación reciente:\n" + "\n".join(lines)
    return ""


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    """
    Chat simple con proveedor OpenAI. Si falta API key, devuelve respuesta stub.
    """
    top_k = req.top_k or 3
    sources = await fetch_rag_context(req.message, limit=top_k)
    
    # Log de fuentes recuperadas
    logger.info(f"RAG returned {len(sources)} sources for query: {req.message[:100]}")
    for idx, src in enumerate(sources):
        logger.debug(f"  Source {idx+1}: {src.get('filename')} (score: {src.get('score', 0):.3f})")
    
    context_msg = build_context_message(sources)
    
    if context_msg:
        logger.info("Using RAG context in prompt")
    else:
        logger.info("No relevant RAG context available")

    if openai_client:
        try:
            system = (
                "Eres un asistente experto que ayuda a usuarios respondiendo sus preguntas.\n\n"
                "INSTRUCCIONES PARA USO DE CONTEXTO:\n"
                "- Si recibes 'Contexto recuperado de documentos:', significa que el usuario tiene documentos subidos.\n"
                "- Este contexto contiene extractos REALES y VERIFICADOS de esos documentos.\n"
                "- Cuando el contexto contiene información relevante para la pregunta, ÚSALO como fuente principal.\n"
                "- SIEMPRE cita el nombre del archivo entre corchetes cuando uses información del contexto.\n"
                "- Si el contexto no es relevante para la pregunta, responde con tu conocimiento general.\n\n"
                "EJEMPLOS DE USO CORRECTO:\n"
                "Pregunta: ¿Qué universidades ofrecen el máster en IA?\n"
                "Contexto: [universidades.pdf] La UCM, UB y UPM ofrecen el Máster en Inteligencia Artificial...\n"
                "Respuesta CORRECTA: Según [universidades.pdf], las universidades que ofrecen el Máster en Inteligencia Artificial son la UCM, UB y UPM.\n\n"
                "ERRORES A EVITAR:\n"
                "❌ NUNCA digas 'no tengo información' si hay contexto relevante.\n"
                "❌ NUNCA ignores el contexto cuando responde directamente la pregunta.\n"
                "❌ NUNCA inventes información que no está en el contexto.\n\n"
                "Sé natural, útil y preciso. Cita siempre tus fuentes cuando uses el contexto."
            )
            messages = [{"role": "system", "content": system}]
            if context_msg:
                messages.append({"role": "system", "content": context_msg})
            messages.append({"role": "user", "content": req.message})
            
            completion = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=CHAT_TEMPERATURE,
                max_tokens=CHAT_MAX_TOKENS,
            )
            reply = completion.choices[0].message.content
            logger.info(f"OpenAI response generated (temp={CHAT_TEMPERATURE}, max_tokens={CHAT_MAX_TOKENS})")
            log_chat(req.message, "openai", reply or "")
            CHAT_COUNTER.labels(provider="openai").inc()
            return {"message": reply, "provider": "openai", "input": req.message, "sources": sources}
        except Exception as exc:  # pragma: no cover - solo en runtime con API real
            logger.exception("Error llamando a OpenAI: %s", exc)
            raise HTTPException(status_code=502, detail="Error con proveedor de IA")

    # Fallback stub para entornos sin API key
    logger.info("Devolviendo respuesta stub (sin OPENAI_API_KEY)")
    message = f"orchestration stub: {req.message}"
    log_chat(req.message, "stub", message)
    CHAT_COUNTER.labels(provider="stub").inc()
    return {"message": message, "provider": "stub", "input": req.message, "sources": sources}


@app.post("/orchestrate")
async def orchestrate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibilidad con endpoint previo. Por ahora delega a chat stub/IA.
    """
    message = payload.get("text") or payload.get("message") or str(payload)
    return await chat(ChatRequest(message=message))


@app.get("/chat/logs")
async def chat_logs(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Devuelve los ultimos chats registrados (best-effort)."""
    if not DATABASE_URL:
        return {"items": []}
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, message, provider, response, created_at
                    FROM chat_logs
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s;
                    """,
                    (lim, off),
                )
                rows = cur.fetchall()
        items: List[Dict[str, Any]] = [
            {
                "id": r[0],
                "message": r[1],
                "provider": r[2],
                "response": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
        LOGS_COUNTER.inc()
        return {"items": items}
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudieron leer logs de DB: %s", exc)
        return {"items": []}


# In-memory chat history storage
import asyncio
from datetime import datetime

chat_history: List[Dict[str, Any]] = []
history_lock = asyncio.Lock()


@app.get("/chat/history")
async def get_chat_history(limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """Devuelve el historial de chat."""
    async with history_lock:
        total = len(chat_history)
        messages = list(reversed(chat_history))  # Más recientes primero
        return {"messages": messages[offset:offset + limit], "total": total}


@app.post("/chat/history")
async def send_message_with_history(req: ChatRequest) -> Dict[str, Any]:
    """Procesa mensaje, guarda en historial y devuelve respuesta."""
    # Guardar mensaje del usuario
    user_message = {
        "id": len(chat_history) + 1,
        "role": "user",
        "message": req.message,
        "created_at": datetime.now().isoformat()
    }
    
    async with history_lock:
        chat_history.append(user_message)
    
    # Obtener respuesta del bot usando la lógica mejorada
    top_k = req.top_k or 3
    sources = await fetch_rag_context(req.message, limit=top_k)
    
    # Log de fuentes recuperadas
    logger.info(f"RAG returned {len(sources)} sources for query: {req.message[:100]}")
    for idx, src in enumerate(sources):
        logger.debug(f"  Source {idx+1}: {src.get('filename')} (score: {src.get('score', 0):.3f})")
    
    context_msg = build_context_message(sources)
    
    # Construir historial conversacional (excluyendo el mensaje actual)
    async with history_lock:
        history_context = build_conversation_history(
            chat_history[:-1],  # Excluir el mensaje que acabamos de añadir
            max_messages=CHAT_HISTORY_LENGTH
        )
    
    if context_msg:
        logger.info("Using RAG context in prompt")
    else:
        logger.info("No relevant RAG context available")
    
    if history_context:
        logger.info(f"Including {CHAT_HISTORY_LENGTH} previous messages in context")
    
    if openai_client:
        try:
            system = (
                "Eres un asistente experto que ayuda a usuarios respondiendo sus preguntas.\n\n"
                "INSTRUCCIONES PARA USO DE CONTEXTO:\n"
                "- Si recibes 'Contexto recuperado de documentos:', significa que el usuario tiene documentos subidos.\n"
                "- Este contexto contiene extractos REALES y VERIFICADOS de esos documentos.\n"
                "- Cuando el contexto contiene información relevante para la pregunta, ÚSALO como fuente principal.\n"
                "- SIEMPRE cita el nombre del archivo entre corchetes cuando uses información del contexto.\n"
                "- Si el contexto no es relevante para la pregunta, responde con tu conocimiento general.\n\n"
                "EJEMPLOS DE USO CORRECTO:\n"
                "Pregunta: ¿Qué universidades ofrecen el máster en IA?\n"
                "Contexto: [universidades.pdf] La UCM, UB y UPM ofrecen el Máster en Inteligencia Artificial...\n"
                "Respuesta CORRECTA: Según [universidades.pdf], las universidades que ofrecen el Máster en Inteligencia Artificial son la UCM, UB y UPM.\n\n"
                "ERRORES A EVITAR:\n"
                "❌ NUNCA digas 'no tengo información' si hay contexto relevante.\n"
                "❌ NUNCA ignores el contexto cuando responde directamente la pregunta.\n"
                "❌ NUNCA inventes información que no está en el contexto.\n\n"
                "Sé natural, útil y preciso. Cita siempre tus fuentes cuando uses el contexto."
            )
            messages = [{"role": "system", "content": system}]
            
            # Añadir historial conversacional si existe
            if history_context:
                messages.append({"role": "system", "content": history_context})
            
            # Añadir contexto RAG si existe
            if context_msg:
                messages.append({"role": "system", "content": context_msg})
            
            messages.append({"role": "user", "content": req.message})
            
            completion = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=CHAT_TEMPERATURE,
                max_tokens=CHAT_MAX_TOKENS,
            )
            bot_text = completion.choices[0].message.content or "Sin respuesta"
            provider = "openai"
            logger.info(f"OpenAI response generated (temp={CHAT_TEMPERATURE}, max_tokens={CHAT_MAX_TOKENS})")
        except Exception as exc:
            logger.exception("Error con OpenAI: %s", exc)
            bot_text = "Error procesando mensaje"
            provider = "error"
    else:
        bot_text = f"Echo (sin OpenAI): {req.message}"
        provider = "stub"
    
    # Guardar respuesta del bot
    bot_message = {
        "id": len(chat_history) + 1,
        "role": "bot",
        "message": bot_text,
        "created_at": datetime.now().isoformat()
    }
    
    async with history_lock:
        chat_history.append(bot_message)
    
    log_chat(req.message, provider, bot_text)
    CHAT_COUNTER.labels(provider=provider).inc()
    
    return {
        "user_message": user_message,
        "bot_message": bot_message
    }


@app.delete("/chat/history")
async def clear_chat_history() -> Dict[str, Any]:
    """Limpia el historial de chat."""
    async with history_lock:
        deleted = len(chat_history)
        chat_history.clear()
    
    return {"deleted": deleted, "message": "Chat history cleared"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
