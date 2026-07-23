"""
``lumify.aio`` — the async/await counterpart to the top-level :mod:`lumify`
package. Same resources, same REST contract, ``await``-able methods.

Kept as a separate import path (rather than exported from :mod:`lumify`
directly) so importing the zero-dependency sync client never requires the
optional ``httpx`` dependency this package needs for its default transport::

    pip install "lumify-sdk[asyncio]"

    from lumify.aio import AsyncLumify
"""

from __future__ import annotations

from .._async_transport import AsyncLumifyClient, AsyncTransport
from .client import AsyncLumify
from .pagination import iterate_items, paginate
from .sse import astream_scores, parse_async_sse_stream

__all__ = [
    "AsyncLumify",
    "AsyncLumifyClient",
    "AsyncTransport",
    "paginate",
    "iterate_items",
    "astream_scores",
    "parse_async_sse_stream",
]
