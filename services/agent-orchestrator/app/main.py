from fastapi import FastAPI

app = FastAPI(title="lotoAI Agent Orchestrator", version="0.1.0")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.post("/orchestrate")
async def orchestrate(payload: dict) -> dict:
    # TODO: implementar enrutado real hacia RAG, agentes externos y MCP
    return {"message": "orchestration stub", "input": payload}
