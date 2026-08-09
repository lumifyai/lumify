# Lumify Rate Limits & Pagination

> Canonical URL: https://lumify.ai/docs/rate-limits.md
> HTML twin: https://lumify.ai/docs/rate-limits

One page an agent can fetch for the complete picture — per-tier limits, sliding-window rules, cursor semantics, and stream caps.

## Per-tier limits

Limits are enforced **per API key** on a **sliding 60-second window**. There is no separate hourly quota.

| Plan | Requests / minute | Notes |
|---|---|---|
| Free Tier | 20 | Plus a rolling 24h anti-abuse credit spend cap |
| Pay As You Go | 60 | Metered credits; no monthly credit cap |
| Growth | 120 | 10,000 credits included / month |
| Enterprise | Custom | Negotiated |

Instant trial keys (no signup) use a tighter anonymous limit. Persistent free-tier keys use the Free row above.

## Headers on every response

| Header | Meaning |
|---|---|
| `X-RateLimit-Limit` | Max requests in the current 60s window |
| `X-RateLimit-Remaining` | Requests left in the window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `X-Credits-Used` | Credits charged for this call (0 on errors / available:false) |
| `X-Credits-Remaining` | Best-effort balance after the call (omitted when unlimited / unknown) |
| `Retry-After` | Seconds to wait (on 429 responses) |

## 429 behavior

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

No credits are consumed on a 429. Switch on `error.code` and sleep `retry_after` before retrying.

## Cursor pagination

- Query params: `?after_id=<last_id>&limit=<n>`
- `limit` range: **1–100** (defaults vary by endpoint; events default 25)
- Response field: `next_after_id` — pass it back as `after_id`; `null` means last page
- Cursor is stable even if new rows are ingested between pages
- **Caveat:** `sort=status` on events does **not** support `after_id` — combining them returns **400**. Use `sort=time` (default) for cursor pagination.

```python
import requests

after_id = None
while True:
    params = {"sport": "nba", "limit": 100}
    if after_id:
        params["after_id"] = after_id
    r = requests.get(
        "https://lumify.ai/v1/events",
        headers={"Authorization": "Bearer lmfy-YOUR_KEY"},
        params=params,
        timeout=30,
    )
    r.raise_for_status()
    body = r.json()
    for event in body["events"]:
        process(event)
    after_id = body.get("next_after_id")
    if not after_id:
        break
```

## SSE concurrency

- Max **5 concurrent streams** per API key
- Each connection costs **1 credit** to open
- Connections close after **5 minutes**; the server sends `event: reconnect` first
- Both SDKs' stream helpers reopen automatically

Related: https://lumify.ai/docs/best-practices.md · https://lumify.ai/docs/cheat-sheet.md
