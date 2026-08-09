import json

from lumify.meta import APIObject, attach_meta, get_meta, parse_meta


def test_parse_meta_reads_headers_case_insensitively():
    meta = parse_meta(
        {
            "X-RateLimit-Limit": "100",
            "x-ratelimit-remaining": "97",
            "X-RateLimit-Reset": "1699999999",
            "X-Credits-Used": "1",
            "X-Credits-Remaining": "4999",
        }
    )
    assert meta.rate_limit_limit == 100
    assert meta.rate_limit_remaining == 97
    assert meta.rate_limit_reset == 1699999999
    assert meta.credits_used == 1
    assert meta.credits_remaining == 4999


def test_parse_meta_missing_headers_are_none():
    meta = parse_meta({})
    assert meta.credits_used is None
    assert meta.rate_limit_remaining is None


def test_attach_and_get_meta_is_hidden_from_serialization():
    body = {"sports": [{"id": 1}], "total": 1}
    meta = parse_meta({"X-Credits-Used": "0"})
    wrapped = attach_meta(body, meta)

    assert isinstance(wrapped, APIObject)
    assert wrapped["total"] == 1
    # Meta is out-of-band: not a key, invisible to json/iteration.
    assert "meta" not in wrapped
    assert "_lumify_response_meta" not in wrapped
    assert set(wrapped.keys()) == {"sports", "total"}
    assert json.loads(json.dumps(wrapped)) == body

    got = get_meta(wrapped)
    assert got is not None
    assert got.credits_used == 0


def test_get_meta_returns_none_for_plain_values():
    assert get_meta({"a": 1}) is None
    assert get_meta(None) is None
    assert get_meta([1, 2, 3]) is None
