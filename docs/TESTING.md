# Pruebas automatizadas

La suite de tests está dividida por servicio. Cada carpeta Python incluye `tests/` para validar healthchecks y contratos base.

## Cómo ejecutar
1) Ir al servicio y crear entorno virtual si aplica.
2) Instalar dependencias: `pip install -r requirements.txt`
3) Ejecutar pruebas: `pytest`

## Servicios cubiertos
- `backend/gateway`: endpoints `/health` y `/info`
- `services/agent-orchestrator`: health y stub `/orchestrate`
- `services/rag/server`: health y `/search` (el `/upload` requiere Postgres en marcha)
- `services/rag/ingestion`: stub de ingesta y cliente Qdrant
- `services/mcp/server`: health y `/tools`
- `services/mcp/client`: cliente httpx y manejo de errores
- `services/agents-external`: agente dummy de eco
