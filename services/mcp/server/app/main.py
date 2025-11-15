from fastapi import FastAPI

app = FastAPI(title="lotoAI MCP Server", version="0.1.0")

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.get("/tools")
async def list_tools() -> dict:
    # TODO: exponer catálogo real de herramientas MCP
    return {"tools": []}
