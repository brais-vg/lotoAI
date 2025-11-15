# MCP (Model Context Protocol)

Implementacion del cliente MCP usado por el orquestador y el servidor MCP que expone herramientas.

- client/: adaptadores para llamar a herramientas MCP.
- server/: registros de herramientas (scripts, scraping, APIs internas).

Stack actual:
- Servidor FastAPI stub en `server/app/main.py`.
- Cliente httpx stub en `client/client.py`.

Como levantar en local:
- `cd services/mcp/server && uvicorn app.main:app --host 0.0.0.0 --port 8081 --reload`
- Docker: `cd infra/docker && docker compose --profile app build mcp-server && docker compose --profile app up mcp-server`

Pendientes:
- Definir catalogo inicial de herramientas.
- Establecer autenticacion/autorizacion para llamadas MCP.
