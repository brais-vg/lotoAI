import logging
import os
from typing import Any, Dict, List

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
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None
MAX_LOG_LENGTH = 500
CHAT_COUNTER = Counter("lotoai_orchestrator_chat_total", "Solicitudes de chat", ["provider"])
LOGS_COUNTER = Counter("lotoai_orchestrator_logs_total", "Lecturas de logs de chat")

app = FastAPI(title="lotoAI Agent Orchestrator", version="0.2.0")


class ChatRequest(BaseModel):
    message: str


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


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    """
    Chat simple con proveedor OpenAI. Si falta API key, devuelve respuesta stub.
    """
    if openai_client:
        try:
            completion = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": req.message}],
                temperature=0.3,
                max_tokens=300,
            )
            reply = completion.choices[0].message.content
            logger.info("Chat completado con OpenAI", extra={"provider": "openai"})
            log_chat(req.message, "openai", reply or "")
            CHAT_COUNTER.labels(provider="openai").inc()
            return {"message": reply, "provider": "openai", "input": req.message}
        except Exception as exc:  # pragma: no cover - solo en runtime con API real
            logger.exception("Error llamando a OpenAI: %s", exc)
            raise HTTPException(status_code=502, detail="Error con proveedor de IA")

    # Fallback stub para entornos sin API key
    logger.info("Devolviendo respuesta stub (sin OPENAI_API_KEY)")
    message = f"orchestration stub: {req.message}"
    log_chat(req.message, "stub", message)
    CHAT_COUNTER.labels(provider="stub").inc()
    return {"message": message, "provider": "stub", "input": req.message}


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


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
