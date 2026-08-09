"""Offline unit tests for llamaindex-lumify.

These exercise client construction / auth hardening without touching the
network (the MCP session is only opened lazily on tool list/call).
"""

from __future__ import annotations

import inspect
import warnings

import llamaindex_lumify
import pytest
from llama_index.core.tools.function_tool import FunctionTool
from llamaindex_lumify import (
    DEFAULT_MCP_URL,
    DEFAULT_SSE_READ_TIMEOUT,
    DEFAULT_TIMEOUT,
    LumifyToolSpec,
    MissingApiKeyError,
    _build_client,
    _normalize_api_key,
    get_lumify_tools,
)


def test_default_url_and_version():
    assert DEFAULT_MCP_URL == "https://lumify.ai/mcp"
    assert isinstance(llamaindex_lumify.__version__, str)
    assert llamaindex_lumify.__version__


def test_explicit_key_sets_bearer_and_client_headers():
    client = _build_client("lmfy-abc.123", DEFAULT_MCP_URL)
    assert client.command_or_url == DEFAULT_MCP_URL
    headers = client.headers
    assert headers["Authorization"] == "Bearer lmfy-abc.123"
    assert headers["User-Agent"].startswith("llamaindex-lumify/")
    assert headers["X-Lumify-Client"].startswith("llamaindex-lumify/")
    assert client.timeout == DEFAULT_TIMEOUT
    assert client.sse_read_timeout == DEFAULT_SSE_READ_TIMEOUT


def test_custom_timeouts_passed_to_client():
    client = _build_client(
        "lmfy-abc.123",
        DEFAULT_MCP_URL,
        timeout=90,
        sse_read_timeout=600,
    )
    assert client.timeout == 90
    assert client.sse_read_timeout == 600


def test_strips_leading_bearer_prefix():
    client = _build_client("Bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert client.headers["Authorization"] == "Bearer lmfy-abc.123"


def test_strips_bearer_case_insensitive():
    client = _build_client("bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert client.headers["Authorization"] == "Bearer lmfy-abc.123"


def test_whitespace_only_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _build_client("   ", DEFAULT_MCP_URL)


def test_empty_string_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _build_client("", DEFAULT_MCP_URL)


def test_env_key_fallback(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "lmfy-env.999")
    client = _build_client(None, DEFAULT_MCP_URL)
    assert client.headers["Authorization"] == "Bearer lmfy-env.999"


def test_env_key_with_bearer_prefix_normalized(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "Bearer lmfy-env.999")
    client = _build_client(None, DEFAULT_MCP_URL)
    assert client.headers["Authorization"] == "Bearer lmfy-env.999"


def test_require_api_key_default_raises_without_key(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="docs/ai"):
        _build_client(None, DEFAULT_MCP_URL)


def test_require_api_key_false_allows_list_without_auth(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    client = _build_client(None, DEFAULT_MCP_URL, require_api_key=False)
    assert "Authorization" not in client.headers
    assert client.headers["User-Agent"].startswith("llamaindex-lumify/")


def test_custom_url_preserved(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    client = _build_client(
        None, "https://self-hosted.example/mcp", require_api_key=False
    )
    assert client.command_or_url == "https://self-hosted.example/mcp"


def test_non_lmfy_prefix_warns_but_still_sends():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        client = _build_client("sk-not-a-lumify-key", DEFAULT_MCP_URL)
    assert client.headers["Authorization"] == "Bearer sk-not-a-lumify-key"
    assert any(issubclass(w.category, UserWarning) for w in caught)
    assert any("lmfy-" in str(w.message) for w in caught)


def test_normalize_api_key_helpers():
    assert _normalize_api_key(None) is None
    assert _normalize_api_key("") is None
    assert _normalize_api_key("  ") is None
    assert _normalize_api_key("Bearer ") is None
    assert _normalize_api_key("  lmfy-x  ") == "lmfy-x"


def test_get_lumify_tools_is_coroutine_fn():
    assert inspect.iscoroutinefunction(llamaindex_lumify.get_lumify_tools)


def test_missing_key_construction_raises_before_super_init(monkeypatch):
    """Missing-key failure must happen before McpToolSpec/client setup."""
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError):
        LumifyToolSpec()


# --- End-to-end wiring, with the MCP client faked out (no network). ---


@pytest.fixture(autouse=True)
def _reset_fake_mcp_client():
    yield
    _FakeMCPClient.tools_to_return = []
    _FakeMCPClient.call_tool_error = None
    _FakeMCPClient.last_url = None
    _FakeMCPClient.last_headers = None
    _FakeMCPClient.last_timeout = None
    _FakeMCPClient.last_sse_read_timeout = None


class _FakeMcpTool:
    def __init__(self, name: str, description: str = "d"):
        self.name = name
        self.description = description
        self.inputSchema = {"type": "object", "properties": {}}


class _FakeListToolsResponse:
    def __init__(self, tools):
        self.tools = tools


class _FakeMCPClient:
    """Stands in for BasicMCPClient; returns a fixed tool list instead of
    touching the network."""

    last_url: str | None = None
    last_headers: dict | None = None
    last_timeout: int | None = None
    last_sse_read_timeout: int | None = None
    tools_to_return: list = []
    call_tool_error: BaseException | None = None

    def __init__(self, url, headers=None, timeout=30, sse_read_timeout=300, **_kwargs):
        type(self).last_url = url
        type(self).last_headers = headers
        type(self).last_timeout = timeout
        type(self).last_sse_read_timeout = sse_read_timeout

    async def list_tools(self):
        return _FakeListToolsResponse(list(_FakeMCPClient.tools_to_return))

    async def call_tool(self, name, arguments):
        if _FakeMCPClient.call_tool_error is not None:
            raise _FakeMCPClient.call_tool_error
        return "ok"


@pytest.mark.asyncio
async def test_get_lumify_tools_never_builds_client_without_key(monkeypatch):
    """Missing-key failure must happen before any client/network setup."""
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    constructed = {"count": 0}

    class _ExplodingClient:
        def __init__(self, *a, **kw):
            constructed["count"] += 1

    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _ExplodingClient)
    with pytest.raises(MissingApiKeyError):
        await get_lumify_tools()
    assert constructed["count"] == 0


@pytest.mark.asyncio
async def test_get_lumify_tools_wires_through_client(monkeypatch):
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("fake")]
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(api_key="lmfy-test.123")

    assert [t.metadata.name for t in tools] == ["fake"]
    assert all(isinstance(t, FunctionTool) for t in tools)
    assert _FakeMCPClient.last_url == DEFAULT_MCP_URL
    assert _FakeMCPClient.last_headers["Authorization"] == "Bearer lmfy-test.123"


@pytest.mark.asyncio
async def test_tool_spec_acreate_wires_through_client(monkeypatch):
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("fake2")]
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tool_spec = LumifyToolSpec(api_key="lmfy-test.123")
    tools = await tool_spec.to_tool_list_async()

    assert [t.metadata.name for t in tools] == ["fake2"]


@pytest.mark.asyncio
async def test_get_lumify_tools_raises_when_server_returns_zero_tools(monkeypatch):
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    with pytest.raises(RuntimeError, match="no tools"):
        await get_lumify_tools(api_key="lmfy-test.123")


@pytest.mark.asyncio
async def test_tool_spec_raises_when_server_returns_zero_tools(monkeypatch):
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tool_spec = LumifyToolSpec(api_key="lmfy-test.123")
    with pytest.raises(RuntimeError, match="no tools"):
        await tool_spec.to_tool_list_async()


@pytest.mark.asyncio
async def test_allowed_tools_empty_filter_does_not_raise(monkeypatch):
    """Explicit allowlist may legitimately yield zero tools — do not raise."""
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("list_events")]
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(
        api_key="lmfy-test.123",
        allowed_tools=["not_a_real_tool"],
    )
    assert tools == []


@pytest.mark.asyncio
async def test_timeouts_wire_through_get_lumify_tools(monkeypatch):
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("fake")]
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    await get_lumify_tools(
        api_key="lmfy-test.123",
        timeout=90,
        sse_read_timeout=600,
    )
    assert _FakeMCPClient.last_timeout == 90
    assert _FakeMCPClient.last_sse_read_timeout == 600


@pytest.mark.asyncio
async def test_fake_tool_call_succeeds_through_wrapped_fn(monkeypatch):
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("fake3")]
    _FakeMCPClient.call_tool_error = None
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(api_key="lmfy-test.123")
    output = await tools[0].acall()
    assert output.raw_output == "ok"


@pytest.mark.asyncio
async def test_friendly_errors_default_wraps_wired_402(monkeypatch):
    """Default path must wrap 401/402 from call_tool, not only unit-level wraps."""

    class _FakeResp:
        status_code = 402

    err = RuntimeError("Payment Required")
    err.response = _FakeResp()
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("get_intelligence")]
    _FakeMCPClient.call_tool_error = err
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(api_key="lmfy-test.123")
    output = await tools[0].acall()
    assert "run out of credits" in output.raw_output
    assert "lumify.ai/register" in output.raw_output


@pytest.mark.asyncio
async def test_friendly_errors_false_leaves_tool_unwrapped(monkeypatch):
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("fake4")]
    _FakeMCPClient.call_tool_error = None
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(api_key="lmfy-test.123", friendly_errors=False)
    output = await tools[0].acall()
    assert output.raw_output == "ok"


def test_sync_to_tool_list_applies_friendly_wrap_and_empty_guard(monkeypatch):
    """Sync listing must use our override (wrapping + empty raise), not bare parent."""
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tool_spec = LumifyToolSpec(api_key="lmfy-test.123")
    with pytest.raises(RuntimeError, match="no tools"):
        tool_spec.to_tool_list()


def test_sync_to_tool_list_returns_wrapped_tools(monkeypatch):
    class _FakeResp:
        status_code = 401

    err = RuntimeError("Unauthorized")
    err.response = _FakeResp()
    _FakeMCPClient.tools_to_return = [_FakeMcpTool("list_events")]
    _FakeMCPClient.call_tool_error = err
    monkeypatch.setattr(llamaindex_lumify, "BasicMCPClient", _FakeMCPClient)

    tools = LumifyToolSpec(api_key="lmfy-test.123").to_tool_list()
    assert len(tools) == 1

    import asyncio

    output = asyncio.run(tools[0].acall())
    assert "missing or invalid" in output.raw_output
