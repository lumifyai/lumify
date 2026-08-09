from urllib.parse import parse_qs, urlparse

import pytest

import lumify._transport as transport_mod
from lumify import ConnectionError, Lumify, NotFoundError, RateLimitError, get_meta
from lumify.errors import APIError

from ._helpers import FakeTransport, RaisingTransport, make_client, only_call


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Never actually sleep during backoff in tests."""
    monkeypatch.setattr(transport_mod.time, "sleep", lambda _s: None)


def test_requires_api_key():
    with pytest.raises(ValueError):
        Lumify(api_key="")


def test_builds_url_with_auth_headers_and_query():
    client = make_client([{"body": {"ok": True}}])
    client.events.list(sport="nhl", limit=2, include_scores=True, status=None)
    req = only_call(client)

    parsed = urlparse(req.url)
    assert parsed.path == "/v1/events"
    q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    # None is dropped; bool serialized lowercase.
    assert q == {"sport": "nhl", "limit": "2", "include_scores": "true"}
    assert req.headers["Authorization"] == "Bearer lmfy-test"
    assert req.headers["Accept"] == "application/json"
    assert req.headers["User-Agent"].startswith("lumify-sdk-python/")


def test_success_attaches_meta():
    client = make_client([{"body": {"event_id": 1, "available": False}, "headers": {"X-Credits-Used": "0"}}])
    odds = client.events.odds(1)
    assert odds["available"] is False
    meta = get_meta(odds)
    assert meta is not None and meta.credits_used == 0


def test_error_envelope_raises_typed_error():
    client = make_client(
        [{"status": 404, "body": {"error": {"code": "not_found", "message": "nope", "status": 404}}}]
    )
    with pytest.raises(NotFoundError) as ei:
        client.teams.get(999999999)
    assert ei.value.code == "not_found"
    assert ei.value.status == 404


def test_invalid_json_success_raises_api_error():
    client = make_client([{"status": 200, "body": "<html>not json</html>"}])
    with pytest.raises(APIError) as ei:
        client.sports.list()
    assert ei.value.code == "invalid_response"


def test_get_retries_on_500_then_succeeds():
    transport = FakeTransport(
        [
            {"status": 500, "body": {"error": {"code": "server_error", "message": "boom", "status": 500}}},
            {"status": 200, "body": {"sports": [], "total": 0}},
        ]
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=2)
    result = client.sports.list()
    assert result["total"] == 0
    assert len(transport.calls) == 2


def test_get_retries_on_429_honoring_retry_after():
    transport = FakeTransport(
        [
            {"status": 429, "body": {"error": {"code": "rate_limited", "message": "slow", "status": 429, "retry_after": 0}}},
            {"status": 200, "body": {"sports": [], "total": 0}},
        ]
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=1)
    result = client.sports.list()
    assert result["total"] == 0
    assert len(transport.calls) == 2


def test_get_gives_up_after_max_retries():
    transport = FakeTransport(
        [{"status": 503, "body": {"error": {"code": "unavailable", "message": "down", "status": 503}}}] * 3
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(APIError):
        client.sports.list()
    assert len(transport.calls) == 3  # 1 + 2 retries


def test_post_is_not_retried():
    transport = FakeTransport(
        [{"status": 500, "body": {"error": {"code": "server_error", "message": "boom", "status": 500}}}] * 3
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(APIError):
        client.agent.credits.topup(1)
    assert len(transport.calls) == 1  # POST never retried


def test_connection_error_retried_then_raised():
    transport = RaisingTransport(
        ConnectionError("network down"), fail_times=5, then={"body": {}}
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=2)
    with pytest.raises(ConnectionError):
        client.sports.list()
    assert len(transport.calls) == 3


def test_connection_error_recovers_within_retries():
    transport = RaisingTransport(
        ConnectionError("blip"), fail_times=1, then={"status": 200, "body": {"total": 0}}
    )
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=2)
    result = client.sports.list()
    assert result["total"] == 0
    assert len(transport.calls) == 2
