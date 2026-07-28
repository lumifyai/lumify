from lumify.aio.pagination import iterate_items, paginate


def _pager(pages):
    """Return an async fetch_page callable serving the given canned pages in order."""
    state = {"i": 0}

    async def fetch(after_id, limit):
        page = pages[state["i"]]
        state["i"] += 1
        return page

    return fetch


async def test_paginate_stops_when_next_after_id_is_none():
    pages = [
        {"events": [{"id": 1}], "next_after_id": 1},
        {"events": [{"id": 2}], "next_after_id": 2},
        {"events": [{"id": 3}], "next_after_id": None},
    ]
    got = [p async for p in paginate(_pager(pages), limit=1)]
    assert len(got) == 3
    assert got[-1]["next_after_id"] is None


async def test_paginate_respects_max_pages():
    async def fetch(after_id, limit):
        return {"events": [{"id": (after_id or 0) + 1}], "next_after_id": (after_id or 0) + 1}

    got = [p async for p in paginate(fetch, limit=1, max_pages=4)]
    assert len(got) == 4


async def test_iterate_items_flattens_with_custom_key():
    pages = [
        {"events": [{"id": 1}, {"id": 2}], "next_after_id": 2},
        {"events": [{"id": 3}], "next_after_id": None},
    ]
    ids = [item["id"] async for item in iterate_items(_pager(pages), items_key="events", limit=2)]
    assert ids == [1, 2, 3]


async def test_iterate_items_default_key_is_data():
    pages = [
        {"data": [{"id": 1}], "next_after_id": 1},
        {"data": [{"id": 2}], "next_after_id": None},
    ]
    ids = [item["id"] async for item in iterate_items(_pager(pages), limit=1)]
    assert ids == [1, 2]


async def test_iterate_items_skips_missing_or_nonlist_items():
    pages = [
        {"next_after_id": 1},  # missing items key
        {"data": "nope", "next_after_id": None},  # not a list
    ]
    assert [item async for item in iterate_items(_pager(pages), limit=1)] == []
