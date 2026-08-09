"""
Verifies the ``Lumify-Signature`` header webhook deliveries carry (see
core/webhooks/delivery.py's ``_sign``):

    Lumify-Signature: t=<unix_ts>,v1=<hex hmac_sha256(signing_secret, `${ts}.${body}`)>

Uses stdlib ``hmac``/``hashlib`` — no dependencies. Mirrors the TS SDK's
``verifyWebhook`` (which uses Web Crypto).
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Callable, Optional, Tuple


class WebhookSignatureError(Exception):
    """Raised when a webhook signature is malformed, mismatched, or stale."""


def _parse_signature_header(header: str) -> Tuple[int, str]:
    parts = {}
    for segment in header.split(","):
        key, sep, value = segment.partition("=")
        if sep and value != "":
            parts[key.strip()] = value.strip()
    t = parts.get("t")
    v1 = parts.get("v1")
    if not t or not v1:
        raise WebhookSignatureError(
            "Malformed Lumify-Signature header — expected 't=<unix_ts>,v1=<hex_hmac>'."
        )
    try:
        timestamp = int(float(t))
    except (TypeError, ValueError):
        raise WebhookSignatureError(
            "Malformed Lumify-Signature header — 't' is not a number."
        )
    return timestamp, v1


def verify_webhook(
    signing_secret: str,
    signature_header: str,
    raw_body: str,
    *,
    tolerance_seconds: int = 300,
    now: Optional[Callable[[], float]] = None,
) -> None:
    """Verify a delivery's ``Lumify-Signature`` header against the raw request
    body and your subscription's ``signing_secret``.

    Raises :class:`WebhookSignatureError` on any failure (bad format, mismatch,
    stale timestamp) — treat that as "reject the delivery with a 4xx", not a
    crash.

    ``raw_body`` must be the *raw, unparsed* request body — re-serializing
    parsed JSON can reorder keys or change whitespace and break the signature.
    """
    timestamp, signature = _parse_signature_header(signature_header)

    now_val = (now or time.time)()
    if abs(now_val - timestamp) > tolerance_seconds:
        raise WebhookSignatureError(
            "Signature timestamp is %ds old, outside the %ds tolerance "
            "(possible replay)." % (round(abs(now_val - timestamp)), tolerance_seconds)
        )

    expected = hmac.new(
        signing_secret.encode("utf-8"),
        ("%d.%s" % (timestamp, raw_body)).encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise WebhookSignatureError(
            "Signature mismatch — payload may have been tampered with, or the "
            "signing secret is wrong."
        )
