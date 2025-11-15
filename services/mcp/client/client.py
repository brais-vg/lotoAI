"""Cliente MCP stub.
Aqui se implementaran las llamadas al servidor MCP y manejo de herramientas.
"""

import httpx


def list_tools(base_url: str = "http://mcp-server:8081") -> dict:
    response = httpx.get(f"{base_url}/tools", timeout=5)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print(list_tools())
