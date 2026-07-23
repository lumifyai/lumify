# @lumifyai/sdk

Official TypeScript/JavaScript client for [Lumify](https://lumify.ai), the
agent-ready sports intelligence API — schedules, live scores, odds, line
movement, public betting splits, and AI bet intelligence across MLB, NFL,
NCAAF, NCAAB, NBA, NHL, tennis, and soccer (FIFA World Cup + MLS, EPL, La Liga,
Serie A, Bundesliga, Ligue 1, and UEFA Champions League).

> **Status:** v0.2.0 — the data-plane slice (sports/seasons/events/teams/players,
> SSE streaming, webhooks with automatic delivery retries, agent onboarding,
> pre-call cost estimates). Same data as the REST API and the
> [MCP server](https://www.npmjs.com/package/@lumifyai/mcp) — this SDK *is* the
> typed REST path, not a third implementation.

## Install

```bash
npm install @lumifyai/sdk
```

Requires Node.js 18+ (uses native `fetch` and Web Crypto — zero runtime
dependencies) or any modern browser/edge runtime.

## Quick start

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: process.env.LUMIFY_API_KEY! });

const { sports } = await client.sports.list();

const event = await client.events.get(12345, {
  includeOdds: true,
  includeIntelligence: true,
});
console.log(event.status, event.intelligence?.bets);
```

Create a key at <https://lumify.ai/api-keys> or programmatically via
`client.agent.keys.create()`.

## Resources

```ts
client.sports.list() / client.seasons.list()
client.events.list(filters) / .get(id, { includeOdds?, includeIntelligence?, bookmaker? })
client.events.batchGet(ids, { includeOdds?, includeIntelligence?, bookmaker? })  // up to 25 ids in one call
client.events.query(text, { limit? })   // natural-language search, e.g. "live nfl games today"
client.events.odds(id) / .oddsHistory(id) / .score(id) / .intelligence(id) / .splits(id)
client.events.stream(id)          // SSE async iterator of live score updates
client.events.paginate(filters) / .iterate(filters)   // cursor pagination helpers
client.teams.list(filters) / .get(id)
client.players.list(filters) / .get(id) / .events(id, filters)
client.webhooks.create() / .list() / .delete(id) / .deliveries(id) / .verify(secret, header, rawBody)
client.agent.keys.create() / .list() / .revoke(id)
client.agent.credits.get() / .listPacks() / .topup(packId)
client.estimate.cost(calls) / .listTools()   // pre-call credit-cost estimate, always free — see below
```

### Estimating cost before you call

`client.estimate.cost(...)` tells you the credit range a planned call (or
batch of calls) will cost *without making it* — costs are data-dependent
(e.g. odds not yet posted are free), so each result is a `min_credits` /
`max_credits` range, not a single number. Always free to call:

```ts
const result = await client.estimate.cost([
  { tool: "get_event", arguments: { event_id: 12345, include_odds: true } },
  { tool: "batch_get_events", arguments: { event_ids: [1, 2, 3] } },
]);
result.total_min_credits; // cheapest realistic total across all calls
result.total_max_credits; // priciest realistic total across all calls
```

Every method maps 1:1 to a REST endpoint and returns the same JSON shape you'd
get from `curl` — see <https://lumify.ai/docs/reference> for full field docs.

## Pagination

List endpoints are cursor-paginated (`after_id`/`limit`, max 100). Use the
iterator helpers instead of tracking cursors by hand:

```ts
for await (const event of client.events.iterate({ sport: "nfl", status: "scheduled" })) {
  console.log(event.id, event.starts_at);
}

// Or page-by-page (events pages use `events`, not `data`):
for await (const page of client.events.paginate({ sport: "nfl" }, { limit: 50 })) {
  console.log(page.events?.length, "events, next cursor:", page.next_after_id);
}
```

## Batch event lookup

Already have a list of event ids (e.g. from `client.events.list()`) and want
full detail for each? `batchGet` fetches up to 25 in a single round-trip
instead of one `get` per event:

```ts
const result = await client.events.batchGet([101, 102, 999999999], { includeOdds: true });
console.log(result.total, "found;", result.not_found, "missing");
for (const event of result.events) console.log(event.id, event.status);
```

Duplicate ids are billed once; ids that don't exist are returned under
`not_found` and cost nothing — credits are the sum of each event's normal
`GET /v1/events/{id}` cost, with the same billing-fairness rules (unavailable
odds/intelligence stay free).

## Natural-language search

`query` maps free text to the same filters `client.events.list()` accepts —
sport, status, and date/date-range — using a small, deterministic, rule-based
mapper (not an LLM call). Costs 1 credit, same as `list()`:

```ts
const result = await client.events.query("live nfl games today", { limit: 5 });
console.log(result.interpreted);          // { sport: "nfl", status: "inprogress", date: "2026-07-15", ... }
console.log(result.equivalent_request);   // "GET /v1/events?sport=nfl&status=inprogress&date=2026-07-15"
console.log(result.unrecognized_terms);   // words that didn't map to a filter
for (const event of result.events ?? []) console.log(event.id, event.status);
```

## Live score streaming (SSE)

```ts
for await (const evt of client.events.stream(eventId)) {
  if (evt.event === "score") console.log(evt.data.status, evt.data.clock);
  if (evt.event === "done") break;
}
```

Cheaper than polling `client.events.score(id)` — the server only emits on
change, plus periodic keep-alives, and closes when the event finishes.

## Webhooks

```ts
const sub = await client.webhooks.create({ url: "https://you.example.com/hooks/lumify" });
// sub.signing_secret ("whsec_...") is returned once — store it.

// In your webhook handler, verify against the *raw* request body:
await client.webhooks.verify(signingSecret, req.header("Lumify-Signature")!, rawBody);
```

`verify()` throws `WebhookSignatureError` (bad format, signature mismatch, or a
stale/replayed timestamp) — treat that as "reject with 4xx", not a crash.

Deliveries that fail transiently (5xx, 429, or a timeout) are automatically
retried with exponential backoff (30s/5m/30m/2h/6h). Check
`client.webhooks.deliveries(id)` for delivery history, including retries
(linked via `parent_delivery_id`) and whether Lumify has given up (`given_up`):

```ts
const history = await client.webhooks.deliveries(sub.id!);
for (const d of history.data ?? []) {  // newest first
  console.log(d.attempt, d.status_code, d.success, d.given_up);
}
```

## Errors

Every non-2xx response throws a typed subclass of `LumifyError` — switch on
`err.code` (the stable machine-readable slug), not `err.message`:

```ts
import { NotFoundError, RateLimitError, ValidationError } from "@lumifyai/sdk";

try {
  await client.events.get(999999999);
} catch (err) {
  if (err instanceof NotFoundError) { /* ... */ }
  if (err instanceof RateLimitError) console.log("retry after", err.retryAfter, "s");
  if (err instanceof ValidationError) console.log(err.fieldErrors);
}
```

`AuthenticationError` (401), `PaymentError` (402), `PermissionError` (403, has `.upgradeUrl` on
sport-scope denials), `NotFoundError` (404), `ValidationError` (422, has
`.fieldErrors`), `RateLimitError` (429, has `.retryAfter` from the envelope or
`Retry-After` header), `APIError` (5xx), and `ConnectionError` (network/timeout,
never reached the server) all extend `LumifyError` (`.code`, `.status`, `.docUrl`,
`.requestId`).

GET requests are automatically retried (default: 2 attempts) with exponential
backoff on `429`/`5xx`/network failures, honoring `Retry-After`. Non-idempotent
requests (`POST`/webhook & key creation) are never auto-retried. Configure with
`maxRetries` / `timeoutMs` on the `Lumify` constructor.

## Credits and rate limits

Every successful response carries `X-Credits-Used`, `X-Credits-Remaining`, and
`X-RateLimit-*` headers. Read them via `getMeta()` (attached as hidden metadata
on the returned object, so it never pollutes `JSON.stringify` or your own
types):

```ts
import { getMeta } from "@lumifyai/sdk";

const odds = await client.events.odds(eventId);
const meta = getMeta(odds);
console.log(meta?.creditsUsed, meta?.rateLimitRemaining);
```

Queries for data that isn't available yet (e.g. odds not yet posted) return
`creditsUsed: 0` — you're never charged for a "not available" read.

## Sync with REST, MCP, and the OpenAPI contract

This SDK's response types (`src/generated/models.ts`) are generated from
Lumify's live OpenAPI schema, not hand-maintained — see
`scripts/export_openapi_sdk.py` (repo root) and `scripts/gen-models.mjs`
(this package). CI fails if either is stale, so the SDK can't silently drift
from what the API actually returns. The client ergonomics (this README's
resource shape, pagination/SSE/webhook helpers) are hand-written on top.

```bash
python scripts/export_openapi_sdk.py            # regenerate the schema slice
node clients/lumify-sdk/scripts/gen-models.mjs   # regenerate the TS models
```

## Development

```bash
npm install
npm run build   # tsc -> dist/
npm test        # build + node --test
```

## License

[MIT](./LICENSE) © 2026 Lumify AI

## Related

- Docs: <https://lumify.ai/docs>
- MCP server (for AI agent runtimes): [`@lumifyai/mcp`](https://www.npmjs.com/package/@lumifyai/mcp)
- npm: <https://www.npmjs.com/package/@lumifyai/sdk>
