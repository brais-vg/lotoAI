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
    assert body["message"] == "orchestration stub"
    assert body["input"] == payload
