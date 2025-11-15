import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
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
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None

app = FastAPI(title="lotoAI Agent Orchestrator", version="0.2.0")


class ChatRequest(BaseModel):
    message: str


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
            return {"message": reply, "provider": "openai", "input": req.message}
        except Exception as exc:  # pragma: no cover - solo en runtime con API real
            logger.exception("Error llamando a OpenAI: %s", exc)
            raise HTTPException(status_code=502, detail="Error con proveedor de IA")

    # Fallback stub para entornos sin API key
    logger.info("Devolviendo respuesta stub (sin OPENAI_API_KEY)")
    return {
        "message": f"orchestration stub: {req.message}",
        "provider": "stub",
        "input": req.message,
    }


@app.post("/orchestrate")
async def orchestrate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compatibilidad con endpoint previo. Por ahora delega a chat stub/IA.
    """
    message = payload.get("text") or payload.get("message") or str(payload)
    return await chat(ChatRequest(message=message))
