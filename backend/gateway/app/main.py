from fastapi import FastAPI

app = FastAPI(title="lotoAI Gateway", version="0.1.0")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.get("/info")
async def info() -> dict:
    return {
        "name": "lotoAI Gateway",
        "services": ["orchestrator", "rag", "mcp"],
        "auth": "oidc",
    }
