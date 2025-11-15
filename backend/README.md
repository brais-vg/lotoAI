# Backend / Gateway

Responsabilidades:
- Autenticacion y autorizacion (OIDC) y gestion de sesiones.
- Exposicion de APIs BFF adaptadas al frontend.
- Orquestacion basica hacia IA, RAG y MCP.
- Persistencia en PostgreSQL y cache cuando aplique.
- Observabilidad: health checks, metrics y trazas.

Proximos pasos:
- Elegir framework (FastAPI/NestJS/Spring) y crear plantilla.
- Definir contrato con agente orquestador y RAG server.
- Modelar esquema inicial en PostgreSQL y migraciones.
