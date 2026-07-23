import json
from urllib.parse import parse_qs, urlparse

from ._async_helpers import make_async_client, only_call


def _path_and_query(req):
    parsed = urlparse(req.url)
    return parsed.path, {k: v[0] for k, v in parse_qs(parsed.query).items()}


async def test_seasons_list_query():
    client = make_async_client([{"body": {"seasons": []}}])
    await client.seasons.list(sport="nfl", current_only=True)
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/seasons"
    assert q == {"sport": "nfl", "current_only": "true"}


async def test_event_get_compound_query_keys():
    client = make_async_client([{"body": {"id": 1}}])
    await client.events.get(1, include_odds=True, include_intelligence=True, bookmaker="pinnacle")
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/events/1"
    assert q == {"include_odds": "true", "include_intelligence": "true", "bookmaker": "pinnacle"}


async def test_events_list_includes_team_id():
    client = make_async_client([{"body": {"events": [], "total": 0}}])
    await client.events.list(sport="nhl", team_id=42, limit=10)
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/events"
    assert q == {"sport": "nhl", "team_id": "42", "limit": "10"}


async def test_batch_get_posts_event_ids_and_drops_unset_optionals():
    client = make_async_client([{"body": {"events": [], "not_found": [], "total": 0}}])
    await client.events.batch_get([1, 2, 3], include_odds=True, bookmaker="pinnacle")
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/events/batch"
    body = json.loads(req.body)
    assert body == {"event_ids": [1, 2, 3], "include_odds": True, "bookmaker": "pinnacle"}


async def test_query_posts_text_and_limit():
    client = make_async_client(
        [
            {
                "body": {
                    "query": "nhl games",
                    "interpreted": {},
                    "unrecognized_terms": [],
                    "equivalent_request": "GET /v1/events",
                    "events": [],
                    "total": 0,
                    "next_after_id": None,
                }
            }
        ]
    )
    await client.events.query("nhl games", limit=5)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/query"
    assert json.loads(req.body) == {"query": "nhl games", "limit": 5}


async def test_player_events_maps_from_keyword():
    client = make_async_client([{"body": {"player_id": 1, "data": []}}])
    await client.players.events(1, from_="2026-01-01", to="2026-02-01", status="final")
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/players/1/events"
    assert q == {"from": "2026-01-01", "to": "2026-02-01", "status": "final"}


async def test_webhook_create_posts_json_body():
    client = make_async_client([{"body": {"id": 1, "signing_secret": "whsec_x"}}])
    await client.webhooks.create(
        url="https://you.example.com/hook", event_types=["score", "line_move"], sport="nhl"
    )
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/webhooks"
    assert req.headers["Content-Type"] == "application/json"
    body = json.loads(req.body)
    assert body["url"] == "https://you.example.com/hook"
    assert body["event_types"] == ["score", "line_move"]
    assert body["sport"] == "nhl"


async def test_webhook_delete_uses_delete_method():
    client = make_async_client([{"body": {"deleted": True, "id": 7}}])
    await client.webhooks.delete(7)
    req = only_call(client)
    assert req.method == "DELETE"
    assert urlparse(req.url).path == "/v1/webhooks/7"


async def test_webhook_deliveries_path_and_query():
    client = make_async_client([{"body": {"data": [], "next_after_id": None}}])
    await client.webhooks.deliveries(
        7, after_id=100, limit=10, success=True, given_up=False, event_type="line_move"
    )
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/webhooks/7/deliveries"
    assert q == {
        "after_id": "100",
        "limit": "10",
        "success": "true",
        "given_up": "false",
        "event_type": "line_move",
    }


async def test_webhook_verify_is_sync_and_works_on_async_client():
    client = make_async_client([])
    sub = {"id": 1, "url": "https://example.com/hook", "signing_secret": "whsec_test"}
    import hashlib
    import hmac
    import time

    ts = int(time.time())
    body = '{"event":"score"}'
    sig = hmac.new(
        sub["signing_secret"].encode("utf-8"), ("%d.%s" % (ts, body)).encode("utf-8"), hashlib.sha256
    ).hexdigest()
    client.webhooks.verify(sub["signing_secret"], "t=%d,v1=%s" % (ts, sig), body)


async def test_agent_key_create_body_and_credits_paths():
    client = make_async_client([{"body": {"id": 1, "key": "lmfy-new"}}])
    await client.agent.keys.create(name="ci", scopes=["nfl", "nba"], expires_in_days=30)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/api/agent/keys"
    body = json.loads(req.body)
    assert body == {"name": "ci", "scopes": ["nfl", "nba"], "expires_in_days": 30}


async def test_agent_credits_topup_posts_pack_id():
    client = make_async_client([{"body": {"success": True}}])
    await client.agent.credits.topup(3)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/api/agent/credits/topup"
    assert json.loads(req.body) == {"pack_id": 3}


async def test_iterate_events_uses_events_key_across_pages():
    client = make_async_client(
        [
            {"body": {"events": [{"id": 1}], "next_after_id": 1}},
            {"body": {"events": [{"id": 2}], "next_after_id": None}},
        ]
    )
    ids = [e["id"] async for e in client.events.iterate(sport="nhl", limit=1)]
    assert ids == [1, 2]


async def test_teams_paginate_yields_pages():
    client = make_async_client(
        [
            {"body": {"data": [{"id": 1}], "next_after_id": 1}},
            {"body": {"data": [{"id": 2}], "next_after_id": None}},
        ]
    )
    pages = [p async for p in client.teams.paginate(sport="nba", limit=1)]
    assert len(pages) == 2
    assert pages[-1]["next_after_id"] is None
