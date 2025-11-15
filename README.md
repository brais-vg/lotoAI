# lotoAI
Plataforma modular de servicios de IA. Este repo contiene el esqueleto inicial de carpetas para cada componente descrito en la arquitectura.

## Arquitectura general
- Cliente web y app movil que hablan solo con el backend via HTTPS.
- Reverse proxy (Traefik/Nginx) para TLS, routing y reglas de seguridad.
- Backend BFF / API Gateway: autenticacion/autorizacion, sesiones, APIs, orquestacion basica y persistencia en PostgreSQL.
- Capa de IA: agente orquestador que consulta RAG, delega a agentes externos y ejecuta herramientas via MCP.
- Agentes externos: modelos especializados (GPT 5.1, Sonnet, Codex, Grok u otros segun el rol).
- Sistema MCP: cliente interno y servidor que expone herramientas (scripts, scraping, APIs, sistemas legacy).
- RAG: pipeline de ingesta, vector store y servicio de busqueda semantica.
- Datos: PostgreSQL, ClickHouse para analitica y MinIO/S3 para ficheros y backups.
- Observabilidad: logs, metricas y trazas con stack Prometheus/Grafana/Loki/Tempo.
- Mensajeria / event bus: Kafka, NATS o RabbitMQ para eventos y tareas.
- Autenticacion: Keycloak u otro proveedor OIDC/OAuth2.
- Contenedores: pensado para Docker y migrable a Kubernetes.

## Estructura de carpetas
```
+-- backend/                  # Backend BFF / API gateway
¦   +-- gateway/
+-- docs/                     # Documentacion y diagramas
+-- frontend/                 # Web y mobile
¦   +-- mobile/
¦   +-- web/
+-- infra/                    # Infraestructura base (proxy, DB, observabilidad, auth, mensajeria)
¦   +-- auth/
¦   +-- databases/
¦   ¦   +-- clickhouse/
¦   ¦   +-- postgres/
¦   +-- messaging/
¦   +-- observability/
¦   ¦   +-- logs/
¦   ¦   +-- metrics/
¦   ¦   +-- traces/
¦   +-- reverse-proxy/
¦   +-- storage/
¦   +-- docker/               # Docker compose y plantillas locales
+-- scripts/                  # Utilidades de desarrollo/ops
+-- services/                 # Servicios de IA y RAG
    +-- agent-orchestrator/
    +-- agents-external/
    +-- mcp/
    ¦   +-- client/
    ¦   +-- server/
    +-- rag/
        +-- ingestion/
        +-- server/
        +-- vector-store/
```

## Flujo de alto nivel
1. Cliente -> Reverse Proxy -> Backend.
2. Backend valida auth y envia peticiones al agente orquestador.
3. El orquestador decide si usar RAG, un agente externo o herramientas via MCP y arma la respuesta.
4. La respuesta vuelve al Backend y luego al cliente; logs, metricas y trazas se reportan en observabilidad; procesos asincronos pasan por mensajeria.

## Primeros pasos sugeridos
1. Definir stack por servicio (p.ej. gateway con FastAPI/NestJS/Spring; web con Next.js).
2. Completar las Dockerfile y pipelines de CI para cada servicio bajo `infra/docker`.
3. Rellenar `.env` a partir de `.env.example` y ajustar secretos.
4. Anadir diagramas en `docs/` y ADR breves para decisiones tecnicas.
5. Desarrollar el agente orquestador y los conectores RAG/MCP antes de exponer APIs publicas.
