# RAG

Componentes:
- ingestion/: pipeline para tokenizacion, chunking y embeddings.
- vector-store/: almacenamiento en Qdrant (u otro) y mantenimiento de indices.
- server/: servicio de consulta semantica que devuelve contexto al orquestador.

Pendientes:
- Elegir modelo de embeddings y estrategia de chunking.
- Definir esquema de metadatos y versionado de datasets.
- Anadir tareas batch para reindexar o purgar colecciones.
