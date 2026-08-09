# Lumify API Cheat Sheet

> Canonical URL: https://lumify.ai/docs/cheat-sheet
> HTML twin: https://lumify.ai/docs/cheat-sheet

One-page re-entry for humans and a compact context block for LLMs.

## Base URL & auth

```
Base URL:  https://lumify.ai
Auth:      Authorization: Bearer lmfy-...
Instant key (no signup): https://lumify.ai/docs/ai
Persistent free tier:    https://lumify.ai/register  (1,000 credits)
```

## Response envelope & headers

- JSON everywhere. Cursor pagination: `?after_id=<id>&limit=<n>` (max 100) → `next_after_id`.
- Timestamps are ISO-8601 UTC with trailing `Z`.
- Every response: `X-RateLimit-{Limit,Remaining,Reset}`, `X-Credits-Used`, `X-Credits-Remaining` (when resolvable).
- Odds / splits / intelligence not ready yet → `200` with `available: false` and **0 credits**.

## Credits (1-credit default)

| Call | Cost |
|---|---|
| Standard (events, scores, odds, splits, intelligence, players) | **1 credit** |
| Multi-bookmaker odds (`bookmaker=all` or a list) | **2 credits** |
| Compound `include_odds` / `include_intelligence` | **+1–2 credits** |
| SSE stream open | **1 credit** |
| `POST /v1/estimate` | **Free** |
| Errors (4xx/5xx) and `available: false` | **Free** |

Rate limits (sliding 60s): Free **20**/min · PAYG **60**/min · Growth **120**/min.

## Hero query

```bash
curl -s "https://lumify.ai/v1/events?sport=mlb&status=scheduled&limit=5" \
  -H "Authorization: Bearer lmfy-YOUR_KEY"

curl -s "https://lumify.ai/v1/events/EVENT_ID?include_odds=true&include_intelligence=true" \
  -H "Authorization: Bearer lmfy-YOUR_KEY"

curl -s -X POST "https://lumify.ai/v1/estimate" \
  -H "Authorization: Bearer lmfy-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"calls":[{"tool":"get_event","arguments":{"event_id":12345,"include_odds":true,"include_intelligence":true}}]}'
```

Intelligence sports today: **MLB, NFL, NCAA Football, ATP/WTA tennis, FIFA World Cup soccer, MLS**.
Splits: **MLB, NBA, NHL, NFL**.

## Error shape

```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded",
    "status": 429,
    "doc_url": "https://lumify.ai/docs/reference#error-codes",
    "retry_after": 23
  },
  "detail": "Rate limit exceeded"
}
```

Switch on `error.code`, not `message`.

## MCP

```
URL:  https://lumify.ai/mcp
Auth: Authorization: Bearer lmfy-...
18 tools — initialize / tools/list / ping free; tools/call metered like REST.
```

## Go deeper

- https://lumify.ai/llms.txt (~4.9k tokens, measured)
- https://lumify.ai/llms-full.txt (~11k tokens GEO, measured)
- https://lumify.ai/docs/llms-full.txt (~54k tokens technical, measured)
- https://lumify.ai/openapi-llms.txt (~5.9k tokens endpoint dump, measured)
- https://lumify.ai/docs/ai
- https://lumify.ai/docs/best-practices
- https://lumify.ai/docs/rate-limits
- https://lumify.ai/changelog.json
