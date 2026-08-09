"""
Async counterpart to :mod:`lumify.sse` for ``GET /v1/events/{id}/stream``.
Uses ``httpx.AsyncClient.stream()`` so callers can ``async for`` live score
updates without blocking the event loop, instead of the sync client's
one-socket-timeout ``urllib`` reader.

The wire-format parser (:func:`lumify.sse._parse_frame`) is shared with the
sync SSE reader — only the transport loop differs.
"""

from __future__ import annotations

import codecs
import json
from typing import Any, AsyncIterable, AsyncIterator, Optional

from ..errors import ConnectionError, error_from_response
from ..sse import ScoreStreamEvent, SSEEvent, _KEEPALIVE_FLOOR, _parse_frame

try:
    import httpx
except ImportError:  # pragma: no cover - guarded by AsyncLumifyClient at construction
    httpx = None  # type: ignore[assignment]


async def parse_async_sse_stream(chunks: AsyncIterable[bytes]) -> AsyncIterator[SSEEvent]:
    """Async-generator counterpart to :func:`lumify.sse.parse_sse_stream`."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    buffer = ""
    async for chunk in chunks:
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


async def astream_scores(
    client: Any,
    event_id: int,
    *,
    connect_timeout: Optional[float] = None,
) -> AsyncIterator[ScoreStreamEvent]:
    """Async counterpart to :func:`lumify.sse.stream_scores` — iterate live
    score updates for an event over SSE without blocking the event loop.
    Emits only on change (plus a final ``done``).

    The server caps a single connection at 5 minutes and sends an
    ``event: reconnect`` frame just before closing it for that reason (as
    opposed to ``event: done``, which means the game actually finished). This
    reconnects automatically and keeps yielding, so a long game's stream looks
    continuous to the caller — the ``reconnect`` event is still yielded for
    visibility/telemetry, but no action is required in response to it.
    """
    if httpx is None:  # pragma: no cover - AsyncLumifyClient already requires httpx
        raise ImportError("astream_scores() requires the optional `httpx` dependency.")

    url = client.build_url("/v1/events/%d/stream" % event_id)
    # Mirror sync stream_scores: keep the read timeout above the server's
    # ~15s keep-alive pings so a healthy idle stream isn't aborted. Connect
    # still uses the caller's timeout (or client default). Built only after
    # the httpx import guard above.
    base = client.timeout if connect_timeout is None else connect_timeout
    if base == 0:
        timeout = httpx.Timeout(None)
    else:
        connect = float(base)
        read = max(connect, _KEEPALIVE_FLOOR)
        timeout = httpx.Timeout(connect=connect, read=read, write=read, pool=connect)
    headers = client.auth_headers("text/event-stream")
    http_client = await client._ensure_http_client()

    while True:
        reconnecting = False
        try:
            async with http_client.stream("GET", url, headers=headers, timeout=timeout) as resp:
                if resp.status_code >= 400:
                    body = await resp.aread()
                    payload = None
                    try:
                        doc = json.loads(body.decode("utf-8", "replace"))
                        if isinstance(doc, dict) and isinstance(doc.get("error"), dict):
                            payload = doc["error"]
                    except ValueError:
                        pass
                    request_id = resp.headers.get("x-request-id")
                    raise error_from_response(resp.status_code, payload, request_id)

                async for frame in parse_async_sse_stream(resp.aiter_bytes()):
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
        except httpx.TimeoutException as exc:
            raise ConnectionError(
                "SSE connect to /v1/events/%d/stream timed out." % event_id, cause=exc
            )
        except httpx.HTTPError as exc:
            raise ConnectionError(
                "SSE connect to /v1/events/%d/stream failed: %s" % (event_id, exc), cause=exc
            )
        if not reconnecting:
            return  # stream ended without an explicit reconnect signal
