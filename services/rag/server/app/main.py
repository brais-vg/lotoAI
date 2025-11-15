from fastapi import FastAPI

app = FastAPI(title="lotoAI RAG Server", version="0.1.0")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/search")
async def search(query: dict) -> dict:
    # TODO: integrar con Qdrant y embeddings
    return {"query": query.get("text", ""), "results": []}
