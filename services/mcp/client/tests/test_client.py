import httpx
import pytest

from client import list_tools


def test_list_tools_uses_httpx(monkeypatch):
    called = {}

    def fake_get(url, timeout):
        called["url"] = url
        return httpx.Response(200, json={"tools": ["t1"]}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    result = list_tools("http://fake-server")
    assert result == {"tools": ["t1"]}
    assert called["url"] == "http://fake-server/tools"


def test_list_tools_raises_on_error(monkeypatch):
    def fake_get(url, timeout):
        return httpx.Response(500, json={"error": "fail"}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", fake_get)

    with pytest.raises(httpx.HTTPStatusError):
        list_tools("http://fake-server")
