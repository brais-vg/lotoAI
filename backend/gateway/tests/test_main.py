import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_info(client):
    resp = await client.get("/info")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("name") == "lotoAI Gateway"
    assert "orchestrator" in body.get("services", [])
