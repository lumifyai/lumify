import pytest

from lumify.aio import AsyncLumify, parse_async_sse_stream

from ._async_helpers import AsyncFakeTransport


def _chunks(text, size=7):
    data = text.encode("utf-8")
    return [data[i : i + size] for i in range(0, len(data), size)]


async def _achunks(text, size=7):
    for chunk in _chunks(text, size):
        yield chunk


async def test_parse_async_sse_stream_named_events_and_keepalive():
    stream = (
        ": keep-alive\n\n"
        "event: score\n"
        'data: {"event_id": 1, "status": "inprogress"}\n\n'
        "event: done\n"
        'data: {"event_id": 1}\n\n'
    )
    frames = [f async for f in parse_async_sse_stream(_achunks(stream))]
    assert [f.event for f in frames] == ["score", "done"]
    assert '"status": "inprogress"' in frames[0].data


async def test_parse_async_sse_stream_multiline_data_joined():
    stream = "event: score\ndata: line1\ndata: line2\n\n"
    frames = [f async for f in parse_async_sse_stream(_achunks(stream, size=3))]
    assert len(frames) == 1
    assert frames[0].data == "line1\nline2"


class _FakeStreamResponse:
    def __init__(self, text, status_code=200):
        self._text = text
        self.status_code = status_code
        self.headers = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def aiter_bytes(self):
        for chunk in _chunks(self._text):
            yield chunk

    async def aread(self):
        return self._text.encode("utf-8")


class _FakeAsyncHTTPClient:
    def __init__(self, response: _FakeStreamResponse):
        self._response = response
        self.calls = 0
        self.last_timeout = None

    def stream(self, method, url, *, headers=None, timeout=None):
        self.calls += 1
        self.last_timeout = timeout
        return self._response


class _QueuedFakeAsyncHTTPClient:
    """Returns a fresh response from the queue on each `.stream()` call —
    for testing that reconnect opens a genuinely new connection."""

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.calls = 0
        self.last_timeout = None

    def stream(self, method, url, *, headers=None, timeout=None):
        self.calls += 1
        self.last_timeout = timeout
        return self._responses[self.calls - 1]


async def test_astream_scores_decodes_events():
    stream = (
        ": keep-alive\n\n"
        'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
        'event: done\ndata: {"event_id": 3}\n\n'
    )
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]))
    client._client._http_client = _FakeAsyncHTTPClient(_FakeStreamResponse(stream))

    events = [e async for e in client.events.stream(3)]
    assert [e.event for e in events] == ["score", "done"]
    assert events[0].data["status"] == "inprogress"
    assert events[1].data["event_id"] == 3


async def test_astream_scores_skips_malformed_json():
    stream = "event: score\ndata: not-json\n\nevent: done\ndata: {}\n\n"
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]))
    client._client._http_client = _FakeAsyncHTTPClient(_FakeStreamResponse(stream))

    events = [e async for e in client.events.stream(3)]
    assert [e.event for e in events] == ["done"]


async def test_astream_scores_reconnects_transparently_on_reconnect_event():
    first = (
        'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
        'event: reconnect\ndata: {"event_id": 3, "reason": "max_stream_duration", "max_seconds": 300}\n\n'
    )
    second = (
        'event: score\ndata: {"event_id": 3, "status": "inprogress", "clock": "9:00"}\n\n'
        'event: done\ndata: {"event_id": 3}\n\n'
    )
    fake_http = _QueuedFakeAsyncHTTPClient([_FakeStreamResponse(first), _FakeStreamResponse(second)])
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]))
    client._client._http_client = fake_http

    events = [e async for e in client.events.stream(3)]

    assert fake_http.calls == 2, "expected a second connection after the reconnect signal"
    assert [e.event for e in events] == ["score", "reconnect", "score", "done"]
    assert events[2].data["clock"] == "9:00"


async def test_astream_scores_does_not_loop_forever_without_reconnect_signal():
    stream = 'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
    fake_http = _QueuedFakeAsyncHTTPClient([_FakeStreamResponse(stream)])
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]))
    client._client._http_client = fake_http

    events = [e async for e in client.events.stream(3)]

    assert fake_http.calls == 1, "must not attempt a reconnect on a plain stream end"
    assert [e.event for e in events] == ["score"]


async def test_astream_scores_raises_typed_error_on_http_error():
    import json

    from lumify import NotFoundError

    body = json.dumps({"error": {"code": "not_found", "message": "nope", "status": 404}})
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]))
    client._client._http_client = _FakeAsyncHTTPClient(_FakeStreamResponse(body, status_code=404))

    with pytest.raises(NotFoundError):
        async for _ in client.events.stream(999999999):
            pass


async def test_astream_scores_enforces_keepalive_read_floor():
    import httpx

    from lumify.sse import _KEEPALIVE_FLOOR

    stream = 'event: done\ndata: {"event_id": 3}\n\n'
    fake_http = _FakeAsyncHTTPClient(_FakeStreamResponse(stream))
    client = AsyncLumify(api_key="lmfy-test", transport=AsyncFakeTransport([]), timeout=5.0)
    client._client._http_client = fake_http

    _ = [e async for e in client.events.stream(3)]

    assert isinstance(fake_http.last_timeout, httpx.Timeout)
    assert fake_http.last_timeout.read == _KEEPALIVE_FLOOR
    assert fake_http.last_timeout.connect == 5.0
