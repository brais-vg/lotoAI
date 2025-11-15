import pytest


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


@pytest.mark.asyncio
async def test_search_stub_returns_empty_results(client):
    payload = {"text": "hello"}
    resp = await client.post("/search", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == payload["text"]
    assert "results" in body
    assert body["results"] == []


@pytest.mark.asyncio
async def test_list_uploads_returns_items_key(client):
    resp = await client.get("/uploads")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
