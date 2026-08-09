"""
lumify — official Python client for the Lumify agent-ready sports intelligence
API (schedules, live scores, odds, line movement, betting splits, and AI bet
intelligence). See https://lumify.ai/docs.

This SDK *is* the typed REST path — the same data as the REST API and the
``@lumifyai/mcp`` server, not a third implementation. Response models
(``lumify.models``) are generated from Lumify's live OpenAPI schema, so they
can't silently drift from what the API returns.
"""

from __future__ import annotations

from ._transport import DEFAULT_BASE_URL, LumifyClient
from .client import Lumify
from .errors import (
    APIError,
    AuthenticationError,
    ConnectionError,
    FieldError,
    LumifyError,
    NotFoundError,
    PaymentError,
    PermissionError,
    RateLimitError,
    ValidationError,
)
from .meta import ResponseMeta, get_meta
from .pagination import iterate_items, paginate
from .sse import ScoreStreamEvent, SSEEvent, parse_sse_stream, stream_scores
from .webhook_signature import WebhookSignatureError, verify_webhook

__version__ = "0.2.0"

__all__ = [
    "Lumify",
    "LumifyClient",
    "DEFAULT_BASE_URL",
    # errors
    "LumifyError",
    "AuthenticationError",
    "PermissionError",
    "NotFoundError",
    "RateLimitError",
    "ValidationError",
    "PaymentError",
    "APIError",
    "ConnectionError",
    "FieldError",
    # meta
    "ResponseMeta",
    "get_meta",
    # pagination
    "paginate",
    "iterate_items",
    # sse
    "stream_scores",
    "parse_sse_stream",
    "SSEEvent",
    "ScoreStreamEvent",
    # webhooks
    "verify_webhook",
    "WebhookSignatureError",
    "__version__",
]
