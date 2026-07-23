from lumify.pagination import iterate_items, paginate


def _pager(pages):
    """Return a fetch_page callable serving the given canned pages in order."""
    state = {"i": 0}

    def fetch(after_id, limit):
        page = pages[state["i"]]
        state["i"] += 1
        return page

    return fetch


def test_paginate_stops_when_next_after_id_is_none():
    pages = [
        {"events": [{"id": 1}], "next_after_id": 1},
        {"events": [{"id": 2}], "next_after_id": 2},
        {"events": [{"id": 3}], "next_after_id": None},
    ]
    got = list(paginate(_pager(pages), limit=1))
    assert len(got) == 3
    assert got[-1]["next_after_id"] is None


def test_paginate_respects_max_pages():
    # Never terminates on its own (always returns a cursor).
    def fetch(after_id, limit):
        return {"events": [{"id": (after_id or 0) + 1}], "next_after_id": (after_id or 0) + 1}

    got = list(paginate(fetch, limit=1, max_pages=4))
    assert len(got) == 4


def test_iterate_items_flattens_with_custom_key():
    pages = [
        {"events": [{"id": 1}, {"id": 2}], "next_after_id": 2},
        {"events": [{"id": 3}], "next_after_id": None},
    ]
    ids = [item["id"] for item in iterate_items(_pager(pages), items_key="events", limit=2)]
    assert ids == [1, 2, 3]


def test_iterate_items_default_key_is_data():
    pages = [
        {"data": [{"id": 1}], "next_after_id": 1},
        {"data": [{"id": 2}], "next_after_id": None},
    ]
    ids = [item["id"] for item in iterate_items(_pager(pages), limit=1)]
    assert ids == [1, 2]


def test_iterate_items_skips_missing_or_nonlist_items():
    pages = [
        {"next_after_id": 1},  # missing items key
        {"data": "nope", "next_after_id": None},  # not a list
    ]
    assert list(iterate_items(_pager(pages), limit=1)) == []
