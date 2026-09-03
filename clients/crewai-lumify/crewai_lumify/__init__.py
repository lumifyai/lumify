"""CrewAI integration for the Lumify Sports Intelligence MCP server.

Lumify hosts a remote Model Context Protocol server at ``https://lumify.ai/mcp``
exposing schedules, live scores, odds, public betting splits, and explainable AI
bet confidence across 8+ sports. This package returns a ready-to-use
``MCPServerHTTP`` for CrewAI's ``Agent(mcps=[...])`` DSL — auth headers and
client attribution included.

Get a free key in seconds — no signup, email, or card — at
https://lumify.ai/docs/ai. Tool *execution* requires a key (Bearer token);
``tools/list`` is public, so pass ``require_api_key=False`` only when you
intentionally want to introspect the tool catalog without credentials.

Example:
    >>> from crewai import Agent, Task, Crew
    >>> from crewai_lumify import get_lumify_mcp
    >>>
    >>> agent = Agent(
    ...     role="Sports Analyst",
    ...     goal="Find edges using odds and intelligence",
    ...     backstory="Expert with access to sports market data",
    ...     mcps=[get_lumify_mcp()],  # reads LUMIFY_API_KEY
    ... )
    >>> task = Task(
    ...     description="What's the best MLB bet today, with the rationale?",
    ...     expected_output="A short recommendation with confidence and why.",
    ...     agent=agent,
    ... )
    >>> Crew(agents=[agent], tasks=[task]).kickoff()  # doctest: +SKIP
"""

from __future__ import annotations

import os
import warnings
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from crewai.mcp import MCPServerHTTP, ToolFilter

__all__ = [
    "get_lumify_mcp",
    "DEFAULT_MCP_URL",
    "MissingApiKeyError",
    "__version__",
]

try:
    __version__ = version("crewai-lumify")
except PackageNotFoundError:  # pragma: no cover - editable/src tree without install
    __version__ = "0.1.0"

#: Hosted Lumify MCP endpoint (Streamable HTTP, stateless JSON mode).
DEFAULT_MCP_URL = "https://lumify.ai/mcp"

_INSTANT_KEY_URL = "https://lumify.ai/docs/ai"


class MissingApiKeyError(ValueError):
    """Raised when a Lumify API key is required but none was provided."""


def _normalize_api_key(api_key: str | None) -> str | None:
    """Strip whitespace / a leading ``Bearer `` prefix; return ``None`` if empty.

    Also warns (does not hard-fail) when the key does not start with the
    expected ``lmfy-`` prefix — callers sometimes paste dashboard labels or
    curl examples by mistake.
    """
    if api_key is None:
        return None
    key = api_key.strip()
    if not key:
        return None
    # Accept "Bearer lmfy-..." copy-pasted from curl / cookbook examples.
    lower = key.lower()
    if lower.startswith("bearer "):
        key = key[7:].strip()
    elif lower == "bearer":
        return None
    if not key:
        return None
    if not key.startswith("lmfy-"):
        warnings.warn(
            "Lumify API keys normally start with 'lmfy-'. "
            f"Get a free instant key (no signup) at {_INSTANT_KEY_URL}.",
            UserWarning,
            stacklevel=2,
        )
    return key


def _resolve_api_key(api_key: str | None) -> str | None:
    """Resolve an explicit key or fall back to ``LUMIFY_API_KEY``."""
    if api_key is not None:
        return _normalize_api_key(api_key)
    return _normalize_api_key(os.environ.get("LUMIFY_API_KEY"))


def _mcp_kwargs(
    api_key: str | None,
    url: str,
    *,
    require_api_key: bool = True,
    streamable: bool = True,
    cache_tools_list: bool = False,
    tool_filter: "ToolFilter | None" = None,
) -> dict[str, Any]:
    """Build keyword args for :class:`crewai.mcp.MCPServerHTTP`.

    Separated from :func:`get_lumify_mcp` so unit tests can assert auth/header
    behavior without importing the full CrewAI runtime.
    """
    key = _resolve_api_key(api_key)
    if require_api_key and not key:
        raise MissingApiKeyError(
            "Lumify API key required for tool execution. "
            f"Pass api_key=..., set LUMIFY_API_KEY, or get a free instant key "
            f"(no signup) at {_INSTANT_KEY_URL}. "
            "Pass require_api_key=False only to list tools without calling them."
        )

    headers: dict[str, str] = {
        "User-Agent": f"crewai-lumify/{__version__}",
        "X-Lumify-Client": f"crewai-lumify/{__version__}",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"

    kwargs: dict[str, Any] = {
        "url": url,
        "headers": headers,
        "streamable": streamable,
        "cache_tools_list": cache_tools_list,
    }
    if tool_filter is not None:
        kwargs["tool_filter"] = tool_filter
    return kwargs


def _mcp_server_cls() -> type[MCPServerHTTP]:
    """Import ``MCPServerHTTP`` lazily so auth checks can run before CrewAI loads."""
    from crewai.mcp import MCPServerHTTP

    return MCPServerHTTP


def get_lumify_mcp(
    api_key: str | None = None,
    url: str = DEFAULT_MCP_URL,
    *,
    require_api_key: bool = True,
    streamable: bool = True,
    cache_tools_list: bool = False,
    tool_filter: "ToolFilter | None" = None,
) -> MCPServerHTTP:
    """Return a CrewAI ``MCPServerHTTP`` pointed at Lumify.

    Pass the result to ``Agent(mcps=[...])``. CrewAI discovers tools and manages
    the connection lifecycle.

    Args:
        api_key: Lumify API key. Defaults to the ``LUMIFY_API_KEY`` env var.
            Get one free (no signup) at https://lumify.ai/docs/ai. Accepts a
            raw ``lmfy-...`` value or a ``Bearer lmfy-...`` copy-paste.
        url: MCP endpoint override. Defaults to :data:`DEFAULT_MCP_URL`.
        require_api_key: When ``True`` (default), require a resolvable key so
            the first tool call does not fail with an opaque 401. Set
            ``False`` only to introspect the public tool catalog.
        streamable: Use streamable HTTP transport (default ``True``). Matches
            Lumify's hosted MCP.
        cache_tools_list: Forwarded to ``MCPServerHTTP`` (default ``False``).
        tool_filter: Optional CrewAI tool filter (static or callable).

    Returns:
        A configured :class:`crewai.mcp.MCPServerHTTP` ready for
        ``Agent(mcps=[...])``.
    """
    kwargs = _mcp_kwargs(
        api_key,
        url,
        require_api_key=require_api_key,
        streamable=streamable,
        cache_tools_list=cache_tools_list,
        tool_filter=tool_filter,
    )
    return _mcp_server_cls()(**kwargs)
