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
frontend/web/             # Web estatica responsive para chat + subida
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

## Endpoints principales
- Gateway: `POST /api/chat` (body `{message}`) -> orquestador; `POST /api/upload` (multipart `file`) -> RAG.
- Orquestador: `POST /chat` -> OpenAI
- RAG: `POST /upload` -> guarda fichero en `/app/data/uploads` y metadata en Postgres; `POST /search` stub

## Tests
- Cada servicio Python incluye `tests/` con validaciones basicas de health/contratos iniciales.
- Ejemplo: `cd backend/gateway && pip install -r requirements.txt && pytest`
- Guia ampliada en `docs/TESTING.md`.

## Notas
- Logging persiste en `/app/logs/app.log` (volumenes mapeados en docker-compose para gateway/orquestador/RAG).
- MCP y agentes externos especificos quedan en desarrollo.
