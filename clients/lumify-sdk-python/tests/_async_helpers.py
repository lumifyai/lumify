"""Async counterpart to ``_helpers.py`` — an injectable fake async transport
for testing :class:`lumify.aio.AsyncLumify` without a real httpx connection
(and without requiring httpx to be installed at all, since the fake
transport is passed as ``transport=`` and bypasses the httpx-backed
default)."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from lumify._async_transport import PreparedRequest, RawResponse
from lumify.aio import AsyncLumify


class AsyncFakeTransport:
    """Async analog of :class:`tests._helpers.FakeTransport`."""

    def __init__(self, responses: List[Dict[str, Any]]) -> None:
        self._responses = list(responses)
        self.calls: List[PreparedRequest] = []

    async def __call__(self, req: PreparedRequest, timeout: float) -> RawResponse:
        self.calls.append(req)
        if not self._responses:
            raise AssertionError("AsyncFakeTransport ran out of canned responses")
        spec = self._responses.pop(0)
        body = spec.get("body", {})
        text = body if isinstance(body, str) else json.dumps(body)
        return RawResponse(
            status=spec.get("status", 200),
            headers=spec.get("headers", {}),
            text=text,
        )


class AsyncRaisingTransport:
    """Async analog of :class:`tests._helpers.RaisingTransport`."""

    def __init__(self, exc: BaseException, fail_times: int, then: Dict[str, Any]) -> None:
        self._exc = exc
        self._fail_times = fail_times
        self._then = then
        self.calls: List[PreparedRequest] = []

    async def __call__(self, req: PreparedRequest, timeout: float) -> RawResponse:
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


def make_async_client(
    responses: List[Dict[str, Any]],
    *,
    max_retries: int = 0,
    **kwargs: Any,
) -> AsyncLumify:
    transport = AsyncFakeTransport(responses)
    client = AsyncLumify(api_key="lmfy-test", transport=transport, max_retries=max_retries, **kwargs)
    client._transport_spy = transport  # type: ignore[attr-defined]
    return client


def only_call(client: AsyncLumify) -> PreparedRequest:
    spy: AsyncFakeTransport = client._transport_spy  # type: ignore[attr-defined]
    assert len(spy.calls) == 1, "expected exactly one request, got %d" % len(spy.calls)
    return spy.calls[0]
