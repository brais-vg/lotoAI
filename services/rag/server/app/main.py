import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

import psycopg2
from fastapi import FastAPI, File, HTTPException, UploadFile
from psycopg2.extras import RealDictCursor

DB_AVAILABLE = True


def configure_logging() -> None:
    log_path = os.getenv("LOG_PATH", "./logs/app.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )


configure_logging()
logger = logging.getLogger("rag-server")

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/lotoai"
)
UPLOAD_DIR = Path(os.getenv("RAG_UPLOAD_DIR", "./data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS uploads (
                        id SERIAL PRIMARY KEY,
                        filename TEXT NOT NULL,
                        path TEXT NOT NULL,
                        size_bytes BIGINT NOT NULL,
                        content_type TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    """
                )
            conn.commit()
    except Exception as exc:  # pragma: no cover - se ejecuta en arranque real
        logger.exception("Fallo iniciando base de datos: %s", exc)
        global DB_AVAILABLE
        DB_AVAILABLE = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="lotoAI RAG Server", version="0.3.0", lifespan=lifespan)


@app.get("/health")
async def health() -> Dict[str, str]:
    status = {"status": "ok"}
    if not DB_AVAILABLE:
        status["db"] = "unavailable"
    return status


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Guarda archivo, almacena metadata en Postgres y devuelve sus datos."""
    if not DB_AVAILABLE:
        raise HTTPException(status_code=503, detail="DB no disponible")
    data = await file.read()
    uid = uuid.uuid4().hex
    safe_name = f"{uid}_{file.filename}"
    path = UPLOAD_DIR / safe_name
    try:
        path.write_bytes(data)
        size = len(data)
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO uploads (filename, path, size_bytes, content_type)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, created_at;
                    """,
                    (file.filename, str(path), size, file.content_type),
                )
                row = cur.fetchone()
                conn.commit()
        payload = {
            "id": row["id"],
            "filename": file.filename,
            "stored_path": str(path),
            "size_bytes": size,
            "content_type": file.content_type,
            "created_at": row["created_at"].isoformat(),
        }
        logger.info("Archivo guardado en RAG: %s", payload)
        return payload
    except Exception as exc:
        logger.exception("No se pudo almacenar el archivo: %s", exc)
        raise HTTPException(status_code=500, detail="No se pudo almacenar el archivo")


@app.get("/uploads")
async def list_uploads(limit: int = 20) -> Dict[str, Any]:
    """Devuelve uploads recientes desde Postgres."""
    if not DB_AVAILABLE:
        return {"items": []}
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, filename, path, size_bytes, content_type, created_at
                    FROM uploads
                    ORDER BY created_at DESC
                    LIMIT %s;
                    """,
                    (max(1, min(limit, 100)),),
                )
                rows = cur.fetchall()
        items: List[Dict[str, Any]] = [
            {
                "id": r["id"],
                "filename": r["filename"],
                "path": r["path"],
                "size_bytes": r["size_bytes"],
                "content_type": r["content_type"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
        return {"items": items}
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudieron listar uploads: %s", exc)
        return {"items": []}


@app.post("/search")
async def search(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Búsqueda básica: filtra uploads por nombre (ILIKE). Placeholder hasta integrar embeddings/Qdrant.
    """
    text = (query.get("text") or "").strip()
    if not DB_AVAILABLE or not text:
        return {"query": text, "results": []}
    try:
        like = f"%{text}%"
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, filename, path, size_bytes, content_type, created_at
                    FROM uploads
                    WHERE filename ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT 20;
                    """,
                    (like,),
                )
                rows = cur.fetchall()
        results: List[Dict[str, Any]] = [
            {
                "id": r["id"],
                "filename": r["filename"],
                "path": r["path"],
                "size_bytes": r["size_bytes"],
                "content_type": r["content_type"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]
        return {"query": text, "results": results}
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo ejecutar búsqueda: %s", exc)
        return {"query": text, "results": []}
