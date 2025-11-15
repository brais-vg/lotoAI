# lotoAI
Proyecto LotoAI

# Arquitectura General

Este documento describe la arquitectura completa de un sistema modular
orientado a IA, compuesto por múltiples servicios independientes y
coordinados. El objetivo es ofrecer una plataforma web con chat
inteligente, herramientas integradas, capacidades RAG, agentes
especializados, servicios MCP y sistemas de observabilidad fiables.

## 📐 Visión General

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