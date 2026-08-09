import json
from urllib.parse import parse_qs, urlparse

from ._helpers import make_client, only_call


def _path_and_query(req):
    parsed = urlparse(req.url)
    return parsed.path, {k: v[0] for k, v in parse_qs(parsed.query).items()}


def test_seasons_list_query():
    client = make_client([{"body": {"seasons": []}}])
    client.seasons.list(sport="nfl", current_only=True)
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/seasons"
    assert q == {"sport": "nfl", "current_only": "true"}


def test_event_get_compound_query_keys():
    client = make_client([{"body": {"id": 1}}])
    client.events.get(1, include_odds=True, include_intelligence=True, bookmaker="pinnacle")
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/events/1"
    assert q == {"include_odds": "true", "include_intelligence": "true", "bookmaker": "pinnacle"}


def test_events_list_includes_team_id():
    client = make_client([{"body": {"events": [], "total": 0}}])
    client.events.list(sport="nhl", team_id=42, limit=10)
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/events"
    assert q == {"sport": "nhl", "team_id": "42", "limit": "10"}


def test_batch_get_posts_event_ids_and_drops_unset_optionals():
    client = make_client([{"body": {"events": [], "not_found": [], "total": 0}}])
    client.events.batch_get([1, 2, 3], include_odds=True, bookmaker="pinnacle")
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/events/batch"
    body = json.loads(req.body)
    assert body == {"event_ids": [1, 2, 3], "include_odds": True, "bookmaker": "pinnacle"}


def test_batch_get_with_only_required_arg_omits_optionals_entirely():
    client = make_client([{"body": {"events": [], "not_found": [], "total": 0}}])
    client.events.batch_get([1, 2])
    body = json.loads(only_call(client).body)
    assert body == {"event_ids": [1, 2]}


def test_query_posts_text_and_limit():
    client = make_client([{"body": {
        "query": "nhl games", "interpreted": {}, "unrecognized_terms": [],
        "equivalent_request": "GET /v1/events", "events": [], "total": 0, "next_after_id": None,
    }}])
    client.events.query("nhl games", limit=5)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/query"
    assert json.loads(req.body) == {"query": "nhl games", "limit": 5}


def test_query_omits_limit_when_not_provided():
    client = make_client([{"body": {}}])
    client.events.query("live nba games")
    body = json.loads(only_call(client).body)
    assert body == {"query": "live nba games"}


def test_odds_history_path_and_query():
    client = make_client([{"body": {"event_id": 1, "movements": []}}])
    client.events.odds_history(1, bookmaker="fanduel", limit=50)
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/events/1/odds/history"
    assert q == {"bookmaker": "fanduel", "limit": "50"}


def test_player_events_maps_from_keyword():
    client = make_client([{"body": {"player_id": 1, "data": []}}])
    client.players.events(1, from_="2026-01-01", to="2026-02-01", status="final")
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/players/1/events"
    assert q == {"from": "2026-01-01", "to": "2026-02-01", "status": "final"}


def test_webhook_create_posts_json_body():
    client = make_client([{"body": {"id": 1, "signing_secret": "whsec_x"}}])
    client.webhooks.create(url="https://you.example.com/hook", event_types=["score", "line_move"], sport="nhl")
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/v1/webhooks"
    assert req.headers["Content-Type"] == "application/json"
    body = json.loads(req.body)
    assert body["url"] == "https://you.example.com/hook"
    assert body["event_types"] == ["score", "line_move"]
    assert body["sport"] == "nhl"


def test_webhook_delete_uses_delete_method():
    client = make_client([{"body": {"deleted": True, "id": 7}}])
    client.webhooks.delete(7)
    req = only_call(client)
    assert req.method == "DELETE"
    assert urlparse(req.url).path == "/v1/webhooks/7"


def test_webhook_deliveries_path_and_query():
    client = make_client([{"body": {"data": [], "next_after_id": None}}])
    client.webhooks.deliveries(
        7, after_id=100, limit=10, success=False, given_up=True, event_type="score"
    )
    path, q = _path_and_query(only_call(client))
    assert path == "/v1/webhooks/7/deliveries"
    assert q == {
        "after_id": "100",
        "limit": "10",
        "success": "false",
        "given_up": "true",
        "event_type": "score",
    }


def test_webhook_deliveries_omits_after_id_when_not_provided():
    client = make_client([{"body": {"data": [], "next_after_id": None}}])
    client.webhooks.deliveries(7)
    _, q = _path_and_query(only_call(client))
    assert "after_id" not in q
    assert "success" not in q


def test_agent_key_create_body_and_credits_paths():
    client = make_client([{"body": {"id": 1, "key": "lmfy-new"}}])
    client.agent.keys.create(name="ci", scopes=["nfl", "nba"], expires_in_days=30)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/api/agent/keys"
    body = json.loads(req.body)
    assert body == {"name": "ci", "scopes": ["nfl", "nba"], "expires_in_days": 30}


def test_agent_credits_topup_posts_pack_id():
    client = make_client([{"body": {"success": True}}])
    client.agent.credits.topup(3)
    req = only_call(client)
    assert req.method == "POST"
    assert urlparse(req.url).path == "/api/agent/credits/topup"
    assert json.loads(req.body) == {"pack_id": 3}


def test_iterate_events_uses_events_key_across_pages():
    client = make_client(
        [
            {"body": {"events": [{"id": 1}], "next_after_id": 1}},
            {"body": {"events": [{"id": 2}], "next_after_id": None}},
        ]
    )
    ids = [e["id"] for e in client.events.iterate(sport="nhl", limit=1)]
    assert ids == [1, 2]
