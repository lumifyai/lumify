"""
Low-level HTTP transport shared by every resource (mirrors the TS SDK's
client.ts). Zero dependencies — the default engine is stdlib ``urllib``.

The engine is injectable (``transport=``) so tests and non-standard runtimes
can supply their own, exactly like passing a custom ``fetch`` to the TS client.
This also keeps the door open to swapping in an async/``httpx`` engine later
without touching any resource code.
"""

from __future__ import annotations

import json as _json
import random
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Mapping, Optional

from .errors import ConnectionError, LumifyError, RateLimitError, error_from_response
from .meta import _CaseInsensitiveHeaders, attach_meta, parse_meta

DEFAULT_BASE_URL = "https://lumify.ai"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
SDK_VERSION = "0.2.0"


class PreparedRequest:
    """An immutable description of an outbound HTTP request."""

    __slots__ = ("method", "url", "headers", "body")

    def __init__(
        self, method: str, url: str, headers: Dict[str, str], body: Optional[str]
    ) -> None:
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body


class RawResponse:
    """The minimal response shape a transport must return."""

    __slots__ = ("status", "headers", "text")

    def __init__(self, status: int, headers: Mapping[str, str], text: str) -> None:
        self.status = status
        self.headers = headers
        self.text = text


# A transport is any callable (request, timeout_seconds) -> RawResponse. It must
# return a RawResponse for *any* HTTP status (including 4xx/5xx) and raise
# lumify.errors.ConnectionError only for transport-level failures (DNS, refused
# connection, timeout) where no response was received.
Transport = Callable[[PreparedRequest, float], RawResponse]


def _urllib_transport(req: PreparedRequest, timeout: float) -> RawResponse:
    request = urllib.request.Request(
        req.url,
        data=req.body.encode("utf-8") if req.body is not None else None,
        method=req.method,
    )
    for key, value in req.headers.items():
        request.add_header(key, value)

    try:
        resp = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        # A real HTTP response with a non-2xx status — read it and let the
        # client map it to a typed error (uniform with the success path).
        body = exc.read().decode("utf-8", "replace")
        headers = dict(exc.headers.items()) if exc.headers else {}
        return RawResponse(status=exc.code, headers=headers, text=body)
    except (socket.timeout, TimeoutError) as exc:
        raise ConnectionError(
            "Request to %s %s timed out after %ss." % (req.method, req.url, timeout),
            cause=exc,
        )
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, (socket.timeout, TimeoutError)):
            raise ConnectionError(
                "Request to %s %s timed out after %ss." % (req.method, req.url, timeout),
                cause=exc,
            )
        raise ConnectionError(
            "Request to %s %s failed: %s" % (req.method, req.url, reason),
            cause=exc,
        )

    with resp:
        body = resp.read().decode("utf-8", "replace")
        status = getattr(resp, "status", None) or resp.getcode()
        headers = dict(resp.headers.items()) if resp.headers else {}
    return RawResponse(status=int(status), headers=headers, text=body)


def _build_query(params: Optional[Mapping[str, Any]]) -> str:
    if not params:
        return ""
    from urllib.parse import urlencode

    pairs = []
    for key, value in params.items():
        if value is None:
            continue
        if isinstance(value, bool):
            # Match the REST/URLSearchParams contract: lowercase true/false,
            # not Python's "True"/"False".
            pairs.append((key, "true" if value else "false"))
        else:
            pairs.append((key, str(value)))
    if not pairs:
        return ""
    return "?" + urlencode(pairs)


def _safe_json(text: str) -> Any:
    try:
        return _json.loads(text)
    except ValueError:
        return _UNPARSEABLE


_UNPARSEABLE = object()


def _parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse ``Retry-After`` as integer seconds; ignore HTTP-date forms."""
    if value is None or value == "":
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    return seconds if seconds >= 0 else None


class LumifyClient:
    """The transport underlying every resource. Not usually constructed
    directly — use :class:`lumify.Lumify`."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: Optional[Transport] = None,
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
        self._transport: Transport = transport or _urllib_transport
        suffix = (" " + user_agent) if user_agent else ""
        self.user_agent = "lumify-sdk-python/%s%s" % (SDK_VERSION, suffix)

    def build_url(self, path: str, query: Optional[Mapping[str, Any]] = None) -> str:
        return "%s%s%s" % (self.base_url, path, _build_query(query))

    def auth_headers(self, accept: str = "application/json") -> Dict[str, str]:
        return {
            "Authorization": "Bearer %s" % self._api_key,
            "Accept": accept,
            "User-Agent": self.user_agent,
        }

    @property
    def transport(self) -> Transport:
        return self._transport

    def get(self, path: str, *, query: Optional[Mapping[str, Any]] = None) -> Any:
        return self.request("GET", path, query=query, idempotent=True)

    def post(
        self,
        path: str,
        *,
        query: Optional[Mapping[str, Any]] = None,
        body: Any = None,
    ) -> Any:
        return self.request("POST", path, query=query, body=body, idempotent=False)

    def delete(self, path: str, *, query: Optional[Mapping[str, Any]] = None) -> Any:
        return self.request("DELETE", path, query=query, idempotent=True)

    def request(
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
        last_exc: Optional[LumifyError] = None

        for attempt in range(attempts):
            if attempt > 0:
                time.sleep(self._backoff(attempt, last_exc))
            try:
                raw = self._transport(prepared, self.timeout)
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
            # Drop top-level None values, mirroring the TS SDK's
            # `JSON.stringify` (which silently omits `undefined`-valued keys)
            # — so optional params left unset never serialize as `null`.
            if isinstance(body, dict):
                body = {k: v for k, v in body.items() if v is not None}
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
