"""
Script de reindexado para uploads existentes.
- Reutiliza los helpers de app.main para indexar nombre y contenido (si ENABLE_CONTENT_EMBED=1).
- Ejecutar dentro del contenedor RAG:
    docker compose -f infra/docker/docker-compose.yml --profile core --profile app exec rag-server python -m app.reindex
"""

import os
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

from app.main import (
    DATABASE_URL,
    index_content_embeddings,
    index_upload_qdrant,
    logger,
)


def fetch_uploads() -> list[dict]:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, filename, path, size_bytes, content_type, created_at
                FROM uploads
                ORDER BY id ASC;
                """
            )
            return list(cur.fetchall())


def reindex() -> None:
    uploads = fetch_uploads()
    logger.info("Reindexando %s uploads", len(uploads))
    for row in uploads:
        path = Path(row["path"])
        if not path.exists():
            logger.warning("No existe el archivo para id=%s en %s", row["id"], path)
            continue
        data = path.read_bytes()
        payload = {
            "id": row["id"],
            "filename": row["filename"],
            "stored_path": row["path"],
            "size_bytes": row["size_bytes"],
            "content_type": row["content_type"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
        try:
            index_upload_qdrant(payload)
            index_content_embeddings(payload, data, row["content_type"] or "")
        except Exception as exc:  # pragma: no cover
            logger.warning("Fallo reindexando id=%s: %s", row["id"], exc)


if __name__ == "__main__":
    if not DATABASE_URL:
        raise SystemExit("DATABASE_URL no configurado")
    reindex()
