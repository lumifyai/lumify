"""
Cursor pagination helpers — every ``/v1`` list endpoint takes ``after_id`` +
``limit`` (max 100, default 25) and returns ``next_after_id`` (``None`` when
exhausted). Some responses also carry ``has_more``; others (events) omit it, so
callers must derive "done" from ``next_after_id is None`` rather than relying on
``has_more``.

List envelopes are not uniform: teams/players use ``data``, events uses
``events``, sports/seasons are non-cursor. Pass ``items_key`` to
:func:`iterate_items` when the array field is not ``data``.

These mirror the TS SDK's standalone ``paginate`` / ``iterateItems`` helpers.
Resource classes also expose ``.paginate()`` / ``.iterate()`` convenience
wrappers that fill in the right ``items_key`` for you.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterator, Optional

# A page fetcher: (after_id, limit) -> page dict.
FetchPage = Callable[[Optional[int], int], Dict[str, Any]]


def paginate(
    fetch_page: FetchPage, *, limit: int = 25, max_pages: int = 1000
) -> Iterator[Dict[str, Any]]:
    """Yield each page of a cursor-paginated list endpoint until
    ``next_after_id`` is ``None`` (or ``max_pages`` is hit)."""
    after_id: Optional[int] = None
    for _ in range(max_pages):
        page = fetch_page(after_id, limit)
        yield page
        nxt = page.get("next_after_id") if isinstance(page, dict) else None
        if nxt is None:
            return
        after_id = nxt


def iterate_items(
    fetch_page: FetchPage,
    *,
    items_key: str = "data",
    limit: int = 25,
    max_pages: int = 1000,
) -> Iterator[Any]:
    """Flatten a paginated list endpoint into a single iterator over its items."""
    for page in paginate(fetch_page, limit=limit, max_pages=max_pages):
        items = page.get(items_key) if isinstance(page, dict) else None
        if isinstance(items, list):
            for item in items:
                yield item
