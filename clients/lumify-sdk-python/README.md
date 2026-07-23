# lumify-sdk

Official Python client for [Lumify](https://lumify.ai), the agent-ready sports
intelligence API — schedules, live scores, odds, line movement, public betting
splits, and AI bet intelligence across MLB, NFL, NCAAF, NCAAB, NBA, NHL,
tennis, and soccer (FIFA World Cup + MLS, EPL, La Liga, Serie A, Bundesliga,
Ligue 1, and UEFA Champions League).

> **Status:** v0.2.0 — the data-plane slice (sports/seasons/events/teams/players,
> SSE streaming, webhooks with automatic delivery retries, agent onboarding,
> pre-call cost estimates), now with both sync (`Lumify`) and async
> (`AsyncLumify`) clients. Same data as the REST API, the
> [TypeScript SDK](https://www.npmjs.com/package/@lumifyai/sdk), and the
> [MCP server](https://www.npmjs.com/package/@lumifyai/mcp) — this SDK *is* the
> typed REST path, not a third implementation.

## Install

```bash
pip install lumify-sdk
```

Requires Python 3.8+. **Zero runtime dependencies** for the sync client — the
transport is stdlib `urllib` and signatures use stdlib `hmac`/`hashlib`. The
async client needs the optional `httpx` dependency (see below).

## Quick start

```python
import os
from lumify import Lumify

client = Lumify(api_key=os.environ["LUMIFY_API_KEY"])

sports = client.sports.list()

event = client.events.get(12345, include_odds=True, include_intelligence=True)
print(event["status"], event.get("intelligence"))
```

Create a key at <https://lumify.ai/api-keys> or programmatically via
`client.agent.keys.create()`.

## Async client

`lumify.aio.AsyncLumify` mirrors `Lumify` method-for-method as `async`/`await`
— same resources, same REST contract, same error types. It needs the optional
`httpx` dependency for its default transport:

```bash
pip install "lumify-sdk[asyncio]"
```

```python
import asyncio
import os
from lumify.aio import AsyncLumify

async def main():
    async with AsyncLumify(api_key=os.environ["LUMIFY_API_KEY"]) as client:
        sports, event = await asyncio.gather(
            client.sports.list(),
            client.events.get(12345, include_odds=True),
        )
        async for e in client.events.iterate(sport="nfl", status="scheduled"):
            print(e["id"], e["starts_at"])

asyncio.run(main())
```

It's a separate import path (`lumify.aio`, not exported from top-level
`lumify`) so importing the zero-dependency sync client never pulls in `httpx`.
Use `async with` (or `await client.aclose()`) to release the pooled HTTP
connection. Pagination helpers (`.paginate()`/`.iterate()`) are async
generators; `client.events.stream(id)` is an async iterator over SSE score
updates; `client.webhooks.verify(...)` stays synchronous (it's pure local
HMAC computation, nothing to await).

## Resources

```python
client.sports.list()  # client.seasons.list()
client.events.list(**filters)  # .get(id, include_odds=?, include_intelligence=?, bookmaker=?)
client.events.batch_get(event_ids)  # up to 25 ids in one round-trip; see below
client.events.query(text, limit=None)  # natural-language search, e.g. "live nfl games today"
client.events.odds(id)  # .odds_history(id) / .score(id) / .intelligence(id) / .splits(id)
client.events.stream(id)              # SSE iterator of live score updates
client.events.paginate(**filters)     # .iterate(**filters) — cursor pagination helpers
client.teams.list(**filters)  # .get(id)
client.players.list(**filters)  # .get(id) / .events(id, **filters)
client.webhooks.create(url=...)  # .list() / .delete(id) / .deliveries(id) / .verify(secret, header, raw_body)
client.agent.keys.create()  # .list() / .revoke(id)
client.agent.credits.get()  # .list_packs() / .topup(pack_id)
client.estimate.cost(calls)  # pre-call credit-cost estimate, always free — see below
client.estimate.list_tools()  # tool names .cost() understands
```

### Estimating cost before you call

`client.estimate.cost(...)` tells you the credit range a planned call (or
batch of calls) will cost *without making it* — costs are data-dependent
(e.g. odds not yet posted are free), so each result is a `min_credits` /
`max_credits` range, not a single number. Always free to call:

```python
result = client.estimate.cost([
    {"tool": "get_event", "arguments": {"event_id": 12345, "include_odds": True}},
    {"tool": "batch_get_events", "arguments": {"event_ids": [1, 2, 3]}},
])
result["total_min_credits"]  # cheapest realistic total across all calls
result["total_max_credits"]  # priciest realistic total across all calls
```

Every method maps 1:1 to a REST endpoint and returns the same JSON shape you'd
get from `curl` (a plain `dict`, typed as the matching model in
`lumify.models`) — see <https://lumify.ai/docs/reference> for full field docs.

## Pagination

List endpoints are cursor-paginated (`after_id`/`limit`, max 100). Use the
iterator helpers instead of tracking cursors by hand:

```python
for event in client.events.iterate(sport="nfl", status="scheduled"):
    print(event["id"], event["starts_at"])

# Or page-by-page (events pages use "events", not "data"):
for page in client.events.paginate(sport="nfl", limit=50):
    print(len(page.get("events", [])), "events, next cursor:", page.get("next_after_id"))
```

Standalone helpers `paginate()` / `iterate_items()` are also exported for
custom fetchers.

## Batch event lookup

Already have a list of event ids (e.g. from `client.events.list()`) and want
full detail for each? `batch_get` fetches up to 25 in a single round-trip
instead of one `GET` per event:

```python
result = client.events.batch_get([101, 102, 999999999], include_odds=True)
print(result["total"], "found;", result["not_found"], "missing")
for event in result["events"]:
    print(event["id"], event["status"])
```

Duplicate ids are billed once; ids that don't exist are returned under
`not_found` and cost nothing — credits are the sum of each event's normal
`GET /v1/events/{id}` cost, with the same billing-fairness rules (unavailable
odds/intelligence stay free).

## Natural-language search

`query` maps free text to the same filters `client.events.list()` accepts —
sport, status, and date/date-range — using a small, deterministic, rule-based
mapper (not an LLM call). Costs 1 credit, same as `list()`:

```python
result = client.events.query("live nfl games today", limit=5)
print(result["interpreted"])          # {"sport": "nfl", "status": "inprogress", "date": "2026-07-15", ...}
print(result["equivalent_request"])   # "GET /v1/events?sport=nfl&status=inprogress&date=2026-07-15"
print(result["unrecognized_terms"])   # words that didn't map to a filter
for event in result["events"]:
    print(event["id"], event["status"])
```

## Live score streaming (SSE)

```python
for evt in client.events.stream(event_id):
    if evt.event == "score":
        print(evt.data["status"], evt.data.get("clock"))
    if evt.event == "done":
        break
```

Cheaper than polling `client.events.score(id)` — the server only emits on
change, plus periodic keep-alives, and closes when the event finishes.

## Webhooks

```python
sub = client.webhooks.create(url="https://you.example.com/hooks/lumify")
# sub["signing_secret"] ("whsec_...") is returned once — store it.

# In your webhook handler, verify against the *raw* request body:
client.webhooks.verify(signing_secret, request.headers["Lumify-Signature"], raw_body)
```

`verify()` raises `WebhookSignatureError` (bad format, signature mismatch, or a
stale/replayed timestamp) — treat that as "reject with 4xx", not a crash.

Deliveries that fail transiently (5xx, 429, or a timeout) are automatically
retried with exponential backoff (30s/5m/30m/2h/6h). Check `client.webhooks.deliveries(id)`
to see delivery history, including retries (linked via `parent_delivery_id`)
and whether Lumify has given up (`given_up`):

```python
history = client.webhooks.deliveries(sub["id"])
for d in history["data"]:  # newest first
    print(d["attempt"], d["status_code"], d["success"], d["given_up"])
```

## Errors

Every non-2xx response raises a typed subclass of `LumifyError` — switch on
`err.code` (the stable machine-readable slug), not `str(err)`:

```python
from lumify import NotFoundError, RateLimitError, ValidationError

try:
    client.events.get(999999999)
except NotFoundError:
    ...
except RateLimitError as err:
    print("retry after", err.retry_after, "s")
except ValidationError as err:
    print(err.field_errors)
```

`AuthenticationError` (401), `PaymentError` (402), `PermissionError` (403, has
`.upgrade_url` on sport-scope denials), `NotFoundError` (404), `ValidationError`
(422, has `.field_errors`), `RateLimitError` (429, has `.retry_after` from the
envelope or `Retry-After` header), `APIError` (5xx), and `ConnectionError`
(network/timeout, never reached the server) all extend `LumifyError`
(`.code`, `.status`, `.doc_url`, `.request_id`).

GET requests are automatically retried (default: 2 attempts) with exponential
backoff on `429`/`5xx`/network failures, honoring `Retry-After`. Non-idempotent
requests (`POST`/webhook & key creation) are never auto-retried. Configure with
`max_retries` / `timeout` on the `Lumify` constructor.

## Credits and rate limits

Every successful response carries `X-Credits-Used`, `X-Credits-Remaining`, and
`X-RateLimit-*` headers. Read them via `get_meta()` (attached out-of-band on the
returned object, so it never pollutes `json.dumps` or iteration):

```python
from lumify import get_meta

odds = client.events.odds(event_id)
meta = get_meta(odds)
print(meta.credits_used, meta.rate_limit_remaining)
```

Queries for data that isn't available yet (e.g. odds not yet posted) return
`credits_used == 0` — you're never charged for a "not available" read.

## Sync with REST, MCP, and the OpenAPI contract

This SDK's response types (`lumify/models.py`) are generated from the *same*
filtered OpenAPI slice the TypeScript SDK uses
(`clients/lumify-sdk/openapi/openapi.sdk.json`, produced by
`scripts/export_openapi_sdk.py` at the repo root), not hand-maintained. CI fails
if the models are stale, so the two SDKs can't disagree with each other or drift
from what the API returns. A shared cross-surface probe matrix
(`tests/fixtures/agent_contract.json`) additionally asserts this SDK builds the
exact REST request that REST and MCP agree on. The client ergonomics (this
README's resource shape, pagination/SSE/webhook helpers) are hand-written.

```bash
python scripts/export_openapi_sdk.py                       # regenerate the schema slice
python clients/lumify-sdk-python/scripts/gen_models.py      # regenerate the Python models
```

## Development

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

[MIT](./LICENSE) © 2026 Lumify AI

## Related

- Docs: <https://lumify.ai/docs>
- TypeScript SDK: [`@lumifyai/sdk`](https://www.npmjs.com/package/@lumifyai/sdk)
- MCP server (for AI agent runtimes): [`@lumifyai/mcp`](https://www.npmjs.com/package/@lumifyai/mcp)
