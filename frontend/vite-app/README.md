# Vite/React (borrador)

Objetivo: migrar la web estática a un cliente con estado (React/Vite) para soporte de streaming, paginación y UX richer.

Propuesta mínima:
- Crear el proyecto con `npm create vite@latest web-vite -- --template react`.
- Configurar `VITE_API_BASE` para apuntar al gateway (por defecto `http://localhost:8088`).
- Replicar vistas actuales (chat, búsqueda, uploads, logs) usando hooks y fetch.
- Añadir componentes para:
  - chat streaming en vez de poll
  - formularios controlados y estados de error/carga
  - paginación (offset/limit) en uploads y logs

No se incluye código aún para evitar duplicar la web estática; este README actúa como guía de migración rápida.
