"""LangChain integration for the Lumify sports-intelligence MCP server.

Lumify hosts a remote Model Context Protocol server at ``https://lumify.ai/mcp``
exposing schedules, live scores, odds, public betting splits, and explainable AI
bet confidence across 8+ sports. This package is a thin, well-typed wrapper over
``langchain-mcp-adapters`` that loads every Lumify tool into a LangChain or
LangGraph agent in one call.

Get a free key in seconds — no signup, email, or card — at
https://lumify.ai/docs/ai. Tool *execution* requires a key (Bearer token);
``tools/list`` is public, so pass ``require_api_key=False`` only when you
intentionally want to introspect the tool catalog without credentials.

Example:
    >>> import asyncio
    >>> from langchain_lumify import get_lumify_tools
    >>> from langchain.agents import create_agent
    >>>
    >>> async def main():
    ...     tools = await get_lumify_tools()  # reads LUMIFY_API_KEY
    ...     agent = create_agent("openai:gpt-4.1", tools)
    ...     return await agent.ainvoke({"messages": "Best MLB bet today?"})
    >>> asyncio.run(main())  # doctest: +SKIP
"""

from __future__ import annotations

import logging
import os
import re
import warnings
from importlib.metadata import PackageNotFoundError, version

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, BaseToolkit
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.interceptors import MCPToolCallRequest

__all__ = [
    "get_lumify_tools",
    "LumifyToolkit",
    "DEFAULT_MCP_URL",
    "MissingApiKeyError",
    "__version__",
]

try:
    __version__ = version("langchain-lumify")
except PackageNotFoundError:  # pragma: no cover - editable/src tree without install
    __version__ = "0.1.0"

#: Hosted Lumify MCP endpoint (Streamable HTTP, stateless JSON mode).
DEFAULT_MCP_URL = "https://lumify.ai/mcp"

_SERVER_NAME = "lumify"
_INSTANT_KEY_URL = "https://lumify.ai/docs/ai"
_logger = logging.getLogger(__name__)


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
        # stacklevel is approximate: this helper is reachable from several
        # entry points (get_lumify_tools, LumifyToolkit.acreate, or
        # _connection_config called directly) at different call depths, so it
        # can't reliably point at the *caller's* line for all of them. Search
        # for the message text rather than relying on the reported location.
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


def _connection_config(
    api_key: str | None,
    url: str,
    *,
    require_api_key: bool = True,
) -> dict[str, object]:
    """Build the single-server connection config for the Lumify MCP server.

    Args:
        api_key: Explicit key, or ``None`` to read ``LUMIFY_API_KEY``.
        url: MCP endpoint.
        require_api_key: When ``True`` (default), raise
            :class:`MissingApiKeyError` if no key resolves. Set ``False`` only
            for unauthenticated ``tools/list`` introspection.
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
        "User-Agent": f"langchain-lumify/{__version__}",
        "X-Lumify-Client": f"langchain-lumify/{__version__}",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return {"transport": "streamable_http", "url": url, "headers": headers}


_REGISTER_URL = "https://lumify.ai/register"
_STATUS_RE = re.compile(r"\b(401|402)\b")


def _extract_http_status(exc: BaseException) -> int | None:
    """Best-effort extraction of an HTTP status code from a transport error.

    The underlying ``mcp`` SDK / httpx transport doesn't guarantee a single
    exception type across versions, so this checks the common ``httpx``
    shape (``exc.response.status_code``) and falls back to pattern-matching
    the stringified exception.
    """
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    match = _STATUS_RE.search(str(exc))
    return int(match.group(1)) if match else None


class _FriendlyErrorInterceptor:
    """Rewrites known Lumify auth/credit transport failures into a readable
    ``ToolMessage`` instead of letting them crash the agent run.

    Lumify's auth middleware short-circuits ``/mcp`` with a raw HTTP 402 (not
    a JSON-RPC error envelope) when a *valid* key has run out of credits, and
    a raw 401 for a missing/invalid key. Because that breaks the JSON-RPC
    framing the MCP SDK expects for a tool-level error, ``langchain-mcp-
    adapters`` treats it as a transport/session failure — which, per its own
    documentation, is deliberately **not** a ``ToolException`` and therefore
    bypasses ``handle_tool_errors`` and propagates as a raw exception. This
    interceptor is the recovery path: it only handles the two status codes it
    can confidently attribute to Lumify's auth layer, and re-raises anything
    else unchanged.
    """

    async def __call__(
        self,
        request: MCPToolCallRequest,
        handler,
    ):
        try:
            return await handler(request)
        except Exception as exc:
            status = _extract_http_status(exc)
            if status == 402:
                hint = (
                    "This Lumify API key has run out of credits. Get 1,000 "
                    f"additional credits (persistent key) free at {_REGISTER_URL}, "
                    f"or a fresh instant trial key at {_INSTANT_KEY_URL}."
                )
            elif status == 401:
                hint = (
                    "This Lumify API key is missing or invalid. Get a free "
                    f"instant key (no signup) at {_INSTANT_KEY_URL}."
                )
            else:
                raise
            _logger.info("Lumify MCP tool call %r denied (HTTP %s)", request.name, status)
            return ToolMessage(
                content=f"{exc}\n\n{hint}",
                tool_call_id="",
                name=request.name,
                status="error",
            )


def _build_client(
    api_key: str | None,
    url: str,
    *,
    require_api_key: bool = True,
    friendly_errors: bool = True,
) -> MultiServerMCPClient:
    """Build a MultiServerMCPClient configured for the Lumify server."""
    return MultiServerMCPClient(
        {_SERVER_NAME: _connection_config(api_key, url, require_api_key=require_api_key)},
        tool_interceptors=[_FriendlyErrorInterceptor()] if friendly_errors else None,
    )


async def get_lumify_tools(
    api_key: str | None = None,
    url: str = DEFAULT_MCP_URL,
    *,
    require_api_key: bool = True,
    friendly_errors: bool = True,
) -> list[BaseTool]:
    """Load all Lumify tools as LangChain ``BaseTool`` objects.

    Args:
        api_key: Lumify API key. Defaults to the ``LUMIFY_API_KEY`` env var.
            Get one free (no signup) at https://lumify.ai/docs/ai. Accepts a
            raw ``lmfy-...`` value or a ``Bearer lmfy-...`` copy-paste.
        url: MCP endpoint override. Defaults to :data:`DEFAULT_MCP_URL`.
        require_api_key: When ``True`` (default), require a resolvable key so
            the first tool call does not fail with an opaque 401. Set
            ``False`` only to introspect the public tool catalog.
        friendly_errors: When ``True`` (default), rewrite HTTP 401/402
            transport failures (invalid key / exhausted credits) into a
            readable `ToolMessage` with a `/register` or `/docs/ai` CTA
            instead of letting them crash the agent run as a raw exception.

    Returns:
        The list of Lumify tools (``list_events``, ``get_intelligence``, …),
        ready to pass to ``create_agent`` or any LangChain agent/executor.
    """
    client = _build_client(
        api_key, url, require_api_key=require_api_key, friendly_errors=friendly_errors
    )
    return await client.get_tools()


class LumifyToolkit(BaseToolkit):
    """A LangChain toolkit bundling every Lumify tool.

    ``BaseToolkit.get_tools`` is synchronous but MCP tools load asynchronously,
    so construct via :meth:`acreate`::

        toolkit = await LumifyToolkit.acreate()
        agent = create_agent("openai:gpt-4.1", toolkit.get_tools())

    Direct construction with an empty tool list is rejected — use
    ``acreate()`` or pass an explicit non-empty ``tools=`` list.
    """

    tools: list[BaseTool] = []

    _EMPTY_MSG = (
        "LumifyToolkit has no tools. Construct via "
        "`await LumifyToolkit.acreate(...)` (loads from Lumify MCP), "
        "or pass an explicit non-empty tools=[...] list."
    )

    def model_post_init(self, __context: object) -> None:
        # Pydantic v2 hook — block the silent empty-toolkit trap on normal
        # construction and on `model_construct` (both invoke this hook).
        if not self.tools:
            raise ValueError(self._EMPTY_MSG)

    def model_copy(self, *, update=None, deep=False):
        # `model_copy` does NOT re-run model_post_init (it's a shallow/deep
        # field copy, not the validation pipeline), so it can otherwise
        # bypass the empty-toolkit guard via e.g. `.model_copy(update={
        # "tools": []})`. Re-check explicitly.
        copied = super().model_copy(update=update, deep=deep)
        if not copied.tools:
            raise ValueError(self._EMPTY_MSG)
        return copied

    @classmethod
    async def acreate(
        cls,
        api_key: str | None = None,
        url: str = DEFAULT_MCP_URL,
        *,
        require_api_key: bool = True,
        friendly_errors: bool = True,
    ) -> LumifyToolkit:
        """Asynchronously load Lumify tools and return a ready toolkit."""
        tools = await get_lumify_tools(
            api_key=api_key,
            url=url,
            require_api_key=require_api_key,
            friendly_errors=friendly_errors,
        )
        if not tools:
            # Extremely unlikely against the hosted server; fail loudly rather
            # than return a toolkit that silently no-ops.
            _logger.error("Lumify MCP returned zero tools from %s", url)
            raise RuntimeError(
                f"Lumify MCP at {url} returned no tools. "
                "Check connectivity and that the endpoint speaks Streamable HTTP."
            )
        return cls(tools=tools)

    def get_tools(self) -> list[BaseTool]:
        return list(self.tools)
