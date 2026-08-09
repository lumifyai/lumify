from lumify.errors import (
    APIError,
    AuthenticationError,
    NotFoundError,
    PaymentError,
    PermissionError,
    RateLimitError,
    ValidationError,
    error_from_response,
)


def test_status_maps_to_subclass():
    cases = {
        401: AuthenticationError,
        402: PaymentError,
        403: PermissionError,
        404: NotFoundError,
        422: ValidationError,
        429: RateLimitError,
        500: APIError,
        503: APIError,
        418: APIError,
    }
    for status, cls in cases.items():
        err = error_from_response(status, {"code": "x", "message": "m", "status": status}, None)
        assert isinstance(err, cls), "%d -> %s" % (status, cls.__name__)
        assert err.status == status


def test_falls_back_to_synthetic_code_and_message():
    err = error_from_response(500, None, "req-1")
    assert err.code == "http_500"
    assert "500" in err.message
    assert err.request_id == "req-1"


def test_rate_limit_prefers_envelope_over_header():
    err = error_from_response(
        429, {"code": "rate_limited", "message": "slow down", "retry_after": 12}, None, retry_after_header=99
    )
    assert isinstance(err, RateLimitError)
    assert err.retry_after == 12


def test_rate_limit_falls_back_to_header():
    err = error_from_response(429, {"code": "rate_limited", "message": "slow"}, None, retry_after_header=7)
    assert err.retry_after == 7


def test_validation_error_exposes_field_errors():
    payload = {
        "code": "validation_error",
        "message": "bad",
        "errors": [{"field": "limit", "message": "too big", "type": "value_error"}],
    }
    err = error_from_response(422, payload, None)
    assert isinstance(err, ValidationError)
    assert len(err.field_errors) == 1
    assert err.field_errors[0].field == "limit"
    assert err.field_errors[0].type == "value_error"


def test_permission_error_exposes_upgrade_url():
    payload = {"code": "forbidden", "message": "nope", "upgrade_url": "https://lumify.ai/pricing"}
    err = error_from_response(403, payload, None)
    assert isinstance(err, PermissionError)
    assert err.upgrade_url == "https://lumify.ai/pricing"


def test_payment_error_exposes_upgrade_and_topup_urls():
    payload = {
        "code": "insufficient_credits",
        "message": "top up",
        "upgrade_url": "https://lumify.ai/pricing",
        "topup_url": "https://lumify.ai/dashboard",
    }
    err = error_from_response(402, payload, None)
    assert isinstance(err, PaymentError)
    assert err.upgrade_url == "https://lumify.ai/pricing"
    assert err.topup_url == "https://lumify.ai/dashboard"
