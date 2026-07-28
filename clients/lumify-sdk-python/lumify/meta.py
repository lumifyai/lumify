"""
Parses the response headers documented in the API's "Response headers" table
(``X-RateLimit-*``, ``X-Credits-*``) into a typed object attached to every
successful SDK response.

Because resource methods return the parsed JSON body directly (e.g. a
``SportsListResponse`` dict) for ergonomics — not a ``{data, meta}`` wrapper —
response metadata is attached out-of-band on a ``dict`` subclass and read back
with :func:`get_meta`. It never appears in ``json.dumps`` / iteration / ``**``
spreads, so it can't leak into logs or persisted data. (This mirrors the TS
SDK, which hides the same metadata behind a non-enumerable Symbol.)
"""

from __future__ import annotations

from typing import Any, Mapping, Optional


class ResponseMeta:
    """Credit and rate-limit metadata parsed from a response's headers."""

    __slots__ = (
        "rate_limit_limit",
        "rate_limit_remaining",
        "rate_limit_reset",
        "credits_used",
        "credits_remaining",
        "headers",
    )

    def __init__(
        self,
        *,
        rate_limit_limit: Optional[int] = None,
        rate_limit_remaining: Optional[int] = None,
        rate_limit_reset: Optional[int] = None,
        credits_used: Optional[int] = None,
        credits_remaining: Optional[int] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        #: Max requests allowed in the current rate-limit window.
        self.rate_limit_limit = rate_limit_limit
        #: Requests remaining in the current window.
        self.rate_limit_remaining = rate_limit_remaining
        #: Unix timestamp (seconds) when the window resets.
        self.rate_limit_reset = rate_limit_reset
        #: Credits charged for this call (0 for unavailable-data reads).
        self.credits_used = credits_used
        #: Best-effort remaining balance; omitted for unmetered plans.
        self.credits_remaining = credits_remaining
        #: The raw (case-insensitive) header mapping, for anything not above.
        self.headers = _CaseInsensitiveHeaders(headers or {})

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            "ResponseMeta(credits_used=%r, credits_remaining=%r, "
            "rate_limit_remaining=%r, rate_limit_reset=%r)"
            % (
                self.credits_used,
                self.credits_remaining,
                self.rate_limit_remaining,
                self.rate_limit_reset,
            )
        )


class _CaseInsensitiveHeaders(Mapping):
    """A read-only, case-insensitive view over a header mapping."""

    def __init__(self, source: Mapping[str, str]) -> None:
        self._store = {str(k).lower(): v for k, v in dict(source).items()}

    def __getitem__(self, key: str) -> str:
        return self._store[str(key).lower()]

    def __iter__(self):
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def get(self, key: str, default: Any = None) -> Any:  # type: ignore[override]
        return self._store.get(str(key).lower(), default)


def _num(headers: Mapping[str, str], name: str) -> Optional[int]:
    view = headers if isinstance(headers, _CaseInsensitiveHeaders) else _CaseInsensitiveHeaders(headers)
    raw = view.get(name)
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None


def parse_meta(headers: Mapping[str, str]) -> ResponseMeta:
    return ResponseMeta(
        rate_limit_limit=_num(headers, "x-ratelimit-limit"),
        rate_limit_remaining=_num(headers, "x-ratelimit-remaining"),
        rate_limit_reset=_num(headers, "x-ratelimit-reset"),
        credits_used=_num(headers, "x-credits-used"),
        credits_remaining=_num(headers, "x-credits-remaining"),
        headers=headers,
    )


# Attribute name used to stash meta on a returned dict subclass instance.
_META_ATTR = "_lumify_response_meta"


class APIObject(dict):
    """A ``dict`` that also carries out-of-band :class:`ResponseMeta`.

    Behaves exactly like ``dict`` for all key access / iteration / serialization
    — the attached meta lives on an instance attribute, not a key.
    """


def attach_meta(value: Any, meta: ResponseMeta) -> Any:
    """Wrap a parsed dict body so its :class:`ResponseMeta` is readable via
    :func:`get_meta`. Non-dict bodies are returned unchanged."""
    if isinstance(value, dict) and not isinstance(value, APIObject):
        value = APIObject(value)
    if isinstance(value, APIObject):
        setattr(value, _META_ATTR, meta)
    return value


def get_meta(value: Any) -> Optional[ResponseMeta]:
    """Read the :class:`ResponseMeta` attached to a value returned by an SDK call."""
    return getattr(value, _META_ATTR, None)
