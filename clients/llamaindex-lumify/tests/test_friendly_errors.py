"""Tests for the friendly-error wrapper.

Lumify's auth middleware short-circuits `/mcp` with a raw HTTP 402 (exhausted
credits) or 401 (missing/invalid key) *outside* the JSON-RPC envelope.
`FunctionTool.acall` awaits the wrapped function directly and does not catch
exceptions, so this would otherwise propagate as a raw, unhandled exception
straight out of an agent's tool call. `_wrap_friendly_errors` is the recovery
path — these tests exercise it directly, without touching the network.
"""

from __future__ import annotations

import pytest
from llama_index.core.tools.function_tool import FunctionTool
from llama_index.core.tools.types import ToolMetadata
from llamaindex_lumify import _extract_http_status, _wrap_friendly_errors


class _FakeHttpxResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeHttpxStatusError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.response = _FakeHttpxResponse(status_code)


def _tool_with_fn(fn, name: str = "get_intelligence") -> FunctionTool:
    return FunctionTool.from_defaults(
        async_fn=fn,
        tool_metadata=ToolMetadata(name=name, description="d"),
    )


def test_extract_http_status_from_httpx_style_response():
    exc = _FakeHttpxStatusError("boom", 402)
    assert _extract_http_status(exc) == 402


def test_extract_http_status_from_bare_status_code_attr():
    exc = Exception("boom")
    exc.status_code = 401
    assert _extract_http_status(exc) == 401


def test_extract_http_status_from_message_text_fallback():
    exc = RuntimeError("Server returned HTTP 402 Payment Required")
    assert _extract_http_status(exc) == 402


def test_extract_http_status_none_when_unrecognized():
    assert _extract_http_status(RuntimeError("connection reset")) is None


def test_extract_http_status_walks_cause_chain():
    try:
        try:
            raise _FakeHttpxStatusError("Payment Required", 402)
        except _FakeHttpxStatusError as inner:
            raise RuntimeError("mcp session failed") from inner
    except RuntimeError as outer:
        assert _extract_http_status(outer) == 402


def test_extract_http_status_walks_exception_group():
    group = ExceptionGroup(
        "transport",
        [_FakeHttpxStatusError("Payment Required", 402)],
    )
    assert _extract_http_status(group) == 402


@pytest.mark.asyncio
async def test_wrapper_converts_402_to_credit_hint_string():
    async def fn(**_kwargs):
        raise _FakeHttpxStatusError("Payment Required", 402)

    wrapped = _wrap_friendly_errors(_tool_with_fn(fn))
    output = await wrapped.acall()

    assert "run out of credits" in output.raw_output
    assert "lumify.ai/register" in output.raw_output


@pytest.mark.asyncio
async def test_wrapper_converts_401_to_auth_hint_string():
    async def fn(**_kwargs):
        raise _FakeHttpxStatusError("Unauthorized", 401)

    wrapped = _wrap_friendly_errors(_tool_with_fn(fn))
    output = await wrapped.acall()

    assert "missing or invalid" in output.raw_output
    assert "docs/ai" in output.raw_output


@pytest.mark.asyncio
async def test_wrapper_reraises_unrecognized_errors():
    async def fn(**_kwargs):
        raise ConnectionError("network is unreachable")

    wrapped = _wrap_friendly_errors(_tool_with_fn(fn))
    with pytest.raises(ConnectionError):
        await wrapped.acall()


@pytest.mark.asyncio
async def test_wrapper_passes_through_success():
    async def fn(**_kwargs):
        return "real result"

    wrapped = _wrap_friendly_errors(_tool_with_fn(fn))
    output = await wrapped.acall()
    assert output.raw_output == "real result"


@pytest.mark.asyncio
async def test_wrapper_preserves_tool_metadata():
    async def fn(**_kwargs):
        return "ok"

    original = _tool_with_fn(fn, name="my_tool")
    wrapped = _wrap_friendly_errors(original)
    assert wrapped.metadata.name == "my_tool"
    assert wrapped.metadata.description == original.metadata.description
