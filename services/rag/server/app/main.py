import io
import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover
    OpenAI = None  # type: ignore

import psycopg2
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if (OpenAI and OPENAI_API_KEY) else None
ENABLE_CONTENT_EMBED = os.getenv("ENABLE_CONTENT_EMBED", "0").lower() in {"1", "true", "yes"}
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "800"))
MAX_CHUNKS = int(os.getenv("MAX_CHUNKS", "4"))
EMBED_COLLECTION_CONTENT = os.getenv("EMBED_COLLECTION_CONTENT", "uploads-content")

UPLOAD_DIR = Path(os.getenv("RAG_UPLOAD_DIR", "./data/uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_COUNTER = Counter("lotoai_rag_uploads_total", "Uploads procesados", ["status"])
EMBED_COUNTER = Counter("lotoai_rag_embeddings_total", "Embeddings generados", ["type"])
SEARCH_COUNTER = Counter("lotoai_rag_search_total", "Busquedas procesadas", ["mode"])


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


def ensure_qdrant_collection(client: QdrantClient, name: str = "uploads") -> None:
    collections = [c.name for c in client.get_collections().collections]
    if name in collections:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )


def embed_text(text: str) -> List[float]:
    if not openai_client:
        raise RuntimeError("No embedding provider configurado")
    result = openai_client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=text[:2000],
    )
    return result.data[0].embedding  # type: ignore[attr-defined]


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


def chunk_text(text: str) -> List[str]:
    """
    Divide texto en chunks semánticos con overlap.
    Prioriza división por párrafos, luego por oraciones.
    """
    if not text:
        return []
    
    chunks = []
    size = max(200, CHUNK_SIZE_CHARS)
    overlap = size // 4  # 25% overlap para mantener contexto
    
    # Dividir por párrafos primero
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    current_chunk = ""
    for para in paragraphs:
        # Si el párrafo cabe en el chunk actual
        if len(current_chunk) + len(para) + 2 <= size:
            current_chunk += ("\n\n" if current_chunk else "") + para
        else:
            # Guardar chunk actual si no está vacío
            if current_chunk:
                chunks.append(current_chunk)
                if len(chunks) >= MAX_CHUNKS:
                    break
                # Mantener overlap del final del chunk anterior
                current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
            
            # Si el párrafo es muy largo, dividirlo por oraciones
            if len(para) > size:
                sentences = para.replace(". ", ".\n").split("\n")
                for sent in sentences:
                    if len(current_chunk) + len(sent) + 1 <= size:
                        current_chunk += (" " if current_chunk else "") + sent
                    else:
                        if current_chunk:
                            chunks.append(current_chunk)
                            if len(chunks) >= MAX_CHUNKS:
                                break
                            current_chunk = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                        current_chunk = sent
            else:
                current_chunk = para
    
    # Añadir último chunk
    if current_chunk and len(chunks) < MAX_CHUNKS:
        chunks.append(current_chunk)
    
    return chunks[:MAX_CHUNKS]


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
    if not ENABLE_CONTENT_EMBED or not openai_client:
        return
    text = extract_text_from_bytes(data, content_type, payload.get("filename", ""))
    chunks = chunk_text(text)
    if not chunks:
        return
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_qdrant_collection(client, name=EMBED_COLLECTION_CONTENT)
        points = []
        for idx, chunk in enumerate(chunks):
            vector = embed_text(chunk)
            point = PointStruct(
                id=payload["id"] * 1000 + idx,
                vector=vector,
                payload={
                    "file_id": payload["id"],
                    "filename": payload.get("filename"),
                    "path": payload.get("stored_path"),
                    "size_bytes": payload.get("size_bytes"),
                    "content_type": payload.get("content_type"),
                    "created_at": payload.get("created_at"),
                    "chunk": chunk[:300],
                },
            )
            points.append(point)
        client.upsert(collection_name=EMBED_COLLECTION_CONTENT, points=points)
        EMBED_COUNTER.labels(type="content").inc(len(points))
    except Exception as exc:  # pragma: no cover
        logger.warning("No se pudo indexar contenido en Qdrant: %s", exc)


def index_upload_qdrant(payload: Dict[str, Any]) -> None:
    """Indexa el upload en Qdrant con embedding del nombre de fichero."""
    if not openai_client:
        return
    try:
        client = QdrantClient(url=QDRANT_URL)
        ensure_qdrant_collection(client)
        vector = embed_text(payload.get("filename", ""))
        point = PointStruct(
            id=payload["id"],
            vector=vector,
            payload=payload,
        )
        client.upsert(collection_name="uploads", points=[point])
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




@app.post("/search")
async def search(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Búsqueda híbrida mejorada:
    - Búsqueda vectorial en contenido y nombres
    - Reranking por relevancia
    - Deduplicación de resultados
    - Fallback a LIKE en Postgres
    """
    text = (query.get("text") or "").strip()
    limit = min(query.get("limit", 10), 50)  # Máximo 50 resultados
    
    if not DB_AVAILABLE or not text:
        return {"query": text, "results": []}
    
    try:
        if openai_client:
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
                        limit=limit * 2,  # Buscar más para tener opciones
                    )
                    for hit in found_content:
                        payload = hit.payload or {}
                        upload_id = payload.get("upload_id")
                        if upload_id:
                            # Si ya existe, mantener el de mayor score
                            if upload_id not in results_map or hit.score > results_map[upload_id].get("score", 0):
                                results_map[upload_id] = {
                                    "id": upload_id,
                                    "filename": payload.get("filename", ""),
                                    "chunk": payload.get("chunk", ""),
                                    "chunk_index": payload.get("chunk_index", 0),
                                    "score": hit.score,
                                    "created_at": payload.get("created_at"),
                                    "content_type": payload.get("content_type"),
                                    "size_bytes": payload.get("size_bytes"),
                                }
                except Exception as exc:
                    logger.warning("Fallo búsqueda vectorial de contenido: %s", exc)

                # Buscar en nombres de archivos
                try:
                    ensure_qdrant_collection(client, name="uploads")
                    found_files = client.search(
                        collection_name="uploads",
                        query_vector=vector,
                        limit=limit,
                    )
                    for hit in found_files:
                        payload = hit.payload or {}
                        upload_id = payload.get("id")
                        if upload_id:
                            # Si ya existe del contenido, combinar scores
                            if upload_id in results_map:
                                # Boost si coincide tanto en nombre como en contenido
                                results_map[upload_id]["score"] = (results_map[upload_id]["score"] + hit.score) / 2
                                results_map[upload_id]["name_match"] = True
                            else:
                                results_map[upload_id] = {
                                    "id": upload_id,
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
                    # Ordenar por score descendente y limitar
                    results_vec = sorted(
                        results_map.values(),
                        key=lambda x: x.get("score", 0),
                        reverse=True
                    )[:limit]
                    
                    SEARCH_COUNTER.labels(mode="vector").inc()
                    return {"query": text, "results": results_vec, "mode": "vector"}
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
