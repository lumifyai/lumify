"""Optional live smoke against the hosted Lumify MCP.

Skipped unless ``LUMIFY_LIVE_SMOKE=1`` and ``LUMIFY_API_KEY`` are set — keeps CI
offline-only (same pattern as langchain-lumify / llamaindex-lumify).

    LUMIFY_LIVE_SMOKE=1 pytest clients/crewai-lumify/tests/test_live_smoke.py
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMIFY_LIVE_SMOKE") != "1",
    reason="Set LUMIFY_LIVE_SMOKE=1 to hit the hosted MCP endpoint",
)


def test_get_lumify_mcp_builds_streamable_http():
    from crewai.mcp import MCPServerHTTP
    from crewai_lumify import DEFAULT_MCP_URL, get_lumify_mcp

    api_key = os.environ.get("LUMIFY_API_KEY")
    if not api_key:
        pytest.skip("LUMIFY_API_KEY required for live smoke")

    mcp = get_lumify_mcp(api_key=api_key)
    assert isinstance(mcp, MCPServerHTTP)
    assert mcp.url == DEFAULT_MCP_URL
    assert mcp.streamable is True
    assert mcp.headers["Authorization"].startswith("Bearer ")
