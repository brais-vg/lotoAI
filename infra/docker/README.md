# Docker local

`docker-compose.yml` define servicios base usando perfiles:
- core: postgres, qdrant, nats, minio
- observability: prometheus, grafana
- edge: traefik
- analytics: clickhouse

Ejemplos:
- docker compose --profile core up -d
- docker compose --profile core --profile observability up -d
- docker compose --profile edge up -d
