"""Stub de ingesta para RAG.
Carga documentos y los envia a Qdrant. Completar con embeddings reales.
"""

from qdrant_client import QdrantClient


def ingest(documents: list[str], collection: str = "lotoai") -> None:
    client = QdrantClient(host="qdrant", port=6333)
    # TODO: vectorizar documentos y upsert en Qdrant
    print(f"Ingest {len(documents)} docs into {collection} (stub)")


if __name__ == "__main__":
    ingest(["demo document"], collection="lotoai")
