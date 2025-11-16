# Vite/React client

Cliente React sencillo (Vite) para chat, búsqueda, uploads y logs consumiendo el gateway.

## Uso
```
cd frontend/vite-app
npm install
# opcional: export VITE_API_BASE=http://localhost:8088
npm run dev   # abre en http://localhost:5173
npm run build # build de producción
```

## Notas
- Usa fetch hacia el gateway; por defecto `VITE_API_BASE` es `http://localhost:8088`.
- Mantiene paginación básica (offset) para uploads y logs, y muestra resultados de búsqueda con score/chunk si existen.
