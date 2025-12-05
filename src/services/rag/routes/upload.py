"""Upload routes."""

import logging
import uuid
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from psycopg2.extras import RealDictCursor
import psycopg2

from ..config import DATABASE_URL, UPLOAD_DIR
from ..core.indexing import index_filename, index_content
from ..models.schemas import UploadResponse

logger = logging.getLogger("rag-server.routes.upload")
router = APIRouter(tags=["uploads"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload and index a file."""
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="Database not configured")
        
    try:
        # Read file
        data = await file.read()
        size = len(data)
        
        # Save to disk
        uid = uuid.uuid4().hex
        safe_name = f"{uid}_{file.filename}"
        path = UPLOAD_DIR / safe_name
        
        with open(path, "wb") as f:
            f.write(data)
            
        # Save to DB
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
        
        # Prepare response payload
        payload = {
            "id": row["id"],
            "filename": file.filename,
            "stored_path": str(path),
            "size_bytes": size,
            "content_type": file.content_type,
            "created_at": row["created_at"].isoformat(),
        }
        
        # Index in Qdrant
        index_filename(payload)
        indexing_result = index_content(payload, data, file.content_type or "")
        
        payload["indexing"] = indexing_result
        
        logger.info(f"File uploaded and indexed: {file.filename}")
        return payload
        
    except Exception as exc:
        logger.error(f"Upload failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
