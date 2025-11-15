# Backend / Gateway

Responsabilidades:
- Autenticacion y autorizacion (OIDC) y gestion de sesiones.
- Exposicion de APIs BFF adaptadas al frontend.
- Orquestacion basica hacia IA, RAG y MCP.
- Persistencia en PostgreSQL y cache cuando aplique.
- Observabilidad: health checks, metrics y trazas.

Stack actual:
- FastAPI + Uvicorn (stub en `gateway/app/main.py`).

Como levantar en local:
- Python: `cd backend/gateway && uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload`
- Docker: `cd infra/docker && docker compose --profile app build gateway && docker compose --profile app up gateway`

Proximos pasos:
- Definir contrato con agente orquestador y RAG server.
- Modelar esquema inicial en PostgreSQL y migraciones.

Tests:
- Ejecutar: `cd backend/gateway && pytest`
- Cobertura actual: `/health` y `/info`.
