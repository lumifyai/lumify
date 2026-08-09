from urllib.parse import parse_qs, urlparse

import pytest

import lumify._async_transport as async_transport_mod
from lumify import ConnectionError, NotFoundError, get_meta
from lumify.aio import AsyncLumify
from lumify.errors import APIError

from ._async_helpers import AsyncFakeTransport, AsyncRaisingTransport, make_async_client, only_call


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Never actually sleep during backoff in tests."""

    async def _no_op_sleep(_seconds):
        return None

    monkeypatch.setattr(async_transport_mod.asyncio, "sleep", _no_op_sleep)


async def test_requires_api_key():
    with pytest.raises(ValueError):
        AsyncLumify(api_key="", transport=AsyncFakeTransport([]))


async def test_builds_url_with_auth_headers_and_query():
    client = make_async_client([{"body": {"ok": True}}])
    await client.events.list(sport="nhl", limit=2, include_scores=True, status=None)
    req = only_call(client)

    parsed = urlparse(req.url)
    assert parsed.path == "/v1/events"
    q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    assert q == {"sport": "nhl", "limit": "2", "include_scores": "true"}
    assert req.headers["Authorization"] == "Bearer lmfy-test"
    assert req.headers["Accept"] == "application/json"
    assert req.headers["User-Agent"].startswith("lumify-sdk-python/")
    assert "asyncio" in req.headers["User-Agent"]


async def test_success_attaches_meta():
    client = make_async_client(
        [{"body": {"event_id": 1, "available": False}, "headers": {"X-Credits-Used": "0"}}]
    )
    odds = await client.events.odds(1)
    assert odds["available"] is False
    meta = get_meta(odds)
    assert meta is not None and meta.credits_used == 0


async def test_error_envelope_raises_typed_error():
    client = make_async_client(
        [{"status": 404, "body": {"error": {"code": "not_found", "message": "nope", "status": 404}}}]
    )
    with pytest.raises(NotFoundError) as ei:
        await client.teams.get(999999999)
    assert ei.value.code == "not_found"
    assert ei.value.status == 404


async def test_invalid_json_success_raises_api_error():
    client = make_async_client([{"status": 200, "body": "<html>not json</html>"}])
    with pytest.raises(APIError) as ei:
        await client.sports.list()
    assert ei.value.code == "invalid_response"


async def test_get_retries_on_500_then_succeeds():
    transport = AsyncFakeTransport(
        [
            {"status": 500, "body": {"error": {"code": "server_error", "message": "boom", "status": 500}}},
            {"status": 200, "body": {"sports": [], "total": 0}},
        ]
    )
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=2)
    result = await client.sports.list()
    assert result["total"] == 0
    assert len(transport.calls) == 2


async def test_get_gives_up_after_max_retries():
    transport = AsyncFakeTransport(
        [{"status": 503, "body": {"error": {"code": "unavailable", "message": "down", "status": 503}}}] * 3
    )
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(APIError):
        await client.sports.list()
    assert len(transport.calls) == 3  # 1 + 2 retries


async def test_post_is_not_retried():
    transport = AsyncFakeTransport(
        [{"status": 500, "body": {"error": {"code": "server_error", "message": "boom", "status": 500}}}] * 3
    )
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(APIError):
        await client.agent.credits.topup(1)
    assert len(transport.calls) == 1  # POST never retried


async def test_connection_error_retried_then_raised():
    transport = AsyncRaisingTransport(ConnectionError("network down"), fail_times=5, then={"body": {}})
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(ConnectionError):
        await client.sports.list()
    assert len(transport.calls) == 3


async def test_connection_error_recovers_within_retries():
    transport = AsyncRaisingTransport(
        ConnectionError("blip"), fail_times=1, then={"status": 200, "body": {"total": 0}}
    )
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=2)
    result = await client.sports.list()
    assert result["total"] == 0
    assert len(transport.calls) == 2


async def test_context_manager_closes_pooled_client():
    async with AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([])) as client:
        assert isinstance(client, AsyncLumify)
    # Closing a client with a custom transport (no pooled httpx client) is a no-op.
    await client.aclose()


def test_missing_httpx_raises_helpful_error_without_transport(monkeypatch):
    monkeypatch.setattr(async_transport_mod, "httpx", None)
    with pytest.raises(ImportError, match="asyncio"):
        AsyncLumify(api_key="lmfy-test")
