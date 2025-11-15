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
�   +-- gateway/
+-- docs/                     # Documentacion y diagramas
+-- frontend/                 # Web y mobile
�   +-- mobile/
�   +-- web/
+-- infra/                    # Infraestructura base (proxy, DB, observabilidad, auth, mensajeria)
�   +-- auth/
�   +-- databases/
�   �   +-- clickhouse/
�   �   +-- postgres/
�   +-- messaging/
�   +-- observability/
�   �   +-- logs/
�   �   +-- metrics/
�   �   +-- traces/
�   +-- reverse-proxy/
�   +-- storage/
�   +-- docker/               # Docker compose y plantillas locales
+-- scripts/                  # Utilidades de desarrollo/ops
+-- services/                 # Servicios de IA y RAG
    +-- agent-orchestrator/
    +-- agents-external/
    +-- mcp/
    �   +-- client/
    �   +-- server/
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

<<<<<<< HEAD
## Primeros pasos sugeridos
1. Definir stack por servicio (p.ej. gateway con FastAPI/NestJS/Spring; web con Next.js).
2. Completar las Dockerfile y pipelines de CI para cada servicio bajo `infra/docker`.
3. Rellenar `.env` a partir de `.env.example` y ajustar secretos.
4. Anadir diagramas en `docs/` y ADR breves para decisiones tecnicas.
5. Desarrollar el agente orquestador y los conectores RAG/MCP antes de exponer APIs publicas.
=======
El proyecto se estructura como un ecosistema de microservicios que
interactúan entre sí a través de un Backend principal que actúa como API
Gateway.

Los componentes incluyen:

-   Frontend Web y App móvil
-   Backend BFF / Gateway
-   Agente Principal de IA
-   Agentes secundarios externos
-   Sistema MCP (cliente/servidor)
-   RAG
-   Bases de datos
-   Observabilidad
-   Mensajería/Event bus
-   Reverse Proxy

## 📦 Componentes Principales

### 1. Cliente Web / Aplicación Móvil

Interfaz de usuario que interactúa exclusivamente con el Backend
mediante HTTPS.

### 2. Reverse Proxy (Traefik / Nginx)

-   Terminación TLS
-   Routing hacia el Backend
-   Reglas de seguridad y rate limiting

### 3. Backend Web (API Gateway / BFF)

Punto central del sistema encargado de: - Autenticación y autorización -
Gestión de sesiones - Exposición de APIs - Orquestación básica de
llamadas hacia agentes, RAG y MCP - Persistencia mediante PostgreSQL

## 🧠 Capa de Inteligencia Artificial

### 4. Agente Principal (Orquestador)

Servicio que procesa peticiones del Backend y decide: - Consultar RAG -
Delegar a agentes secundarios (modelos remotos) - Ejecutar herramientas
vía MCP - Ensamblar respuestas finales

### 5. Agentes Secundarios (Modelos Externos)

Modelos especializados accesibles por API: - GPT 5.1 - Sonnet - Codex /
Sonnet-code - Grok - Otros modelos dedicados según rol

## 🔧 MCP -- Model Context Protocol

### 6. Cliente MCP

Librería o servicio interno utilizado por el Agente Principal para
llamar a herramientas a través del servidor MCP.

### 7. Servidor MCP

Servidor que expone herramientas externas: - Scripts locales - Web
scraping - APIs internas/externas - Acceso a sistemas legacy -
Automatizaciones

## 📚 Sistema RAG (Retrieval-Augmented Generation)

### 8. Pipeline de Ingesta

Tokenización, chunking, embeddings y normalización.

### 9. Vector Store

DB vectorial (Qdrant, Milvus, Weaviate). Almacena y sirve embeddings.

### 10. RAG Server

Servicio que realiza búsquedas semánticas y devuelve contexto relevante
al Agente Principal.

## 🗄️ Persistencia

### 11. PostgreSQL

Base de datos principal.

### 12. ClickHouse

Base analítica para logs, métricas y grandes volúmenes.

### 13. Storage (MinIO - S3-like)

Almacenamiento de documentos, backups, datasets.

## 📊 Observabilidad

### 14. Logs

Loki + Promtail o sistema básico de ficheros.

### 15. Métricas

Prometheus + Grafana.

### 16. Trazas

Tempo o Jaeger.

## ✉️ Mensajería / Event Bus

Kafka / NATS / RabbitMQ para ingesta, tareas largas y eventos internos.

## 🔐 Autenticación

Keycloak u otro proveedor OIDC/OAuth2.

## 🗺️ Flujo General

1.  Cliente → Backend via Reverse Proxy
2.  Backend → Agente Principal
3.  Agente Principal:
    -   llama RAG
    -   llama modelos externos
    -   ejecuta herramientas MCP
4.  Respuesta → Backend → Cliente
5.  Logs, métricas y trazas gestionadas por observabilidad
6.  Sistema de mensajería maneja procesos asíncronos

## 🧩 Contenedores

Pensado para ejecutarse en Docker:
- Red interna
- Persistencia por volúmenes
- Servicios segmentados por tack
- Preparado para migrar a Kubernetes

## 🧱 Infraestructura

Provisional

  <img width="1536" height="1024" alt="infra" src="https://github.com/user-attachments/assets/11d18621-bb11-4219-a04a-aa4e90f84f0e" />
>>>>>>> 13b3d86b98e32495409333dda80208f4368cac3b
