"""
Server-Sent Events reader for ``GET /v1/events/{id}/stream`` (see
api/routes/v1/stream.py). The endpoint emits named events — ``score`` on
change, ``done`` when the event finishes, ``error`` if the id doesn't exist —
plus unnamed ``: keep-alive`` comment pings every ~15s.

This parses the wire format directly off the HTTP response body (stdlib
``urllib``); it does not use any EventSource abstraction, so it can send the
``Authorization`` header the API requires. Mirrors the TS SDK's sse.ts.
"""

from __future__ import annotations

import codecs
import json
import socket
import urllib.error
import urllib.request
from typing import Any, Iterable, Iterator, Optional

from .errors import ConnectionError, error_from_response

_KEEPALIVE_FLOOR = 60.0  # keep the read timeout above the server's ~15s pings


class SSEEvent:
    """A single parsed SSE frame."""

    __slots__ = ("event", "data", "id")

    def __init__(self, event: str, data: str, id: Optional[str] = None) -> None:  # noqa: A002
        #: The ``event:`` field (defaults to "message" per the SSE spec).
        self.event = event
        #: Raw ``data:`` field, joined across multiline data.
        self.data = data
        self.id = id


class ScoreStreamEvent:
    """A decoded live-score stream event: ``event`` is one of
    ``"score"`` | ``"done"`` | ``"error"`` | ``"reconnect"``; ``data`` is the
    parsed JSON. ``"reconnect"`` is handled transparently by
    :func:`stream_scores` / :func:`lumify.aio.sse.astream_scores` (they
    reconnect and keep yielding) — it's surfaced here only for visibility."""

    __slots__ = ("event", "data")

    def __init__(self, event: str, data: Any) -> None:
        self.event = event
        self.data = data

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "ScoreStreamEvent(event=%r, data=%r)" % (self.event, self.data)


def _parse_frame(raw: str) -> Optional[SSEEvent]:
    data_lines = []
    event = "message"
    ident: Optional[str] = None
    comment_only = True

    for line in raw.split("\n"):
        if line.startswith(":"):
            continue  # comment / keep-alive
        comment_only = False
        if line.startswith("event:"):
            event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            data_lines.append(line[len("data:"):].lstrip())
        elif line.startswith("id:"):
            ident = line[len("id:"):].strip()

    if comment_only and not data_lines:
        return None
    return SSEEvent(event=event, data="\n".join(data_lines), id=ident)


def parse_sse_stream(chunks: Iterable[bytes]) -> Iterator[SSEEvent]:
    """Parse a ``text/event-stream`` byte stream into individual SSE frames.

    Exposed for advanced use and testing; most callers want
    :func:`stream_scores`.
    """
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    for chunk in chunks:
        if not chunk:
            continue
        buffer += decoder.decode(chunk)
        buffer = buffer.replace("\r\n", "\n").replace("\r", "\n")
        while "\n\n" in buffer:
            raw, buffer = buffer.split("\n\n", 1)
            frame = _parse_frame(raw)
            if frame is not None:
                yield frame

    tail = buffer + decoder.decode(b"", final=True)
    tail = tail.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if tail:
        frame = _parse_frame(tail)
        if frame is not None:
            yield frame


def _iter_bytes(fp: Any, size: int = 1024) -> Iterator[bytes]:
    while True:
        chunk = fp.read(size)
        if not chunk:
            break
        yield chunk


def _connect(client: Any, event_id: int, connect_timeout: Optional[float]):
    url = client.build_url("/v1/events/%d/stream" % event_id)

    base = client.timeout if connect_timeout is None else connect_timeout
    if base == 0:
        read_timeout: Optional[float] = None
    else:
        read_timeout = max(float(base), _KEEPALIVE_FLOOR)

    request = urllib.request.Request(
        url, headers=client.auth_headers("text/event-stream"), method="GET"
    )
    try:
        return urllib.request.urlopen(request, timeout=read_timeout)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        payload = None
        try:
            doc = json.loads(body)
            if isinstance(doc, dict) and isinstance(doc.get("error"), dict):
                payload = doc["error"]
        except ValueError:
            pass
        request_id = exc.headers.get("x-request-id") if exc.headers else None
        raise error_from_response(exc.code, payload, request_id)
    except (socket.timeout, TimeoutError) as exc:
        raise ConnectionError(
            "SSE connect to /v1/events/%d/stream timed out." % event_id, cause=exc
        )
    except urllib.error.URLError as exc:
        raise ConnectionError(
            "SSE connect to /v1/events/%d/stream failed: %s"
            % (event_id, getattr(exc, "reason", exc)),
            cause=exc,
        )


def stream_scores(
    client: Any,
    event_id: int,
    *,
    connect_timeout: Optional[float] = None,
) -> Iterator[ScoreStreamEvent]:
    """Iterate live score updates for an event over SSE. Emits only on change
    (plus a final ``done``), so it's far cheaper than polling the score endpoint.

    The server caps a single connection at 5 minutes and sends an
    ``event: reconnect`` frame just before closing it for that reason (as
    opposed to ``event: done``, which means the game actually finished). This
    reconnects automatically and keeps yielding, so a long game's stream looks
    continuous to the caller — the ``reconnect`` event is still yielded for
    visibility/telemetry, but no action is required in response to it.

    Note (sync/zero-dep tradeoff vs. the TS SDK): stdlib ``urllib`` applies one
    socket timeout to the whole request, so the read timeout is held above the
    server's keep-alive interval rather than being connect-only. Pass
    ``connect_timeout=0`` to disable the timeout entirely.
    """
    while True:
        resp = _connect(client, event_id, connect_timeout)
        reconnecting = False
        with resp:
            for frame in parse_sse_stream(_iter_bytes(resp)):
                if frame.event == "message" and not frame.data:
                    continue  # keep-alive with no named event
                try:
                    data = json.loads(frame.data) if frame.data else None
                except ValueError:
                    continue  # malformed frame — skip rather than raise mid-stream
                yield ScoreStreamEvent(event=frame.event, data=data)
                if frame.event == "reconnect":
                    reconnecting = True
                    break  # tear this connection down below, then loop to reconnect
                if frame.event in ("done", "error"):
                    return
        if not reconnecting:
            return  # stream ended without an explicit reconnect signal
