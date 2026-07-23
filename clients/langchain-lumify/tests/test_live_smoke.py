"""Optional live smoke against the hosted Lumify MCP endpoint.

Skipped by default. Enable with::

    LUMIFY_LIVE_SMOKE=1 pytest clients/langchain-lumify/tests/test_live_smoke.py
"""

from __future__ import annotations

import os

import pytest
from langchain_lumify import get_lumify_tools

pytestmark = pytest.mark.skipif(
    os.environ.get("LUMIFY_LIVE_SMOKE") != "1",
    reason="Set LUMIFY_LIVE_SMOKE=1 to hit https://lumify.ai/mcp",
)


@pytest.mark.asyncio
async def test_tools_list_unauthenticated():
    """``tools/list`` is public — load the catalog without a key."""
    tools = await get_lumify_tools(require_api_key=False)
    names = {t.name for t in tools}
    # Stable core surface — fail if the hosted server drops critical tools.
    assert {"list_events", "get_intelligence", "get_odds"} <= names
    assert len(tools) >= 16
