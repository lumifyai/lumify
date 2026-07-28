import lumify.sse as sse_mod
from lumify import Lumify
from lumify.sse import parse_sse_stream, stream_scores


def _chunks(text, size=7):
    data = text.encode("utf-8")
    return [data[i : i + size] for i in range(0, len(data), size)]


def test_parse_sse_stream_named_events_and_keepalive():
    stream = (
        ": keep-alive\n\n"
        "event: score\n"
        'data: {"event_id": 1, "status": "inprogress"}\n\n'
        "event: done\n"
        'data: {"event_id": 1}\n\n'
    )
    frames = list(parse_sse_stream(_chunks(stream)))
    # keep-alive comment produces no frame
    assert [f.event for f in frames] == ["score", "done"]
    assert '"status": "inprogress"' in frames[0].data


def test_parse_sse_stream_multiline_data_joined():
    stream = "event: score\ndata: line1\ndata: line2\n\n"
    frames = list(parse_sse_stream(_chunks(stream, size=3)))
    assert len(frames) == 1
    assert frames[0].data == "line1\nline2"


def test_parse_sse_stream_handles_crlf():
    stream = "event: done\r\ndata: {}\r\n\r\n"
    frames = list(parse_sse_stream(_chunks(stream)))
    assert len(frames) == 1
    assert frames[0].event == "done"


class _FakeResponse:
    def __init__(self, text):
        self._data = text.encode("utf-8")
        self._pos = 0

    def read(self, size=-1):
        if size is None or size < 0:
            chunk = self._data[self._pos :]
            self._pos = len(self._data)
            return chunk
        chunk = self._data[self._pos : self._pos + size]
        self._pos += size
        return chunk

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_stream_scores_decodes_events(monkeypatch):
    stream = (
        ": keep-alive\n\n"
        'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
        'event: done\ndata: {"event_id": 3}\n\n'
    )
    monkeypatch.setattr(
        sse_mod.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse(stream)
    )
    client = Lumify(api_key="lmfy-test", base_url="http://localhost:9999")
    events = list(stream_scores(client._client, 3))
    assert [e.event for e in events] == ["score", "done"]
    assert events[0].data["status"] == "inprogress"
    assert events[1].data["event_id"] == 3


def test_stream_scores_skips_malformed_json(monkeypatch):
    stream = "event: score\ndata: not-json\n\nevent: done\ndata: {}\n\n"
    monkeypatch.setattr(
        sse_mod.urllib.request, "urlopen", lambda req, timeout=None: _FakeResponse(stream)
    )
    client = Lumify(api_key="lmfy-test", base_url="http://localhost:9999")
    events = list(stream_scores(client._client, 3))
    # malformed score frame skipped; done still delivered
    assert [e.event for e in events] == ["done"]


def test_stream_scores_reconnects_transparently_on_reconnect_event(monkeypatch):
    streams = [
        (
            'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
            'event: reconnect\ndata: {"event_id": 3, "reason": "max_stream_duration", "max_seconds": 300}\n\n'
        ),
        (
            'event: score\ndata: {"event_id": 3, "status": "inprogress", "clock": "9:00"}\n\n'
            'event: done\ndata: {"event_id": 3}\n\n'
        ),
    ]
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        return _FakeResponse(streams[len(calls) - 1])

    monkeypatch.setattr(sse_mod.urllib.request, "urlopen", fake_urlopen)
    client = Lumify(api_key="lmfy-test", base_url="http://localhost:9999")
    events = list(stream_scores(client._client, 3))

    assert len(calls) == 2, "expected a second connection after the reconnect signal"
    assert [e.event for e in events] == ["score", "reconnect", "score", "done"]
    assert events[2].data["clock"] == "9:00"


def test_stream_scores_does_not_loop_forever_without_reconnect_signal(monkeypatch):
    stream = 'event: score\ndata: {"event_id": 3, "status": "inprogress"}\n\n'
    calls = []

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        return _FakeResponse(stream)

    monkeypatch.setattr(sse_mod.urllib.request, "urlopen", fake_urlopen)
    client = Lumify(api_key="lmfy-test", base_url="http://localhost:9999")
    events = list(stream_scores(client._client, 3))

    assert len(calls) == 1, "must not attempt a reconnect on a plain stream end"
    assert [e.event for e in events] == ["score"]
