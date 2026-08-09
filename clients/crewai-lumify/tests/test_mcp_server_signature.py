"""Guards against crewai.mcp.MCPServerHTTP's constructor drifting away from
the kwargs crewai-lumify builds.

The tests in test_connection_config.py exercise ``_mcp_kwargs``/
``get_lumify_mcp`` against a fake stand-in class that accepts any keyword
argument via ``**kwargs``, so a kwarg name/type mismatch against the *real*
``MCPServerHTTP`` would not be caught there. This module only runs when
crewai is actually importable — it is skipped under the fast, ``--no-deps``
unit-test job used in CI, but is worth running locally (or in a full-deps CI
job) whenever crewai is upgraded.
"""

from __future__ import annotations

import inspect

import pytest

crewai_mcp = pytest.importorskip(
    "crewai.mcp", reason="crewai not installed in this environment"
)

from crewai_lumify import DEFAULT_MCP_URL, _mcp_kwargs  # noqa: E402


def _accepted_params() -> set[str]:
    return set(inspect.signature(crewai_mcp.MCPServerHTTP).parameters)


def test_default_kwargs_are_accepted_by_real_constructor():
    kwargs = _mcp_kwargs("lmfy-x", DEFAULT_MCP_URL)
    assert set(kwargs) <= _accepted_params()
    server = crewai_mcp.MCPServerHTTP(**kwargs)
    assert server.url == DEFAULT_MCP_URL
    assert server.headers["Authorization"] == "Bearer lmfy-x"


def test_full_kwargs_are_accepted_by_real_constructor():
    kwargs = _mcp_kwargs(
        "lmfy-x",
        DEFAULT_MCP_URL,
        streamable=False,
        cache_tools_list=True,
        tool_filter=lambda *_args, **_kwargs: True,
    )
    assert set(kwargs) <= _accepted_params()
    server = crewai_mcp.MCPServerHTTP(**kwargs)
    assert server.streamable is False
    assert server.cache_tools_list is True
