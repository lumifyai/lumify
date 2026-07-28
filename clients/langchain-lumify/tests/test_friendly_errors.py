"""Tests for the friendly-error interceptor.

Lumify's auth middleware short-circuits `/mcp` with a raw HTTP 402 (exhausted
credits) or 401 (missing/invalid key) *outside* the JSON-RPC envelope, which
`langchain-mcp-adapters` treats as a transport failure rather than a graceful
tool error (see its own docs: transport/session failures are deliberately not
`ToolException` and bypass `handle_tool_errors`). `_FriendlyErrorInterceptor`
is the recovery path — these tests exercise it directly, without touching the
network.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import ToolMessage
from langchain_lumify import _extract_http_status
from langchain_lumify import _FriendlyErrorInterceptor as FriendlyErrorInterceptor
from langchain_mcp_adapters.interceptors import MCPToolCallRequest


class _FakeHttpxResponse:
    def __init__(self, status_code: int):
        self.status_code = status_code


class _FakeHttpxStatusError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.response = _FakeHttpxResponse(status_code)


def _request(name: str = "get_intelligence") -> MCPToolCallRequest:
    return MCPToolCallRequest(name=name, args={}, server_name="lumify")


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


@pytest.mark.asyncio
async def test_interceptor_converts_402_to_credit_hint_tool_message():
    async def handler(_req):
        raise _FakeHttpxStatusError("Payment Required", 402)

    result = await FriendlyErrorInterceptor()(_request(), handler)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert "run out of credits" in result.content
    assert "lumify.ai/register" in result.content
    assert result.name == "get_intelligence"


@pytest.mark.asyncio
async def test_interceptor_converts_401_to_auth_hint_tool_message():
    async def handler(_req):
        raise _FakeHttpxStatusError("Unauthorized", 401)

    result = await FriendlyErrorInterceptor()(_request(), handler)

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert "missing or invalid" in result.content
    assert "docs/ai" in result.content


@pytest.mark.asyncio
async def test_interceptor_reraises_unrecognized_errors():
    async def handler(_req):
        raise ConnectionError("network is unreachable")

    with pytest.raises(ConnectionError):
        await FriendlyErrorInterceptor()(_request(), handler)


@pytest.mark.asyncio
async def test_interceptor_passes_through_success():
    sentinel = object()

    async def handler(_req):
        return sentinel

    result = await FriendlyErrorInterceptor()(_request(), handler)
    assert result is sentinel
