"""
Error taxonomy mirroring api/errors.py's unified envelope (and the TS SDK's
errors.ts):

    { "error": { "code", "message", "status", "doc_url", ...extra }, "detail" }

Agents should switch on ``err.code``, not parse ``err.message``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class LumifyError(Exception):
    """Base class for every error the SDK raises for a non-2xx API response."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str,
        doc_url: Optional[str] = None,
        request_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        #: Stable machine-readable slug, e.g. ``"not_found"`` — switch on this.
        self.code = code
        #: HTTP status code (0 for connection errors).
        self.status = status
        #: Link to the error-code reference docs, when the envelope carries one.
        self.doc_url = doc_url
        #: Value of the ``X-Request-Id`` response header, if present.
        self.request_id = request_id
        #: The full parsed ``error`` object from the response envelope.
        self.payload = payload or {}

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "%s(code=%r, status=%r, message=%r)" % (
            type(self).__name__,
            self.code,
            self.status,
            self.message,
        )


class AuthenticationError(LumifyError):
    """401 — missing/invalid API key."""


class PaymentError(LumifyError):
    """402 — credit top-up or payment method required."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        #: Present on credit/trial denials — where to upgrade the plan.
        self.upgrade_url: Optional[str] = self.payload.get("upgrade_url")
        #: Present on credit denials — dashboard top-up entry point.
        self.topup_url: Optional[str] = self.payload.get("topup_url")


class PermissionError(LumifyError):
    """403 — key lacks scope/plan for this resource."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        #: Present on sport-scope denials — where to upgrade the key's plan/scope.
        self.upgrade_url: Optional[str] = self.payload.get("upgrade_url")


class NotFoundError(LumifyError):
    """404 — resource does not exist."""


class FieldError:
    """One entry in a 422 validation error's ``errors`` list."""

    __slots__ = ("field", "message", "type")

    def __init__(self, field: str, message: str, type: str) -> None:  # noqa: A002
        self.field = field
        self.message = message
        self.type = type

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return "FieldError(field=%r, message=%r, type=%r)" % (
            self.field,
            self.message,
            self.type,
        )


class ValidationError(LumifyError):
    """422 — request failed server-side validation."""

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message, **kwargs)
        raw = self.payload.get("errors") or []
        self.field_errors: List[FieldError] = [
            FieldError(
                field=str(e.get("field", "")),
                message=str(e.get("message", "")),
                type=str(e.get("type", "")),
            )
            for e in raw
            if isinstance(e, dict)
        ]


class RateLimitError(LumifyError):
    """429 — rate limit exceeded."""

    def __init__(
        self, message: str, *, retry_after: Optional[float] = None, **kwargs: Any
    ) -> None:
        super().__init__(message, **kwargs)
        # Prefer the envelope field (canonical for Lumify), fall back to the header.
        from_payload = self.payload.get("retry_after")
        if isinstance(from_payload, (int, float)):
            self.retry_after: Optional[float] = float(from_payload)
        elif retry_after is not None:
            self.retry_after = float(retry_after)
        else:
            self.retry_after = None


class APIError(LumifyError):
    """5xx, or any status this SDK has no dedicated class for."""


class ConnectionError(LumifyError):
    """Network failure, timeout, or abort — the request never got a response."""

    def __init__(self, message: str, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(message, status=0, code="connection_error")
        self.__cause__ = cause


def error_from_response(
    status: int,
    payload: Optional[Dict[str, Any]],
    request_id: Optional[str],
    *,
    retry_after_header: Optional[float] = None,
) -> LumifyError:
    """Build the right LumifyError subclass from a parsed error envelope.

    Falls back to :class:`APIError` for unrecognized status codes.
    """
    payload = payload or None
    code = (payload or {}).get("code") or ("http_%d" % status)
    message = (payload or {}).get("message") or ("Request failed with status %d." % status)
    common = dict(
        status=status,
        code=code,
        doc_url=(payload or {}).get("doc_url"),
        request_id=request_id,
        payload=payload,
    )

    if status == 401:
        return AuthenticationError(message, **common)
    if status == 402:
        return PaymentError(message, **common)
    if status == 403:
        return PermissionError(message, **common)
    if status == 404:
        return NotFoundError(message, **common)
    if status == 422:
        return ValidationError(message, **common)
    if status == 429:
        return RateLimitError(message, retry_after=retry_after_header, **common)
    return APIError(message, **common)
