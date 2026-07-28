"""Async counterparts to :mod:`lumify.pagination` — same cursor-pagination
contract (``after_id``/``limit`` in, ``next_after_id`` out), as async
generators so callers can ``async for`` without blocking on each page."""

from __future__ import annotations

from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional

# An async page fetcher: (after_id, limit) -> awaitable page dict.
AsyncFetchPage = Callable[[Optional[int], int], Awaitable[Dict[str, Any]]]


async def paginate(
    fetch_page: AsyncFetchPage, *, limit: int = 25, max_pages: int = 1000
) -> AsyncIterator[Dict[str, Any]]:
    """Yield each page of a cursor-paginated list endpoint until
    ``next_after_id`` is ``None`` (or ``max_pages`` is hit)."""
    after_id: Optional[int] = None
    for _ in range(max_pages):
        page = await fetch_page(after_id, limit)
        yield page
        nxt = page.get("next_after_id") if isinstance(page, dict) else None
        if nxt is None:
            return
        after_id = nxt


async def iterate_items(
    fetch_page: AsyncFetchPage,
    *,
    items_key: str = "data",
    limit: int = 25,
    max_pages: int = 1000,
) -> AsyncIterator[Any]:
    """Flatten a paginated list endpoint into a single async iterator over its items."""
    async for page in paginate(fetch_page, limit=limit, max_pages=max_pages):
        items = page.get(items_key) if isinstance(page, dict) else None
        if isinstance(items, list):
            for item in items:
                yield item
