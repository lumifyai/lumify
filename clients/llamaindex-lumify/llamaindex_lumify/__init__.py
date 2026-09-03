"""LlamaIndex integration for the Lumify sports-intelligence MCP server.

Lumify hosts a remote Model Context Protocol server at ``https://lumify.ai/mcp``
exposing schedules, live scores, odds, public betting splits, and explainable AI
bet confidence across 8+ sports. LlamaIndex already speaks MCP natively via
``llama-index-tools-mcp`` (``BasicMCPClient`` + ``McpToolSpec``); this package is
a thin, well-typed convenience layer on top that handles Lumify's auth/header
conventions and turns Lumify's 401/402 transport failures into readable tool
output instead of a crashed agent run.

Get a free key in seconds — no signup, email, or card — at
https://lumify.ai/docs/ai. Tool *execution* requires a key (Bearer token);
``tools/list`` is public, so pass ``require_api_key=False`` only when you
intentionally want to introspect the tool catalog without credentials.

Example:
    >>> import asyncio
    >>> from llamaindex_lumify import get_lumify_tools
    >>> from llama_index.core.agent.workflow import FunctionAgent
    >>>
    >>> async def main():
    ...     tools = await get_lumify_tools()  # reads LUMIFY_API_KEY
    ...     agent = FunctionAgent(tools=tools, llm=...)
    ...     return await agent.run("Best MLB bet today?")
    >>> asyncio.run(main())  # doctest: +SKIP
"""

from __future__ import annotations

import logging
import os
import re
import warnings
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Callable

from llama_index.core.tools.function_tool import FunctionTool
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
from llama_index.tools.mcp.base import patch_sync

__all__ = [
    "get_lumify_tools",
    "LumifyToolSpec",
    "DEFAULT_MCP_URL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_SSE_READ_TIMEOUT",
    "MissingApiKeyError",
    "__version__",
]

try:
    __version__ = version("llamaindex-lumify")
except PackageNotFoundError:  # pragma: no cover - editable/src tree without install
    __version__ = "0.1.0"

#: Hosted Lumify MCP endpoint (Streamable HTTP, stateless JSON mode).
DEFAULT_MCP_URL = "https://lumify.ai/mcp"

#: Default HTTP timeout (seconds) for MCP connect/request operations.
DEFAULT_TIMEOUT = 30

#: Default SSE/stream read timeout (seconds); long enough for slow tool calls
#: such as ``get_intelligence`` under load.
DEFAULT_SSE_READ_TIMEOUT = 300

_INSTANT_KEY_URL = "https://lumify.ai/docs/ai"
_REGISTER_URL = "https://lumify.ai/register"
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


def _build_client(
    api_key: str | None,
    url: str,
    *,
    require_api_key: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    sse_read_timeout: int = DEFAULT_SSE_READ_TIMEOUT,
) -> BasicMCPClient:
    """Build a ``BasicMCPClient`` configured for the Lumify MCP server.

    Args:
        api_key: Explicit key, or ``None`` to read ``LUMIFY_API_KEY``.
        url: MCP endpoint.
        require_api_key: When ``True`` (default), raise
            :class:`MissingApiKeyError` if no key resolves. Set ``False`` only
            for unauthenticated ``tools/list`` introspection.
        timeout: HTTP timeout in seconds for connect/request operations.
        sse_read_timeout: Stream/SSE read timeout in seconds.
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
        "User-Agent": f"llamaindex-lumify/{__version__}",
        "X-Lumify-Client": f"llamaindex-lumify/{__version__}",
    }
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return BasicMCPClient(
        url,
        headers=headers,
        timeout=timeout,
        sse_read_timeout=sse_read_timeout,
    )


_STATUS_RE = re.compile(r"\b(401|402)\b")


def _status_from_single_exc(exc: BaseException) -> int | None:
    """Extract an HTTP status from one exception object (no cause walking)."""
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    match = _STATUS_RE.search(str(exc))
    return int(match.group(1)) if match else None


def _extract_http_status(exc: BaseException) -> int | None:
    """Best-effort extraction of an HTTP status code from a transport error.

    Lumify's auth middleware short-circuits ``/mcp`` with a raw HTTP 402 (not
    a JSON-RPC error envelope) when a *valid* key has run out of credits, and
    a raw 401 for a missing/invalid key. The underlying ``mcp`` SDK / httpx
    transport doesn't guarantee a single exception type across versions for
    that case, so this checks the common ``httpx`` shape
    (``exc.response.status_code``), walks ``__cause__`` / ``__context__`` and
    ``ExceptionGroup.exceptions``, and falls back to pattern-matching the
    stringified exception.
    """
    seen: set[int] = set()
    stack: list[BaseException] = [exc]
    while stack:
        current = stack.pop()
        ident = id(current)
        if ident in seen:
            continue
        seen.add(ident)

        status = _status_from_single_exc(current)
        if status is not None:
            return status

        cause = current.__cause__
        if isinstance(cause, BaseException):
            stack.append(cause)
        context = current.__context__
        # Prefer cause; still walk context when it differs (implicit chaining).
        if isinstance(context, BaseException) and context is not cause:
            stack.append(context)

        nested = getattr(current, "exceptions", None)
        if isinstance(nested, tuple):
            for child in nested:
                if isinstance(child, BaseException):
                    stack.append(child)
    return None


def _friendly_hint(status: int | None) -> str | None:
    if status == 402:
        return (
            "This Lumify API key has run out of credits. Get 1,000 "
            f"additional credits (persistent key) free at {_REGISTER_URL}, "
            f"or a fresh instant trial key at {_INSTANT_KEY_URL}."
        )
    if status == 401:
        return (
            "This Lumify API key is missing or invalid. Get a free "
            f"instant key (no signup) at {_INSTANT_KEY_URL}."
        )
    return None


def _empty_tools_error(url: str) -> RuntimeError:
    _logger.error("Lumify MCP returned zero tools from %s", url)
    return RuntimeError(
        f"Lumify MCP at {url} returned no tools. "
        "Check connectivity and that the endpoint speaks Streamable HTTP."
    )


def _wrap_friendly_errors(tool: FunctionTool) -> FunctionTool:
    """Rewrite known Lumify auth/credit transport failures into readable tool
    output instead of letting them crash the agent run.

    ``FunctionTool.acall`` awaits the wrapped async function directly and
    does not catch exceptions, so an HTTP 401/402 raised by the transport
    below ``McpToolSpec`` would otherwise propagate as a raw, unhandled
    exception. This wrapper is the recovery path: it only handles the two
    status codes it can confidently attribute to Lumify's auth layer, and
    re-raises anything else unchanged.
    """
    original_fn: Callable[..., Any] = tool.async_fn
    tool_name = tool.metadata.name

    async def wrapped(**kwargs: Any) -> Any:
        try:
            return await original_fn(**kwargs)
        except Exception as exc:
            hint = _friendly_hint(_extract_http_status(exc))
            if hint is None:
                raise
            _logger.info("Lumify MCP tool call %r denied: %s", tool_name, exc)
            return f"{exc}\n\n{hint}"

    return FunctionTool.from_defaults(
        async_fn=wrapped,
        tool_metadata=tool.metadata,
        partial_params=tool.partial_params,
    )


class LumifyToolSpec(McpToolSpec):
    """A ``McpToolSpec`` pre-configured for Lumify's hosted MCP server.

    Construct directly (no separate async factory needed — client setup is
    synchronous; only tool fetching is async)::

        tool_spec = LumifyToolSpec()  # reads LUMIFY_API_KEY
        tools = await tool_spec.to_tool_list_async()

    Or synchronously outside an event loop: ``tool_spec.to_tool_list()``.
    """

    def __init__(
        self,
        api_key: str | None = None,
        url: str = DEFAULT_MCP_URL,
        *,
        require_api_key: bool = True,
        friendly_errors: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        sse_read_timeout: int = DEFAULT_SSE_READ_TIMEOUT,
        allowed_tools: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        client = _build_client(
            api_key,
            url,
            require_api_key=require_api_key,
            timeout=timeout,
            sse_read_timeout=sse_read_timeout,
        )
        self._friendly_errors = friendly_errors
        self._mcp_url = url
        # Full catalog expected when ``allowed_tools`` is None. An explicit
        # filter (including ``[]``) may legitimately yield zero tools.
        self._raise_on_empty = allowed_tools is None
        super().__init__(client=client, allowed_tools=allowed_tools, **kwargs)

    async def to_tool_list_async(self) -> list[FunctionTool]:
        tools = await super().to_tool_list_async()
        if self._friendly_errors:
            tools = [_wrap_friendly_errors(t) for t in tools]
        if self._raise_on_empty and not tools:
            raise _empty_tools_error(self._mcp_url)
        return tools

    def to_tool_list(self) -> list[FunctionTool]:
        """Sync shim over :meth:`to_tool_list_async`.

        Explicitly overridden so friendly-error wrapping and the empty-catalog
        guard cannot silently regress if upstream stops delegating sync listing
        to the async method.
        """
        return patch_sync(self.to_tool_list_async)()


async def get_lumify_tools(
    api_key: str | None = None,
    url: str = DEFAULT_MCP_URL,
    *,
    require_api_key: bool = True,
    friendly_errors: bool = True,
    timeout: int = DEFAULT_TIMEOUT,
    sse_read_timeout: int = DEFAULT_SSE_READ_TIMEOUT,
    allowed_tools: list[str] | None = None,
) -> list[FunctionTool]:
    """Load all Lumify tools as LlamaIndex ``FunctionTool`` objects.

    Args:
        api_key: Lumify API key. Defaults to the ``LUMIFY_API_KEY`` env var.
            Get one free (no signup) at https://lumify.ai/docs/ai. Accepts a
            raw ``lmfy-...`` value or a ``Bearer lmfy-...`` copy-paste.
        url: MCP endpoint override. Defaults to :data:`DEFAULT_MCP_URL`.
        require_api_key: When ``True`` (default), require a resolvable key so
            the first tool call does not fail with an opaque 401. Set
            ``False`` only to introspect the public tool catalog.
        friendly_errors: When ``True`` (default), rewrite HTTP 401/402
            transport failures (invalid key / exhausted credits) into
            readable tool output with a `/register` or `/docs/ai` CTA instead
            of letting them crash the agent run as a raw exception.
        timeout: HTTP timeout in seconds for MCP connect/request operations.
        sse_read_timeout: Stream/SSE read timeout in seconds (raise for slow
            tools such as ``get_intelligence``).
        allowed_tools: Optional tool-name allowlist passed through to
            ``McpToolSpec``. When ``None`` (default), the full catalog is
            loaded and an empty response raises. When set, an empty filtered
            result is returned as-is.

    Returns:
        The list of Lumify tools (``list_events``, ``get_intelligence``, …),
        ready to pass to ``FunctionAgent`` / ``ReActAgent`` or any LlamaIndex
        agent.
    """
    tool_spec = LumifyToolSpec(
        api_key,
        url,
        require_api_key=require_api_key,
        friendly_errors=friendly_errors,
        timeout=timeout,
        sse_read_timeout=sse_read_timeout,
        allowed_tools=allowed_tools,
    )
    return await tool_spec.to_tool_list_async()
