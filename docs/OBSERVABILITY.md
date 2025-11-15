# Observabilidad y métricas

- Cada servicio FastAPI expone `GET /metrics` en formato Prometheus (gateway, agent-orchestrator, rag-server).
- Contadores principales:
  - Gateway: `lotoai_gateway_chat_total`, `lotoai_gateway_upload_total`, `lotoai_gateway_search_total`, `lotoai_gateway_logs_total`.
  - Orquestador: `lotoai_orchestrator_chat_total` (por proveedor), `lotoai_orchestrator_logs_total`.
  - RAG: `lotoai_rag_uploads_total`, `lotoai_rag_embeddings_total` (por tipo), `lotoai_rag_search_total` (vector/like).
- Logs por defecto en texto en `/app/logs/app.log` (montados como volumen en Docker). Ajusta `LOG_PATH` si es necesario.
- Para consumir métricas en local: `curl http://localhost:8088/metrics` (gateway) o el puerto correspondiente del servicio.
