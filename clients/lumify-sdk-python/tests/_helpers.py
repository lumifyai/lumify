"""Shared test helpers: an injectable fake transport (the Python analog of the
TS suite's ``fakeFetch``) that records outbound requests and returns canned
responses in order."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from lumify import Lumify
from lumify._transport import PreparedRequest, RawResponse


class FakeTransport:
    """Records each :class:`PreparedRequest` and returns canned responses in
    sequence. Each canned entry is a dict with optional keys:
    ``status`` (default 200), ``headers`` (default ``{}``), and ``body``
    (a dict → JSON-encoded, or a raw string used verbatim)."""

    def __init__(self, responses: List[Dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: List[PreparedRequest] = []

    def __call__(self, req: PreparedRequest, timeout: float) -> RawResponse:
        self.calls.append(req)
        if not self._responses:
            raise AssertionError("FakeTransport ran out of canned responses")
        spec = self._responses.pop(0)
        body = spec.get("body", {})
        text = body if isinstance(body, str) else json.dumps(body)
        return RawResponse(
            status=spec.get("status", 200),
            headers=spec.get("headers", {}),
            text=text,
        )


class RaisingTransport:
    """A transport that raises a given exception (e.g. ConnectionError) for the
    first ``fail_times`` calls, then delegates to a fallback canned response."""

    def __init__(self, exc: BaseException, fail_times: int, then: Dict[str, Any]) -> None:
        self._exc = exc
        self._fail_times = fail_times
        self._then = then
        self.calls: List[PreparedRequest] = []

    def __call__(self, req: PreparedRequest, timeout: float) -> RawResponse:
        self.calls.append(req)
        if len(self.calls) <= self._fail_times:
            raise self._exc
        body = self._then.get("body", {})
        text = body if isinstance(body, str) else json.dumps(body)
        return RawResponse(
            status=self._then.get("status", 200),
            headers=self._then.get("headers", {}),
            text=text,
        )


def make_client(
    responses: List[Dict[str, Any]],
    *,
    max_retries: int = 0,
    **kwargs: Any,
) -> Lumify:
    transport = FakeTransport(responses)
    client = Lumify(api_key="lmfy-test", transport=transport, max_retries=max_retries, **kwargs)
    # Expose the transport for assertions.
    client._transport_spy = transport  # type: ignore[attr-defined]
    return client


def only_call(client: Lumify) -> PreparedRequest:
    spy: FakeTransport = client._transport_spy  # type: ignore[attr-defined]
    assert len(spy.calls) == 1, "expected exactly one request, got %d" % len(spy.calls)
    return spy.calls[0]
