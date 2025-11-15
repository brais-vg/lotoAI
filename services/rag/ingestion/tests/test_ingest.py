import types

from ingest import ingest


def test_ingest_uses_qdrant_client(monkeypatch, capsys):
    created = {}

    class FakeClient:
        def __init__(self, host, port):
            created["host"] = host
            created["port"] = port

    monkeypatch.setattr("ingest.QdrantClient", FakeClient)

    ingest(["doc1", "doc2"], collection="demo")
    captured = capsys.readouterr()
    assert "Ingest 2 docs into demo" in captured.out
    assert created == {"host": "qdrant", "port": 6333}
