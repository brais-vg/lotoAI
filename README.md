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
5. Embeddings de contenido: activados con `ENABLE_CONTENT_EMBED=1` (ver `.env`). Usa OpenAI + Qdrant; controla coste ajustando `CHUNK_SIZE_CHARS`/`MAX_CHUNKS`.
6. Cliente React opcional: `cd frontend/vite-app && npm install && npm run dev` (usa `VITE_API_BASE` para el gateway, por defecto http://localhost:8088).

## Endpoints principales
- Gateway: `POST /api/chat` (body `{message}`) -> orquestador; `POST /api/upload` (multipart `file`) -> RAG; `GET /api/uploads` (lista con paginacion offset/limit); `GET /api/chat/logs`; `POST /api/search` -> RAG; `GET /metrics` (Prometheus).
- Orquestador: `POST /chat` -> OpenAI/stub; `GET /chat/logs` (offset/limit); `GET /metrics`.
- RAG: `POST /upload` (guarda fichero y metadata en Postgres; indexa en Qdrant y embeddings si se habilita); `GET /uploads` (offset/limit); `POST /search` (vectorial si hay Qdrant+OpenAI, fallback LIKE); `GET /metrics`.

## Tests
- Cada servicio Python incluye `tests/` con validaciones basicas de health/contratos iniciales.
- Ejemplo: `cd backend/gateway && pip install -r requirements.txt && pytest`
- Guia ampliada en `docs/TESTING.md`.

## Notas
- Logging persiste en `/app/logs/app.log` (volumenes mapeados en docker-compose para gateway/orquestador/RAG). Formato actual: textual.
- Embeddings: contenido indexado con OpenAI/Qdrant si `ENABLE_CONTENT_EMBED=1`; ajustar `CHUNK_SIZE_CHARS`/`MAX_CHUNKS` para controlar coste.
- Reindexado: dentro del contenedor RAG puedes reindexar nombre + contenido existentes con  
  `docker compose -f infra/docker/docker-compose.yml --profile core --profile app exec -T rag-server python -c "import sys; sys.path.append('/app'); import app.reindex as r; r.reindex()"`.
- MCP y agentes externos especificos siguen en desarrollo.
