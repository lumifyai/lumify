# Lumify Documentation

> Canonical URL: https://lumify.ai/docs.md
> HTML twin: https://lumify.ai/docs

Quickstart, authentication, rate limits, and versioning for the sports intelligence API.

<!-- Auto-generated from api/templates/public/docs.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

### Start here

- [**Cheat sheet** Auth, envelope, and the hero query on one page.](/docs/cheat-sheet)

- [**Understanding odds** Read a real moneyline and a player-prop ticket.](/docs/understanding-odds)

- [**Glossary** Juice, moneyline, handle — mapped to Lumify fields.](/docs/glossary)

- [**Sports Coverage** What is live on each sport, surface by surface.](/docs/sports-coverage)

- [**5-minute walkthrough** Longer first-call path, credits, and troubleshooting.](/docs/getting-started/quick-start)

<!-- #start -->

# Quickstart

Get your first Lumify API response in under 60 seconds.

### 1 — Get your API key

Click **Get instant trial key** in the banner above — no signup required. Keys look like lmfy-xxxxxx.yyyy… and are passed as a Bearer token on every request. For a persistent account, create a key in your [API Keys dashboard](/api-keys).

### 2 — Make your first request

Fetch today's MLB schedule:

```bash
curl "https://lumify.ai/v1/events?sport=mlb&status=scheduled" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "events": [
    {
      "id":         9199,
      "name":       "Atlanta Braves @ San Diego Padres",
      "sport":      "mlb",
      "league":     "mlb",
      "status":     "scheduled",
      "starts_at":  "2026-06-23T23:40:00Z",
      "venue":      { "id": 42, "name": "Petco Park", "city": "San Diego" }
    }
  ],
  "total":          1,
  "next_after_id":  null
}
```

That's a successful call — grab any id from events for the next request.

> **Note:** That's it. From here, explore the full [API Reference](/docs/reference). Common next steps: [look up a player](/docs/reference#players), [fetch live odds](/docs/reference#event-odds), or [poll a live score](/docs/reference#event-score).

### Next (2 minutes) — Get bet intelligence for a game

Take any id from the events response and fetch its intelligence payload. On MLB, tennis, soccer, NFL, and NCAAF that includes predictive bets[] (probability / fair_price). On NBA, NCAAB, and NHL, available is often false and bets[] is empty — still read forecasts[], or scan the daily board with GET /v1/intelligence/forecasts (MCP list_forecasts). How to read that payload: [Understanding Odds](/docs/understanding-odds). How forecasts work: [/docs/forecasts](/docs/forecasts).

```bash
curl "https://lumify.ai/v1/events/{id}/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Prefer a longer walkthrough? See the [Quick Start Guide](/docs/getting-started/quick-start). Agents: [/docs/getting-started/quick-start.md](/docs/getting-started/quick-start.md).

<!-- #quickstart -->

# Introduction

 The Lumify v1 API gives you structured, real-time sports intelligence — schedules, live scores, team and player data — all in one consistent interface. Every endpoint is authenticated with a bearer token and returns JSON.

> **Note:** Base URL  https://lumify.ai

All timestamps are ISO-8601 UTC strings with a T and a Z (2026-08-12T14:42:19Z). Date-only fields use YYYY-MM-DD. All request bodies and responses use UTF-8 JSON.

 Prefer an interactive explorer or a machine-readable contract? The full OpenAPI schema is at
 [/openapi.json](/openapi.json) —
 browse it live in [ReDoc](/api/redoc)
 or [Swagger UI](/api/docs).

<!-- #introduction -->

## Authentication

Every /v1/* request must include a valid Lumify API key as a **Bearer token**. Keys are created in your [dashboard](/api-keys) and follow the format lmfy-xxxxxx.yyyyyyyy…

> **Warning:** You don't have any API keys yet. Create one to start making requests.
 [Create API key →](/api-keys)

### Request header

| Header | Value |
| --- | --- |
| Authorization | Bearer YOUR_API_KEY |

### Example

```bash
curl https://lumify.ai/v1/events \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Auth errors

| Status | Reason | When it occurs |
| --- | --- | --- |
| 401 | Unauthorized | Missing, malformed, invalid, inactive, or expired API key. Expired keys return the same 401 as invalid keys (no expiry leak). Check Authorization: Bearer lmfy-…. |
| 403 | Forbidden | Valid key but denied for this resource — e.g. sport scope not granted (error.code = sport_scope_denied). See upgrade_url in the error body. |

<!-- #authentication -->

## Rate Limits

Limits are enforced per API key on a sliding 60-second window. Every response — success or error — includes the following headers so you can throttle proactively:

| Response header | Description |
| --- | --- |
| X-RateLimit-Limit | Maximum requests allowed in the window |
| X-RateLimit-Remaining | Requests remaining in the current window |
| X-RateLimit-Reset | Unix timestamp when the window resets |
| X-Credits-Used | Credits charged for this successful authenticated call (variable-cost endpoints may be > 1) |
| X-Credits-Remaining | Best-effort remaining balance after this call. Omitted when the plan is unlimited (pure metered PAYG) or the balance cannot be resolved. |

### Limits by plan

| Plan | Requests / minute |
| --- | --- |
| Free Tier | 20 |
| Pay As You Go | 60 |
| Growth | 120 |
| Enterprise | Custom |

Limits are enforced per API key on a sliding 60-second window. Exceeding your limit returns 429 Too Many Requests. No credits are consumed on a 429 response.

### 429 response

```json
{
  "error": {
    "code":         "rate_limit_exceeded",
    "message":      "Rate limit exceeded",
    "status":       429,
    "doc_url":      "https://lumify.ai/docs/reference#error-codes",
    "retry_after":  23
  },
  "detail": "Rate limit exceeded"
}
```

> **Tip:** Best practice: Read X-RateLimit-Remaining on every response and back off before you hit zero. When you receive a 429, wait error.retry_after seconds (also mirrored in the Retry-After header) before retrying. Switch on error.code.

<!-- #rate-limits -->

## Versioning

The API version is part of the path (/v1/…). We guarantee backwards compatibility within a major version. Breaking changes ship under a new prefix (/v2/…) with at least 90 days notice.

<!-- #versioning -->
