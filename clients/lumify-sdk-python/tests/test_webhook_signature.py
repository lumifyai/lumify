import hashlib
import hmac

import pytest

from lumify.webhook_signature import WebhookSignatureError, verify_webhook

SECRET = "whsec_test_secret"
BODY = '{"event":"score","event_id":1}'


def _sign(secret, timestamp, body):
    return hmac.new(
        secret.encode("utf-8"), ("%d.%s" % (timestamp, body)).encode("utf-8"), hashlib.sha256
    ).hexdigest()


def test_valid_signature_passes():
    ts = 1_700_000_000
    sig = _sign(SECRET, ts, BODY)
    header = "t=%d,v1=%s" % (ts, sig)
    verify_webhook(SECRET, header, BODY, now=lambda: ts + 10)  # no raise


def test_signature_mismatch_raises():
    ts = 1_700_000_000
    header = "t=%d,v1=%s" % (ts, "deadbeef" * 8)
    with pytest.raises(WebhookSignatureError):
        verify_webhook(SECRET, header, BODY, now=lambda: ts + 10)


def test_tampered_body_raises():
    ts = 1_700_000_000
    sig = _sign(SECRET, ts, BODY)
    header = "t=%d,v1=%s" % (ts, sig)
    with pytest.raises(WebhookSignatureError):
        verify_webhook(SECRET, header, BODY + "tampered", now=lambda: ts + 10)


def test_stale_timestamp_raises():
    ts = 1_700_000_000
    sig = _sign(SECRET, ts, BODY)
    header = "t=%d,v1=%s" % (ts, sig)
    with pytest.raises(WebhookSignatureError):
        verify_webhook(SECRET, header, BODY, tolerance_seconds=300, now=lambda: ts + 3600)


def test_malformed_header_raises():
    with pytest.raises(WebhookSignatureError):
        verify_webhook(SECRET, "garbage", BODY, now=lambda: 1_700_000_000)
    with pytest.raises(WebhookSignatureError):
        verify_webhook(SECRET, "t=abc,v1=xx", BODY, now=lambda: 1_700_000_000)
