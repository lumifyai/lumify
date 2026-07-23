# Quick Start Guide

Make your first Lumify Sports Intelligence API call in under 5 minutes.

Lumify is an agent-ready sports intelligence API. It returns structured schedules,
live scores, odds, betting splits, and AI-generated bet intelligence (confidence
scores, signal breakdowns, and narratives) across multiple sports.

## 1. Create Your Account

1. Sign up at [lumify.ai/register](https://lumify.ai/register)
2. Verify your email address
3. Your **Free Tier** account includes **1,000 credits** that never expire — no credit card required

## 2. Create an API Key

1. Log in and open the [API Keys dashboard](https://lumify.ai/api-keys)
2. Click **Create key**
3. Copy the key immediately — it is shown **only once**

Keys use the format `lmfy-xxxxxx.yyyyyyyy…` and are passed as a Bearer token on every request.

## 3. Make Your First Call

All `/v1/*` endpoints require the `Authorization: Bearer` header and return JSON.

### List today's scheduled MLB games

```bash
curl "https://lumify.ai/v1/events?sport=mlb&status=scheduled" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response:**
```json
{
  "events": [
    {
      "id": 9199,
      "name": "Atlanta Braves @ San Diego Padres",
      "sport": "mlb",
      "league": "mlb",
      "status": "scheduled",
      "starts_at": "2026-06-23 23:40:00",
      "venue": { "id": 42, "name": "Petco Park", "city": "San Diego" }
    }
  ],
  "total": 1,
  "next_after_id": null
}
```

### Fetch bet intelligence for an event

```bash
curl "https://lumify.ai/v1/events/9199/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response (abbreviated):**
```json
{
  "event_id": 9199,
  "available": true,
  "has_recommend": true,
  "analyst_take": "Sharp money has moved toward San Diego through the morning...",
  "bets": [
    {
      "bet_type": "ML_P1",
      "player_name": "San Diego Padres",
      "tier": "moderate",
      "confidence_score": 0.611,
      "rationale": ["Strong Starting Pitching Edge (20/25)", "Deep Research supports this bet (+3.1pp)"],
      "attribution": ["pitching_edge", "deep_research"]
    }
  ]
}
```

## 4. Explore the Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/sports` | Supported sports, leagues, and current seasons |
| `GET /v1/events` | Paginated, filterable event list |
| `GET /v1/events/{id}` | Full event detail (optionally `?include_odds=true`, `?include_intelligence=true`) |
| `GET /v1/events/{id}/score` | Lightweight live-score snapshot |
| `GET /v1/events/{id}/odds` | Current moneyline, spread, and total lines |
| `GET /v1/events/{id}/odds/history` | Line movement history |
| `GET /v1/events/{id}/splits` | Public betting splits (bets % vs handle %) |
| `GET /v1/events/{id}/intelligence` | Confidence scores, signals, and narratives |
| `GET /v1/players` | Player/team lookup |
| `GET /v1/players/{id}` | Player or team profile |
| `GET /v1/players/{id}/events` | Player/team schedule and results |

## 5. Credits & Rate Limits

- Each API call costs **1 credit**. Compound calls add credits: `include_odds=true` or
  `include_intelligence=true` add **+1 credit** each; multi-bookmaker odds
  (`bookmaker=all` or a comma-separated list) cost **2 credits**.
- Failed requests (`4xx`/`5xx`) do not consume credits.
- Rate limits are enforced per API key on a sliding 60-second window. Every response
  includes `X-RateLimit-*` headers so you can throttle proactively. Exceeding the limit
  returns `429 Too Many Requests` with a `retry_after` value.

## Next Steps

- [API Reference](https://lumify.ai/docs) — full endpoint documentation with curl, Python, and JavaScript examples
- [Pricing](https://lumify.ai/pricing) — plans and credit allowances
- [FAQ](https://lumify.ai/faq) — data coverage, billing, and integration questions

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `401 Unauthorized` | Check the key is correct, active, and passed as `Authorization: Bearer lmfy-…` |
| `402 Payment Required` | Credits exhausted or daily free-tier cap hit — switch on `error.code` (`insufficient_credits`, `daily_credit_cap_exceeded`) and follow `upgrade_url` / `topup_url`. `daily_credit_cap_exceeded` includes `resets_at` (rolling 24h window) |
| `429 Too Many Requests` | You exceeded your plan's rate limit — back off and retry after the window resets |
| `available: false` on intelligence/odds | The pipeline has not computed data for this event yet — poll again shortly |

Need help? Contact [support@lumify.ai](mailto:support@lumify.ai)
