# lotoAI
Plataforma modular de servicios de IA. Este repo contiene el esqueleto inicial y un piloto basico funcional (chat + subida de ficheros a RAG).

## Arquitectura general
- Cliente web responsive (sin login) que consume el gateway.
- Gateway/BFF (FastAPI) para orquestar chat y subida de ficheros.
- Agente orquestador (FastAPI) que usa OpenAI API (fallback stub si no hay API key).
- RAG server (FastAPI) que almacena ficheros en disco y registra metadata en Postgres.
- Dependencias: Postgres, Qdrant, NATS, MinIO (via Docker compose). MCP y agentes externos quedan pendientes.

## Estructura de carpetas
```
backend/                  # Gateway/API BFF
frontend/web/             # Web estatica responsive para chat + upload + busqueda/logs
infra/docker/             # docker-compose con perfiles
services/
  agent-orchestrator/     # Chat con OpenAI
  mcp/                    # MCP server/cliente (placeholder)
  rag/
    server/               # RAG server: upload + search stub
    ingestion/            # Scripts de ingesta (placeholder)
    vector-store/         # Placeholder
  agents-external/        # Placeholder agentes externos
```

## Como levantar el piloto (local)
1. Copia `.env.example` a `.env` y rellena `OPENAI_API_KEY` si quieres respuestas reales.
2. Ejecuta `./scripts/init.sh` (Linux/Mac) o `./scripts/init.ps1` (Windows) para construir y levantar perfiles core+app.
   - Web: http://localhost:3000
   - Gateway API: http://localhost:8088
   - Orquestador: http://localhost:8090
   - RAG: http://localhost:8000
3. Para parar: `./scripts/stop.sh` o `./scripts/stop.ps1`. Para reiniciar sin build: `./scripts/start.sh` o `./scripts/start.ps1`.
4. Sin API key el chat usa stub. El upload requiere Postgres (perfil core) y crea metadata en la DB.
5. **Configuraci\u00f3n RAG** (ver `.env`):
   - **Embeddings**: Soporta OpenAI API (por defecto) o modelos locales (Sentence Transformers)
     - `EMBEDDING_PROVIDER`: `openai` (por defecto) o `local`
     - `LOCAL_EMBEDDING_MODEL`: Modelo local a usar (ej: `BAAI/bge-m3`, `all-MiniLM-L6-v2`)
     - `OPENAI_EMBED_MODEL`: Modelo OpenAI si se usa API (por defecto: `text-embedding-3-small`)
   - **Chunking**: Configuraci\u00f3n para divisi\u00f3n de documentos
     - `CHUNK_SIZE_CHARS`: Tama\u00f1o de chunks en caracteres (por defecto: `600`)
     - `MAX_CHUNKS`: L\u00edmite de chunks por documento (`None` para ilimitado, por defecto)
     - `MAX_CHUNKS_SAFETY`: L\u00edmite de seguridad (por defecto: `500`)
     - `CHUNK_OVERLAP_RATIO`: Proporci\u00f3n de solapamiento (por defecto: `0.25`)
   - **Reranking**: Mejora resultados de b\u00fasqueda con cross-encoder
     - `ENABLE_RERANKING`: Habilitar reranking (por defecto: `1`)
     - `RERANKER_MODEL`: Modelo a usar (por defecto: `cross-encoder/ms-marco-MiniLM-L-6-v2`)
     - `RERANK_TOP_K`: Resultados a reordenar (por defecto: `50`)
     - `RERANK_FINAL_K`: Resultados finales tras reranking (por defecto: `10`)
   - `ENABLE_CONTENT_EMBED`: Activar indexaci\u00f3n de contenido (`1` o `0`, por defecto: `0`)
   - `QDRANT_COLLECTION_PREFIX`: Prefijo opcional para colecciones Qdrant (permite m\u00faltiples modelos)
6. Cliente React opcional: `cd frontend/vite-app && npm install && npm run dev` (usa `VITE_API_BASE` para el gateway, por defecto http://localhost:8088).

## Endpoints principales
- Gateway: `POST /api/chat` (body `{message}`) -> orquestador; `POST /api/upload` (multipart `file`) -> RAG; `GET /api/uploads` (lista con paginacion offset/limit); `GET /api/chat/logs`; `POST /api/search` -> RAG; `GET /metrics` (Prometheus).
- Orquestador: `POST /chat` -> OpenAI/stub; `GET /chat/logs` (offset/limit); `GET /metrics`.
- RAG: `POST /upload` (guarda fichero y metadata en Postgres; indexa en Qdrant con embeddings configurables);  
  `GET /uploads` (offset/limit); 
  `POST /search` (b\u00fasqueda h\u00edbrida vectorial con reranking opcional, fallback LIKE; par\u00e1metros: `text`, `limit`, `rerank`);  
  `POST /search/advanced` (multi-query retrieval con RRF);  
  `GET /metrics`.

## Tests
- Cada servicio Python incluye `tests/` con validaciones basicas de health/contratos iniciales.
- Ejemplo: `cd backend/gateway && pip install -r requirements.txt && pytest`
- Guia ampliada en `docs/TESTING.md`.

## Notas
- Logging persiste en `/app/logs/app.log` (volumenes mapeados en docker-compose para gateway/orquestador/RAG). Formato actual: textual.
- **RAG Mejorado**:
  - Soporta embeddings locales (Sentence Transformers) o OpenAI API
  - Chunking ilimitado por defecto para m\u00e1xima calidad (configurable con `MAX_CHUNKS`)
  - Reranking con cross-encoder para mejorar relevancia de resultados
  - B\u00fasqueda h\u00edbrida: contenido + nombres de archivo
  - Multi-query retrieval con Reciprocal Rank Fusion en `/search/advanced`
- Reindexado: dentro del contenedor RAG puedes reindexar nombre + contenido existentes con  
  `docker compose -f infra/docker/docker-compose.yml --profile core --profile app exec -T rag-server python -c "import sys; sys.path.append('/app'); import app.reindex as r; r.reindex()"`
  - **Importante**: Reindexar con nuevos par\u00e1metros de chunking crear\u00e1 m\u00e1s chunks (implica m\u00e1s llamadas a API de embeddings si usas OpenAI).
- MCP y agentes externos espec\u00edficos siguen en desarrollo.

- MCP y agentes externos especificos siguen en desarrollo.
