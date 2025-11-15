# RAG

Componentes:
- ingestion/: pipeline para tokenizacion, chunking y embeddings.
- vector-store/: almacenamiento en Qdrant (u otro) y mantenimiento de indices.
- server/: servicio de consulta semantica que devuelve contexto al orquestador.

Stack actual:
- Servidor FastAPI en `server/app/main.py` con endpoints:
  - `/health`
  - `/upload` (guarda ficheros en disco y metadata en Postgres)
  - `/search` (stub)
- Script de ingesta stub en `ingestion/ingest.py` usando Qdrant client.

Como levantar en local:
- `cd services/rag/server && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Docker: `cd infra/docker && docker compose --profile app build rag-server && docker compose --profile app up rag-server`

Pendientes:
- Elegir modelo de embeddings y estrategia de chunking.
- Definir esquema de metadatos y versionado de datasets.
- Anadir tareas batch para reindexar o purgar colecciones.
