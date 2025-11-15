# Servicios de IA

Contiene servicios de IA, agentes y RAG.

- agent-orchestrator/: agente principal que decide rutas.
- agents-external/: integraciones con modelos/LLM externos.
- mcp/: cliente y servidor MCP para exponer herramientas.
- rag/: pipeline de ingesta, vector store y servidor de busqueda.

Proximos pasos:
- Definir protocolo interno entre backend y orquestador (REST/gRPC/queue).
- Seleccionar SDKs para proveedores LLM y manejo de costes/limites.
- Establecer contratos RAG (payload de consulta, formato de contexto).
