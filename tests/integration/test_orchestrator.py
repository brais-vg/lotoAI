import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_orchestrate_echoes_payload(client):
    payload = {"text": "hola"}
    resp = await client.post("/orchestrate", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert "orchestration stub" in body["message"]
    assert body["input"] in (payload["text"], payload)
    assert body.get("provider") in ("stub", "openai")


@pytest.mark.asyncio
async def test_chat_logs_endpoint(client):
    resp = await client.get("/chat/logs")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
