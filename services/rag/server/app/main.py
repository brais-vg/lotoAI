import io
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

try:
    from sentence_transformers import CrossEncoder
except ImportError:  # pragma: no cover
    CrossEncoder = None  # type: ignore

import psycopg2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams, Filter, FieldCondition, MatchValue, Range

from app.embedding_service import get_embedding_service, EmbeddingService

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
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")

# Legacy OpenAI client for LLM calls (query variants)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None

# Embedding configuration
ENABLE_CONTENT_EMBED = os.getenv("ENABLE_CONTENT_EMBED", "0").lower() in {"1", "true", "yes"}

# Chunking configuration - UNLIMITED by default for quality
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "600"))
max_chunks_str = os.getenv("MAX_CHUNKS", "None")
MAX_CHUNKS = None if max_chunks_str.lower() in {"none", ""} else int(max_chunks_str)
MAX_CHUNKS_SAFETY = int(os.getenv("MAX_CHUNKS_SAFETY", "500"))  # Safety limit
CHUNK_OVERLAP_RATIO = float(os.getenv("CHUNK_OVERLAP_RATIO", "0.25"))

# Collection naming with prefix support
COLLECTION_PREFIX = os.getenv("QDRANT_COLLECTION_PREFIX", "")
if COLLECTION_PREFIX:
    EMBED_COLLECTION_UPLOADS = f"{COLLECTION_PREFIX}-uploads"
    EMBED_COLLECTION_CONTENT = f"{COLLECTION_PREFIX}-uploads-content"
else:
    EMBED_COLLECTION_UPLOADS = "uploads"
    EMBED_COLLECTION_CONTENT = "uploads-content"

# Reranking configuration
ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "1").lower() in {"1", "true", "yes"}
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
RERANK_TOP_K = int(os.getenv("RERANK_TOP_K", "50"))
RERANK_FINAL_K = int(os.getenv("RERANK_FINAL_K", "10"))

# Initialize embedding service
try:
    embedding_service: Optional[EmbeddingService] = get_embedding_service()
    logger.info(f"Initialized embedding service: {embedding_service.get_model_name() if embedding_service else 'None'}")
except Exception as exc:
    logger.warning(f"Could not initialize embedding service: {exc}")
    embedding_service = None

# Initialize reranker
reranker: Optional[CrossEncoder] = None
if ENABLE_RERANKING and CrossEncoder:
    try:
        logger.info(f"Loading reranker model: {RERANKER_MODEL}")
        reranker = CrossEncoder(RERANKER_MODEL)
        logger.info("Reranker loaded successfully")
    except Exception as exc:
        logger.warning(f"Could not load reranker: {exc}")

UPLOAD_DIR = Path(os.getenv("RAG_UPLOAD_DIR", "./data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_COUNTER = Counter("lotoai_rag_uploads_total", "Uploads procesados", ["status"])
EMBED_COUNTER = Counter("lotoai_rag_embeddings_total", "Embeddings generados", ["type"])
SEARCH_COUNTER = Counter("lotoai_rag_search_total", "Busquedas procesadas", ["mode"])
RERANK_COUNTER = Counter("lotoai_rag_rerank_total", "Reranking operations", ["status"])


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


def ensure_qdrant_collection(client: QdrantClient, name: str = "uploads", vector_size: Optional[int] = None) -> None:
    """Ensure Qdrant collection exists with appropriate vector size."""
    collections = [c.name for c in client.get_collections().collections]
    if name in collections:
        return
    
    # Auto-detect vector size from embedding service if not provided
    if vector_size is None:
        if embedding_service:
            vector_size = embedding_service.get_dimension()
        else:
            vector_size = 1536  # Default fallback
    
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    logger.info(f"Created Qdrant collection '{name}' with vector size {vector_size}")


def embed_text(text: str) -> List[float]:
    """Generate embedding for text using configured embedding service."""
    if not embedding_service:
        raise RuntimeError("No embedding service configured")
    return embedding_service.embed(text)


def generate_query_variants(query: str, num_variants: int = 3) -> List[str]:
    """
    Genera variantes de la query usando LLM para multi-query retrieval.
    """
    if not openai_client:
        return [query]
    
    try:
        prompt = f"""Generate {num_variants} different search queries that capture the same intent as: "{query}"

Make each query focus on different aspects or use different phrasings.
Return only the queries, one per line, without numbering or explanation."""

        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=150,
        )
        
        variants_text = response.choices[0].message.content or ""
        variants = [v.strip() for v in variants_text.split("\n") if v.strip()]
        
        # Siempre incluir la query original
        return [query] + variants[:num_variants]
    except Exception as exc:
        logger.warning("Error generando variantes de query: %s", exc)
        return [query]


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]], k: int = 60
) -> List[Dict[str, Any]]:
    """
    Fusiona múltiples listas de resultados usando Reciprocal Rank Fusion.
    RRF score = sum(1 / (rank + k)) para cada documento.
    """
    scores: Dict[int, float] = {}
    doc_data: Dict[int, Dict[str, Any]] = {}
    
    for results in results_list:
        for rank, doc in enumerate(results):
            doc_id = doc.get("id")
            if doc_id:
                # Acumular score RRF
                scores[doc_id] = scores.get(doc_id, 0) + 1 / (rank + k)
                # Guardar datos del documento (usar el de mayor score original)
                if doc_id not in doc_data or doc.get("score", 0) > doc_data[doc_id].get("score", 0):
                    doc_data[doc_id] = doc
    
    # Combinar scores RRF con datos del documento
    fused = []
    for doc_id, rrf_score in scores.items():
        doc = doc_data[doc_id].copy()
        doc["rrf_score"] = rrf_score
        doc["original_score"] = doc.get("score", 0)
        doc["score"] = rrf_score  # Usar RRF score como score principal
        fused.append(doc)
    
    return sorted(fused, key=lambda x: x["score"], reverse=True)


def chunk_text(text: str) -> List[Dict[str, Any]]:
    """
    Divide texto en chunks semánticos con overlap y metadata.
    Soporta chunks ilimitados para máxima calidad.
    Prioriza división por párrafos, luego por oraciones.
    
    Returns:
        List of dicts with 'text' and 'metadata' keys
    """
    if not text:
        return []
    
    chunks: List[Dict[str, Any]] = []
    size = max(200, CHUNK_SIZE_CHARS)
    overlap = int(size * CHUNK_OVERLAP_RATIO)
    
    # Dividir por párrafos primero
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    current_chunk = ""
    chunk_type = "paragraph"
    
    for para in paragraphs:
        # Si el párrafo cabe en el chunk actual
        if len(current_chunk) + len(para) + 2 <= size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # Guardar chunk actual si no está vacío
            if current_chunk:
                chunks.append({
                    "text": current_chunk,
                    "type": chunk_type,
                })
                # Check safety limit
                if MAX_CHUNKS is not None and len(chunks) >= MAX_CHUNKS:
                    break
                if len(chunks) >= MAX_CHUNKS_SAFETY:
                    logger.warning(f"Hit safety limit of {MAX_CHUNKS_SAFETY} chunks")
                    break
                # Mantener overlap del final del chunk anterior
                current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
            
            # Si el párrafo es muy largo, dividirlo por oraciones
            if len(para) > size:
                sentences = para.replace(". ", ".\n").split("\n")
                chunk_type = "sentence"
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= size:
                        current_chunk += (" " if current_chunk else "") + sent
                    else:
                        if current_chunk:
                            chunks.append({
                                "text": current_chunk,
                                "type": chunk_type,
                            })
                            if MAX_CHUNKS is not None and len(chunks) >= MAX_CHUNKS:
                                break
                            if len(chunks) >= MAX_CHUNKS_SAFETY:
                                logger.warning(f"Hit safety limit of {MAX_CHUNKS_SAFETY} chunks")
                                break
                            current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                        current_chunk = sent
                chunk_type = "paragraph"  # Reset type
            else:
                current_chunk = para
    
    # Añadir último chunk
    if current_chunk:
        if MAX_CHUNKS is None or len(chunks) < MAX_CHUNKS:
            if len(chunks) < MAX_CHUNKS_SAFETY:
                chunks.append({
                    "text": current_chunk,
                    "type": chunk_type,
                })
    
    # Add chunk metadata
    total_chunks = len(chunks)
    for idx, chunk in enumerate(chunks):
        chunk["chunk_index"] = idx
        chunk["total_chunks"] = total_chunks
    
    logger.debug(f"Created {total_chunks} chunks from {len(text)} characters")
    return chunks


def extract_text_from_bytes(data: bytes, content_type: str, filename: str) -> str:
    """
    Extrae texto de diferentes formatos de archivo.
    Soporta: PDF, DOCX, MD, HTML, TXT
    """
    ct = (content_type or "").lower()
    name = filename.lower()
    
    # PDF
    if "pdf" in ct or name.endswith(".pdf"):
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages]
            text = "\n".join(pages)
        except Exception as exc:
            logger.warning("No se pudo extraer texto de PDF: %s", exc)
            return ""
    
    # DOCX
    elif "word" in ct or name.endswith((".docx", ".doc")):
        try:
            from docx import Document
            doc = Document(io.BytesIO(data))
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            text = "\n".join(paragraphs)
        except Exception as exc:
            logger.warning("No se pudo extraer texto de DOCX: %s", exc)
            return ""
    
    # HTML
    elif "html" in ct or name.endswith((".html", ".htm")):
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(data, "lxml")
            # Eliminar scripts y estilos
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except Exception as exc:
            logger.warning("No se pudo extraer texto de HTML: %s", exc)
            return ""
    
    # Markdown
    elif name.endswith(".md"):
        try:
            import markdown
            from bs4 import BeautifulSoup
            # Convertir MD a HTML y luego extraer texto
            html = markdown.markdown(data.decode("utf-8", errors="ignore"))
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator="\n", strip=True)
        except Exception as exc:
            logger.warning("No se pudo extraer texto de MD: %s", exc)
            return ""
    
    # Texto plano (fallback)
    else:
        try:
            text = data.decode("utf-8", errors="ignore")
        except Exception:
            return ""
    
    # Limpieza de texto
    # Eliminar líneas vacías múltiples
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    
    # Eliminar caracteres de control excepto saltos de línea
    text = "".join(char for char in text if char.isprintable() or char == "\n")
    
    return text


def index_content_embeddings(payload: Dict[str, Any], data: bytes, content_type: str) -> None:
    """Index document content chunks in Qdrant with embeddings."""
    if not ENABLE_CONTENT_EMBED or not embedding_service:
        return
    
    text = extract_text_from_bytes(data, content_type, payload.get("filename", ""))
    chunks = chunk_text(text)
    if not chunks:
        return
    
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_qdrant_collection(client, name=EMBED_COLLECTION_CONTENT)
        points = []
        
        for chunk_data in chunks:
            chunk_text_str = chunk_data["text"]
            vector = embed_text(chunk_text_str)
            
            point = PointStruct(
                id=payload["id"] * 1000 + chunk_data["chunk_index"],
                vector=vector,
                payload={
                    "file_id": payload["id"],
                    "filename": payload.get("filename"),
                    "path": payload.get("stored_path"),
                    "size_bytes": payload.get("size_bytes"),
                    "content_type": payload.get("content_type"),
                    "created_at": payload.get("created_at"),
                    "chunk": chunk_text_str[:300],  # Store preview
                    "chunk_index": chunk_data["chunk_index"],
                    "total_chunks": chunk_data["total_chunks"],
                    "chunk_type": chunk_data["type"],
                },
            )
            points.append(point)
        
        client.upsert(collection_name=EMBED_COLLECTION_CONTENT, points=points)
        EMBED_COUNTER.labels(type="content").inc(len(points))
        logger.info(f"Indexed {len(points)} content chunks for file_id={payload['id']}")
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo indexar contenido en Qdrant: %s", exc)


def index_upload_qdrant(payload: Dict[str, Any]) -> None:
    """Indexa el upload en Qdrant con embedding del nombre de fichero."""
    if not embedding_service:
        return
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_qdrant_collection(client, name=EMBED_COLLECTION_UPLOADS)
        vector = embed_text(payload.get("filename", ""))
        point = PointStruct(
            id=payload["id"],
            vector=vector,
            payload=payload,
        )
        client.upsert(collection_name=EMBED_COLLECTION_UPLOADS, points=[point])
        logger.info("Indexado en Qdrant upload id=%s", payload["id"])
        EMBED_COUNTER.labels(type="filename").inc()
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo indexar en Qdrant: %s", exc)


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
        index_upload_qdrant(payload)
        index_content_embeddings(payload, data, file.content_type or "")
        UPLOAD_COUNTER.labels(status="ok").inc()
        return payload
    except Exception as exc:
        logger.exception("No se pudo almacenar el archivo: %s", exc)
        UPLOAD_COUNTER.labels(status="error").inc()
        raise HTTPException(status_code=500, detail="No se pudo almacenar el archivo")


@app.get("/uploads")
async def list_uploads(limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Devuelve uploads recientes desde Postgres."""
    if not DB_AVAILABLE:
        return {"items": []}
    lim = max(1, min(limit, 100))
    off = max(0, offset)
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, filename, path, size_bytes, content_type, created_at
                    FROM uploads
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s;
                    """,
                    (lim, off),
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


def rerank_results(query: str, results: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
    """
    Rerank search results using cross-encoder model.
    
    Args:
        query: Search query
        results: List of result dicts with 'chunk' or 'filename' for text matching
        top_k: Number of top results to return after reranking
        
    Returns:
        Reranked results with updated scores and rerank_score field
    """
    if not reranker or not results:
        return results[:top_k]
    
    try:
        # Prepare query-document pairs for cross-encoder
        pairs = []
        for result in results:
            # Use chunk preview if available, otherwise use filename
            text = result.get("chunk", result.get("filename", ""))
            pairs.append([query, text])
        
        # Get reranking scores
        scores = reranker.predict(pairs)
        
        # Add rerank scores to results and sort
        for i, result in enumerate(results):
            result["rerank_score"] = float(scores[i])
            result["original_score"] = result.get("score", 0.0)
        
        # Sort by rerank score and return top k
        reranked = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
        RERANK_COUNTER.labels(status="success").inc()
        logger.debug(f"Reranked {len(results)} results, returning top {top_k}")
        return reranked[:top_k]
    except Exception as exc:
        logger.warning("Error during reranking: %s", exc)
        RERANK_COUNTER.labels(status="error").inc()
        return results[:top_k]


@app.post("/search")
async def search(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Búsqueda híbrida mejorada con reranking:
    - Búsqueda vectorial en contenido y nombres
    - Reranking opcional por relevancia
    - Deduplicación de resultados
    - Fallback a LIKE en Postgres
    """
    text = (query.get("text") or "").strip()
    limit = min(query.get("limit", 10), 50)  # Máximo 50 resultados
    use_reranking = query.get("rerank", ENABLE_RERANKING)
    
    if not DB_AVAILABLE or not text:
        return {"query": text, "results": []}
    
    try:
        if embedding_service:
            try:
                client = QdrantClient(url=QDRANT_URL)
                vector = embed_text(text)
                results_map: Dict[int, Dict[str, Any]] = {}  # Para deduplicar por upload_id
                
                # Buscar en contenido
                try:
                    ensure_qdrant_collection(client, name=EMBED_COLLECTION_CONTENT)
                    found_content = client.search(
                        collection_name=EMBED_COLLECTION_CONTENT,
                        query_vector=vector,
                        limit=RERANK_TOP_K if use_reranking else limit * 2,
                    )
                    for hit in found_content:
                        payload = hit.payload or {}
                        file_id = payload.get("file_id")  # Note: Changed from upload_id
                        if file_id:
                            # Si ya existe, mantener el de mayor score
                            if file_id not in results_map or hit.score > results_map[file_id].get("score", 0):
                                results_map[file_id] = {
                                    "id": file_id,
                                    "filename": payload.get("filename", ""),
                                    "chunk": payload.get("chunk", ""),
                                    "chunk_index": payload.get("chunk_index", 0),
                                    "chunk_type": payload.get("chunk_type", ""),
                                    "score": hit.score,
                                    "created_at": payload.get("created_at"),
                                    "content_type": payload.get("content_type"),
                                    "size_bytes": payload.get("size_bytes"),
                                }
                except Exception as exc:
                    logger.warning("Fallo búsqueda vectorial de contenido: %s", exc)

                # Buscar en nombres de archivos
                try:
                    ensure_qdrant_collection(client, name=EMBED_COLLECTION_UPLOADS)
                    found_files = client.search(
                        collection_name=EMBED_COLLECTION_UPLOADS,
                        query_vector=vector,
                        limit=limit,
                    )
                    for hit in found_files:
                        payload = hit.payload or {}
                        file_id = payload.get("id")
                        if file_id:
                            # Si ya existe del contenido, combinar scores
                            if file_id in results_map:
                                # Boost si coincide tanto en nombre como en contenido
                                results_map[file_id]["score"] = (results_map[file_id]["score"] + hit.score) / 2
                                results_map[file_id]["name_match"] = True
                            else:
                                results_map[file_id] = {
                                    "id": file_id,
                                    "filename": payload.get("filename", ""),
                                    "chunk": "",  # No hay chunk para búsqueda por nombre
                                    "score": hit.score,
                                    "created_at": payload.get("created_at"),
                                    "content_type": payload.get("content_type"),
                                    "size_bytes": payload.get("size_bytes"),
                                    "name_match": True,
                                }
                except Exception as exc:
                    logger.warning("Fallo búsqueda vectorial de nombres: %s", exc)

                if results_map:
                    # Convert to list and sort
                    results_vec = sorted(
                        results_map.values(),
                        key=lambda x: x.get("score", 0),
                        reverse=True
                    )
                    
                    # Apply reranking if enabled
                    if use_reranking and reranker:
                        results_vec = rerank_results(text, results_vec, top_k=min(RERANK_FINAL_K, limit))
                        mode = "vector+rerank"
                    else:
                        results_vec = results_vec[:limit]
                        mode = "vector"
                    
                    SEARCH_COUNTER.labels(mode=mode).inc()
                    return {"query": text, "results": results_vec, "mode": mode}
            except Exception as exc:
                logger.warning("Fallo búsqueda vectorial, se usa LIKE: %s", exc)

        # Fallback a búsqueda LIKE
        like = f"%{text}%"
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id, filename, path, size_bytes, content_type, created_at
                    FROM uploads
                    WHERE filename ILIKE %s
                    ORDER BY created_at DESC
                    LIMIT %s;
                    """,
                    (like, limit),
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
                "score": 0.5,  # Score artificial para consistencia
            }
            for r in rows
        ]
        SEARCH_COUNTER.labels(mode="like").inc()
        return {"query": text, "results": results, "mode": "like"}
    except Exception as exc:
        logger.warning("No se pudo ejecutar búsqueda: %s", exc)
        return {"query": text, "results": [], "mode": "error"}


@app.post("/search/advanced")
async def advanced_search(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Búsqueda avanzada con multi-query retrieval y Reciprocal Rank Fusion.
    Genera variantes de la query y fusiona resultados para mejor recall.
    """
    text = (query.get("text") or "").strip()
    limit = min(query.get("limit", 10), 50)
    num_variants = min(query.get("num_variants", 3), 5)
    
    if not DB_AVAILABLE or not text or not openai_client:
        return {"query": text, "results": [], "mode": "fallback"}
    
    try:
        # 1. Generar variantes de la query
        query_variants = generate_query_variants(text, num_variants)
        logger.info(f"Generated {len(query_variants)} query variants for: {text}")
        
        # 2. Buscar con cada variante
        all_results_lists = []
        client = QdrantClient(url=QDRANT_URL)
        
        for variant in query_variants:
            try:
                vector = embed_text(variant)
                variant_results = []
                
                # Buscar en contenido
                try:
                    ensure_qdrant_collection(client, name=EMBED_COLLECTION_CONTENT)
                    found_content = client.search(
                        collection_name=EMBED_COLLECTION_CONTENT,
                        query_vector=vector,
                        limit=limit * 2,
                    )
                    for hit in found_content:
                        payload = hit.payload or {}
                        payload["score"] = hit.score
                        variant_results.append(payload)
                except Exception as exc:
                    logger.warning(f"Error búsqueda contenido variante '{variant}': {exc}")
                
                # Buscar en nombres
                try:
                    ensure_qdrant_collection(client, name="uploads")
                    found_files = client.search(
                        collection_name="uploads",
                        query_vector=vector,
                        limit=limit,
                    )
                    for hit in found_files:
                        payload = hit.payload or {}
                        payload["score"] = hit.score
                        variant_results.append(payload)
                except Exception as exc:
                    logger.warning(f"Error búsqueda nombres variante '{variant}': {exc}")
                
                if variant_results:
                    all_results_lists.append(variant_results)
                    
            except Exception as exc:
                logger.warning(f"Error procesando variante '{variant}': {exc}")
        
        # 3. Fusionar resultados con RRF
        if all_results_lists:
            fused_results = reciprocal_rank_fusion(all_results_lists)
            final_results = fused_results[:limit]
            
            SEARCH_COUNTER.labels(mode="advanced").inc()
            return {
                "query": text,
                "query_variants": query_variants,
                "results": final_results,
                "mode": "advanced",
                "num_variants_used": len(query_variants)
            }
        else:
            return {"query": text, "results": [], "mode": "no_results"}
            
    except Exception as exc:
        logger.warning(f"Error en búsqueda avanzada: {exc}")
        return {"query": text, "results": [], "mode": "error"}


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
