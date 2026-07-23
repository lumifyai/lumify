"""
Async HTTP transport for :class:`lumify.aio.AsyncLumify` — the 0.2.0
async/await counterpart to :class:`lumify._transport.LumifyClient`.

Unlike the sync client (zero-dependency stdlib ``urllib``), true concurrent
async I/O without a dependency means hand-rolling HTTP/1.1 + TLS framing,
which isn't worth the risk. This engine uses `httpx <https://www.python-httpx.org/>`_
instead — an optional dependency, installed with ``pip install
"lumify-sdk[asyncio]"``. Importing :mod:`lumify` (the sync client) never
requires it; only constructing an :class:`AsyncLumify` without a custom
``transport=`` does.

All the pure request/response logic (building the request, mapping errors,
deciding whether/how long to retry) is identical to the sync client and is
imported from :mod:`lumify._transport` rather than duplicated.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any, Awaitable, Callable, Dict, Mapping, Optional

from ._transport import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    SDK_VERSION,
    PreparedRequest,
    RawResponse,
    _build_query,
    _parse_retry_after,
    _safe_json,
    _UNPARSEABLE,
)
from .errors import ConnectionError, LumifyError, RateLimitError, error_from_response
from .meta import _CaseInsensitiveHeaders, attach_meta, parse_meta

try:
    import httpx
except ImportError as _import_error:  # pragma: no cover - exercised via _require_httpx
    httpx = None  # type: ignore[assignment]
    _HTTPX_IMPORT_ERROR: Optional[BaseException] = _import_error
else:
    _HTTPX_IMPORT_ERROR = None


# An async transport is any coroutine function (request, timeout_seconds) ->
# RawResponse. Like the sync Transport, it must return a RawResponse for any
# HTTP status and raise lumify.errors.ConnectionError only when no response
# was received at all.
AsyncTransport = Callable[[PreparedRequest, float], Awaitable[RawResponse]]


def _require_httpx() -> None:
    if httpx is None:
        raise ImportError(
            "AsyncLumify needs the optional `httpx` dependency for its default "
            "transport. Install it with `pip install \"lumify-sdk[asyncio]\"` "
            "(or `pip install httpx`), or pass your own `transport=`."
        ) from _HTTPX_IMPORT_ERROR


class AsyncLumifyClient:
    """The async transport underlying every ``lumify.aio`` resource. Not
    usually constructed directly — use :class:`lumify.aio.AsyncLumify`."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: Optional[AsyncTransport] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "Lumify SDK: `api_key` is required (create one at "
                "https://lumify.ai/api-keys)."
            )
        self._api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._custom_transport = transport
        if transport is None:
            _require_httpx()
        self._http_client: Optional["httpx.AsyncClient"] = None
        suffix = (" " + user_agent) if user_agent else ""
        self.user_agent = "lumify-sdk-python/%s%s (asyncio)" % (SDK_VERSION, suffix)

    def build_url(self, path: str, query: Optional[Mapping[str, Any]] = None) -> str:
        return "%s%s%s" % (self.base_url, path, _build_query(query))

    def auth_headers(self, accept: str = "application/json") -> Dict[str, str]:
        return {
            "Authorization": "Bearer %s" % self._api_key,
            "Accept": accept,
            "User-Agent": self.user_agent,
        }

    async def _ensure_http_client(self) -> "httpx.AsyncClient":
        if self._http_client is None:
            self._http_client = httpx.AsyncClient()
        return self._http_client

    async def _httpx_transport(self, req: PreparedRequest, timeout: float) -> RawResponse:
        client = await self._ensure_http_client()
        try:
            resp = await client.request(
                req.method,
                req.url,
                content=req.body.encode("utf-8") if req.body is not None else None,
                headers=req.headers,
                timeout=timeout,
            )
        except httpx.TimeoutException as exc:
            raise ConnectionError(
                "Request to %s %s timed out after %ss." % (req.method, req.url, timeout),
                cause=exc,
            )
        except httpx.HTTPError as exc:
            raise ConnectionError(
                "Request to %s %s failed: %s" % (req.method, req.url, exc), cause=exc
            )
        return RawResponse(status=resp.status_code, headers=dict(resp.headers), text=resp.text)

    async def aclose(self) -> None:
        """Close the pooled ``httpx.AsyncClient`` (a no-op with a custom
        ``transport=``). Safe to call multiple times."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    async def __aenter__(self) -> "AsyncLumifyClient":
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.aclose()

    async def get(self, path: str, *, query: Optional[Mapping[str, Any]] = None) -> Any:
        return await self.request("GET", path, query=query, idempotent=True)

    async def post(
        self,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
    ) -> Any:
        return await self.request("POST", path, query=query, body=body, idempotent=False)

    async def delete(self, path: str, *, query: Optional[Mapping[str, Any]] = None) -> Any:
        return await self.request("DELETE", path, query=query, idempotent=True)

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
        idempotent: Optional[bool] = None,
    ) -> Any:
        if idempotent is None:
            idempotent = method == "GET"
        attempts = max(1, self.max_retries + 1) if idempotent else 1

        prepared = self._prepare(method, path, query, body)
        transport = self._custom_transport or self._httpx_transport
        last_exc: Optional[LumifyError] = None

        for attempt in range(attempts):
            if attempt > 0:
                await asyncio.sleep(self._backoff(attempt, last_exc))
            try:
                raw = await transport(prepared, self.timeout)
                return self._process(method, path, raw)
            except LumifyError as exc:
                last_exc = exc
                if not (idempotent and self._should_retry(exc) and attempt < attempts - 1):
                    raise
        # Unreachable — the loop always returns or raises.
        assert last_exc is not None
        raise last_exc

    def _prepare(
        self, method: str, path: str, query: Optional[Mapping[str, Any]], body: Any
    ) -> PreparedRequest:
        headers = self.auth_headers()
        payload: Optional[str] = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            if isinstance(body, dict):
                body = {k: v for k, v in body.items() if v is not None}
            import json as _json

            payload = _json.dumps(body)
        return PreparedRequest(method, self.build_url(path, query), headers, payload)

    def _process(self, method: str, path: str, raw: RawResponse) -> Any:
        headers = _CaseInsensitiveHeaders(raw.headers)
        request_id = headers.get("x-request-id")
        parsed = _safe_json(raw.text) if raw.text else None
        parse_failed = bool(raw.text) and parsed is _UNPARSEABLE

        if not (200 <= raw.status < 300):
            payload = None
            if isinstance(parsed, dict):
                err = parsed.get("error")
                if isinstance(err, dict):
                    payload = err
            raise error_from_response(
                raw.status,
                payload,
                request_id,
                retry_after_header=_parse_retry_after(headers.get("retry-after")),
            )

        if parse_failed:
            from .errors import APIError

            raise APIError(
                "Response from %s %s was not valid JSON." % (method, path),
                status=raw.status,
                code="invalid_response",
                request_id=request_id,
            )

        return attach_meta(parsed, parse_meta(raw.headers))

    def _should_retry(self, exc: LumifyError) -> bool:
        if isinstance(exc, ConnectionError):
            return True
        return exc.status == 429 or exc.status >= 500

    def _backoff(self, attempt: int, last_exc: Optional[LumifyError]) -> float:
        if isinstance(last_exc, RateLimitError) and last_exc.retry_after is not None:
            if last_exc.retry_after >= 0:
                return float(last_exc.retry_after)
        base = 0.25 * (2 ** (attempt - 1))
        return base + random.random() * 0.1
