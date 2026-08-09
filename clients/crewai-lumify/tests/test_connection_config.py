"""Offline unit tests for crewai-lumify.

These exercise MCP kwargs / auth hardening without requiring a network call.
``get_lumify_mcp`` is tested with ``_mcp_server_cls`` faked out so CI does not
need to load the full CrewAI runtime for unit coverage.
"""

from __future__ import annotations

import warnings

import crewai_lumify
import pytest
from crewai_lumify import (
    DEFAULT_MCP_URL,
    MissingApiKeyError,
    _mcp_kwargs,
    _normalize_api_key,
    get_lumify_mcp,
)


def test_default_url_and_version():
    assert DEFAULT_MCP_URL == "https://lumify.ai/mcp"
    assert isinstance(crewai_lumify.__version__, str)
    assert crewai_lumify.__version__


def test_explicit_key_sets_bearer_and_client_headers():
    kwargs = _mcp_kwargs("lmfy-abc.123", DEFAULT_MCP_URL)
    assert kwargs["url"] == DEFAULT_MCP_URL
    assert kwargs["streamable"] is True
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Bearer lmfy-abc.123"
    assert headers["User-Agent"].startswith("crewai-lumify/")
    assert headers["X-Lumify-Client"].startswith("crewai-lumify/")


def test_strips_leading_bearer_prefix():
    kwargs = _mcp_kwargs("Bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert kwargs["headers"]["Authorization"] == "Bearer lmfy-abc.123"


def test_strips_bearer_case_insensitive():
    kwargs = _mcp_kwargs("bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert kwargs["headers"]["Authorization"] == "Bearer lmfy-abc.123"


def test_whitespace_only_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _mcp_kwargs("   ", DEFAULT_MCP_URL)


def test_empty_string_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _mcp_kwargs("", DEFAULT_MCP_URL)


def test_env_key_fallback(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "lmfy-env.999")
    kwargs = _mcp_kwargs(None, DEFAULT_MCP_URL)
    assert kwargs["headers"]["Authorization"] == "Bearer lmfy-env.999"


def test_env_key_with_bearer_prefix_normalized(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "Bearer lmfy-env.999")
    kwargs = _mcp_kwargs(None, DEFAULT_MCP_URL)
    assert kwargs["headers"]["Authorization"] == "Bearer lmfy-env.999"


def test_require_api_key_default_raises_without_key(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="docs/ai"):
        _mcp_kwargs(None, DEFAULT_MCP_URL)


def test_require_api_key_false_allows_list_without_auth(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    kwargs = _mcp_kwargs(None, DEFAULT_MCP_URL, require_api_key=False)
    assert "Authorization" not in kwargs["headers"]
    assert kwargs["headers"]["User-Agent"].startswith("crewai-lumify/")


def test_custom_url_preserved(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    kwargs = _mcp_kwargs(
        None, "https://self-hosted.example/mcp", require_api_key=False
    )
    assert kwargs["url"] == "https://self-hosted.example/mcp"


def test_non_lmfy_prefix_warns_but_still_sends():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        kwargs = _mcp_kwargs("sk-not-a-lumify-key", DEFAULT_MCP_URL)
    assert kwargs["headers"]["Authorization"] == "Bearer sk-not-a-lumify-key"
    assert any(issubclass(w.category, UserWarning) for w in caught)
    assert any("lmfy-" in str(w.message) for w in caught)


def test_normalize_api_key_helpers():
    assert _normalize_api_key(None) is None
    assert _normalize_api_key("") is None
    assert _normalize_api_key("  ") is None
    assert _normalize_api_key("Bearer ") is None
    assert _normalize_api_key("  lmfy-x  ") == "lmfy-x"


def test_streamable_and_cache_flags():
    kwargs = _mcp_kwargs(
        "lmfy-x",
        DEFAULT_MCP_URL,
        streamable=False,
        cache_tools_list=True,
    )
    assert kwargs["streamable"] is False
    assert kwargs["cache_tools_list"] is True


def test_tool_filter_only_passed_when_set():
    kwargs = _mcp_kwargs("lmfy-x", DEFAULT_MCP_URL)
    assert "tool_filter" not in kwargs
    filt = object()
    kwargs = _mcp_kwargs("lmfy-x", DEFAULT_MCP_URL, tool_filter=filt)
    assert kwargs["tool_filter"] is filt


def test_get_lumify_mcp_never_constructs_server_without_key(monkeypatch):
    """Missing-key failure must happen before CrewAI MCPServerHTTP is built."""
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    constructed = {"count": 0}

    class _Boom:
        def __init__(self, *a, **kw):
            constructed["count"] += 1
            raise AssertionError("should not construct")

    monkeypatch.setattr(crewai_lumify, "_mcp_server_cls", lambda: _Boom)
    with pytest.raises(MissingApiKeyError):
        get_lumify_mcp()
    assert constructed["count"] == 0


def test_get_lumify_mcp_wires_kwargs(monkeypatch):
    constructed: dict = {}

    class _FakeHTTP:
        def __init__(self, **kwargs):
            constructed.update(kwargs)

    monkeypatch.setattr(crewai_lumify, "_mcp_server_cls", lambda: _FakeHTTP)
    result = get_lumify_mcp(api_key="lmfy-test.123")

    assert isinstance(result, _FakeHTTP)
    assert constructed["url"] == DEFAULT_MCP_URL
    assert constructed["headers"]["Authorization"] == "Bearer lmfy-test.123"
    assert constructed["streamable"] is True


def test_get_lumify_mcp_require_api_key_false_end_to_end(monkeypatch):
    """require_api_key=False should reach MCPServerHTTP without Authorization."""
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    constructed: dict = {}

    class _FakeHTTP:
        def __init__(self, **kwargs):
            constructed.update(kwargs)

    monkeypatch.setattr(crewai_lumify, "_mcp_server_cls", lambda: _FakeHTTP)
    result = get_lumify_mcp(require_api_key=False)

    assert isinstance(result, _FakeHTTP)
    assert "Authorization" not in constructed["headers"]


def test_get_lumify_mcp_forwards_tool_filter(monkeypatch):
    """tool_filter should reach MCPServerHTTP unchanged when set."""
    constructed: dict = {}

    class _FakeHTTP:
        def __init__(self, **kwargs):
            constructed.update(kwargs)

    monkeypatch.setattr(crewai_lumify, "_mcp_server_cls", lambda: _FakeHTTP)
    filt = object()
    get_lumify_mcp(api_key="lmfy-test.123", tool_filter=filt)

    assert constructed["tool_filter"] is filt