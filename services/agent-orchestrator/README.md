# Agente orquestador

Se encarga de recibir peticiones del backend y decidir:
- Si consulta contexto en RAG.
- Si delega en un agente/modelo externo especializado.
- Si ejecuta herramientas via MCP.
- Como ensamblar y devolver la respuesta final.

Ideas:
- Mantener memoria conversacional con storage externo.
- Politicas de enrutado configurables.
- Observabilidad con spans por decision tomada.

Stack actual:
- FastAPI + Uvicorn (stub en `app/main.py`).

Como levantar en local:
- Python: `cd services/agent-orchestrator && uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload`
- Docker: `cd infra/docker && docker compose --profile app build agent-orchestrator && docker compose --profile app up agent-orchestrator`

Pendientes:
- Elegir modelo de embeddings y estrategia de chunking.
- Definir esquema de metadatos y versionado de datasets.
- Anadir tareas batch para reindexar o purgar colecciones.

Tests:
- Ejecutar: `cd services/agent-orchestrator && pytest`
- Pruebas actuales: health check y stub de `/orchestrate` (aseguran contrato minimo mientras se implementa la logica real).
