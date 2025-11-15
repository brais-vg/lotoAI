# Docker local

`docker-compose.yml` define servicios base usando perfiles:
- core: postgres, qdrant, nats, minio
- observability: prometheus, grafana
- edge: traefik
- analytics: clickhouse
- app: gateway, agente orquestador, rag-server, mcp-server (build local)

Ejemplos:
- docker compose --profile core up -d
- docker compose --profile core --profile observability up -d
- docker compose --profile core --profile app up -d gateway agent-orchestrator rag-server mcp-server
- docker compose --profile edge up -d
