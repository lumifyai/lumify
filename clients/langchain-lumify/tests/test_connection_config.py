"""Offline unit tests for langchain-lumify.

These exercise connection-config / auth hardening without touching the network
(the MCP session is only opened lazily on ``get_tools``).
"""

import inspect
import warnings

import langchain_lumify
import pytest
from langchain_core.tools import StructuredTool
from langchain_lumify import (
    DEFAULT_MCP_URL,
    LumifyToolkit,
    MissingApiKeyError,
    _connection_config,
    _normalize_api_key,
    get_lumify_tools,
)


def test_default_url_and_version():
    assert DEFAULT_MCP_URL == "https://lumify.ai/mcp"
    assert isinstance(langchain_lumify.__version__, str)
    assert langchain_lumify.__version__


def test_explicit_key_sets_bearer_and_client_headers():
    cfg = _connection_config("lmfy-abc.123", DEFAULT_MCP_URL)
    assert cfg["transport"] == "streamable_http"
    assert cfg["url"] == DEFAULT_MCP_URL
    headers = cfg["headers"]
    assert headers["Authorization"] == "Bearer lmfy-abc.123"
    assert headers["User-Agent"].startswith("langchain-lumify/")
    assert headers["X-Lumify-Client"].startswith("langchain-lumify/")


def test_strips_leading_bearer_prefix():
    cfg = _connection_config("Bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert cfg["headers"]["Authorization"] == "Bearer lmfy-abc.123"


def test_strips_bearer_case_insensitive():
    cfg = _connection_config("bearer lmfy-abc.123", DEFAULT_MCP_URL)
    assert cfg["headers"]["Authorization"] == "Bearer lmfy-abc.123"


def test_whitespace_only_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _connection_config("   ", DEFAULT_MCP_URL)


def test_empty_string_key_treated_as_missing():
    with pytest.raises(MissingApiKeyError):
        _connection_config("", DEFAULT_MCP_URL)


def test_env_key_fallback(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "lmfy-env.999")
    cfg = _connection_config(None, DEFAULT_MCP_URL)
    assert cfg["headers"]["Authorization"] == "Bearer lmfy-env.999"


def test_env_key_with_bearer_prefix_normalized(monkeypatch):
    monkeypatch.setenv("LUMIFY_API_KEY", "Bearer lmfy-env.999")
    cfg = _connection_config(None, DEFAULT_MCP_URL)
    assert cfg["headers"]["Authorization"] == "Bearer lmfy-env.999"


def test_require_api_key_default_raises_without_key(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    with pytest.raises(MissingApiKeyError, match="docs/ai"):
        _connection_config(None, DEFAULT_MCP_URL)


def test_require_api_key_false_allows_list_without_auth(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    cfg = _connection_config(None, DEFAULT_MCP_URL, require_api_key=False)
    assert "Authorization" not in cfg["headers"]
    assert cfg["headers"]["User-Agent"].startswith("langchain-lumify/")


def test_custom_url_preserved(monkeypatch):
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    cfg = _connection_config(
        None, "https://self-hosted.example/mcp", require_api_key=False
    )
    assert cfg["url"] == "https://self-hosted.example/mcp"


def test_non_lmfy_prefix_warns_but_still_sends():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cfg = _connection_config("sk-not-a-lumify-key", DEFAULT_MCP_URL)
    assert cfg["headers"]["Authorization"] == "Bearer sk-not-a-lumify-key"
    assert any(issubclass(w.category, UserWarning) for w in caught)
    assert any("lmfy-" in str(w.message) for w in caught)


def test_normalize_api_key_helpers():
    assert _normalize_api_key(None) is None
    assert _normalize_api_key("") is None
    assert _normalize_api_key("  ") is None
    assert _normalize_api_key("Bearer ") is None
    assert _normalize_api_key("  lmfy-x  ") == "lmfy-x"


def test_get_lumify_tools_is_coroutine_fn():
    assert inspect.iscoroutinefunction(langchain_lumify.get_lumify_tools)


def test_empty_toolkit_construction_raises():
    with pytest.raises(ValueError, match="acreate"):
        LumifyToolkit()


def test_toolkit_with_explicit_tools_ok():
    fake = StructuredTool.from_function(lambda x: x, name="t", description="d")
    tk = LumifyToolkit(tools=[fake])
    assert [t.name for t in tk.get_tools()] == ["t"]


# --- End-to-end wiring, with MultiServerMCPClient faked out (no network). ---
#
# The tests above only exercise `_connection_config` directly; these cover the
# actual async call path (get_lumify_tools / LumifyToolkit.acreate ->
# MultiServerMCPClient), which had no non-network coverage previously.


class _FakeMCPClient:
    """Stands in for MultiServerMCPClient; records the connection/interceptors
    it was built with and returns a fixed tool list instead of touching the
    network."""

    last_connections: dict | None = None
    last_interceptors: list | None = None

    def __init__(self, connections, *, tool_interceptors=None, **_kwargs):
        type(self).last_connections = connections
        type(self).last_interceptors = tool_interceptors
        self._tools = list(_FakeMCPClient.tools_to_return)

    async def get_tools(self):
        return self._tools

    tools_to_return: list = []


@pytest.mark.asyncio
async def test_get_lumify_tools_never_constructs_client_without_key(monkeypatch):
    """Missing-key failure must happen before any client/network setup."""
    monkeypatch.delenv("LUMIFY_API_KEY", raising=False)
    constructed = {"count": 0}

    class _ExplodingClient:
        def __init__(self, *a, **kw):
            constructed["count"] += 1

    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _ExplodingClient)
    with pytest.raises(MissingApiKeyError):
        await get_lumify_tools()
    assert constructed["count"] == 0


@pytest.mark.asyncio
async def test_get_lumify_tools_wires_through_client(monkeypatch):
    fake_tool = StructuredTool.from_function(lambda x: x, name="fake", description="d")
    _FakeMCPClient.tools_to_return = [fake_tool]
    _FakeMCPClient.last_connections = None
    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _FakeMCPClient)

    tools = await get_lumify_tools(api_key="lmfy-test.123")

    assert [t.name for t in tools] == ["fake"]
    conns = _FakeMCPClient.last_connections
    assert set(conns) == {"lumify"}
    assert conns["lumify"]["url"] == DEFAULT_MCP_URL
    assert conns["lumify"]["headers"]["Authorization"] == "Bearer lmfy-test.123"


@pytest.mark.asyncio
async def test_toolkit_acreate_wires_through_client(monkeypatch):
    fake_tool = StructuredTool.from_function(lambda x: x, name="fake2", description="d")
    _FakeMCPClient.tools_to_return = [fake_tool]
    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _FakeMCPClient)

    toolkit = await LumifyToolkit.acreate(api_key="lmfy-test.123")

    assert [t.name for t in toolkit.get_tools()] == ["fake2"]


@pytest.mark.asyncio
async def test_toolkit_acreate_raises_when_server_returns_zero_tools(monkeypatch):
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _FakeMCPClient)

    with pytest.raises(RuntimeError, match="no tools"):
        await LumifyToolkit.acreate(api_key="lmfy-test.123")


def test_friendly_errors_default_installs_interceptor(monkeypatch):
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _FakeMCPClient)
    langchain_lumify._build_client("lmfy-x", DEFAULT_MCP_URL)
    assert len(_FakeMCPClient.last_interceptors) == 1


def test_friendly_errors_false_installs_no_interceptor(monkeypatch):
    _FakeMCPClient.tools_to_return = []
    monkeypatch.setattr(langchain_lumify, "MultiServerMCPClient", _FakeMCPClient)
    langchain_lumify._build_client("lmfy-x", DEFAULT_MCP_URL, friendly_errors=False)
    assert _FakeMCPClient.last_interceptors is None
