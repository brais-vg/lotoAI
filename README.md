# lotoAI
Plataforma modular de servicios de IA. Este repo contiene el esqueleto inicial y un piloto básico funcional (chat + subida de ficheros a RAG).

## Arquitectura general
- Cliente web responsive (sin login) que consume el gateway.
- Gateway/BFF (FastAPI) para orquestar chat y subida de ficheros.
- Agente orquestador (FastAPI) que usa OpenAI API (fallback stub si no hay API key).
- RAG server (FastAPI) que almacena ficheros en disco y registra metadata en Postgres.
- Dependencias: Postgres, Qdrant, NATS, MinIO (via Docker compose). MCP y agentes externos quedan pendientes.

## Estructura de carpetas
```
backend/                  # Gateway/API BFF
frontend/web/             # Web estática responsive para chat + subida
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

## Cómo levantar el piloto (local)
1. Copia `.env.example` a `.env` y rellena `OPENAI_API_KEY` si quieres respuestas reales.
2. Levanta dependencias y app: `cd infra/docker && docker compose --profile core --profile app up -d --build`
   - Web: http://localhost:3000
   - Gateway API: http://localhost:8088
   - Orquestador: http://localhost:8090
   - RAG: http://localhost:8000
3. Si no pones API key, el chat devolverá un stub. El upload requiere Postgres levantado (perfil core).

## Endpoints principales
- Gateway: `POST /api/chat` (body `{message}`) -> orquestador; `POST /api/upload` (multipart `file`) -> RAG.
- Orquestador: `POST /chat` -> OpenAI
- RAG: `POST /upload` -> guarda fichero en `/app/data/uploads` y metadata en Postgres; `POST /search` stub

## Tests
- Cada servicio Python incluye `tests/` con validaciones básicas de health/contratos iniciales.
- Ejemplo: `cd backend/gateway && pip install -r requirements.txt && pytest`
- Guía ampliada en `docs/TESTING.md`.

## Notas
- Logging persiste en `/app/logs/app.log` (volúmenes mapeados en docker-compose para gateway/orquestador/RAG).
- MCP y agentes externos específicos quedan en desarrollo.
