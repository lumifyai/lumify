# First API Call in 5 Minutes

> Canonical URL: https://lumify.ai/docs/getting-started/quick-start.md
> HTML twin: https://lumify.ai/docs/getting-started/quick-start

Make your first Lumify Sports Intelligence API call. Lumify returns structured
schedules, live scores, odds, betting splits, and predictive bet intelligence
(probability, fair price, and Price overlay) across multiple sports.

## 1. Get your API key

Click **Get instant trial key** on the [HTML Quick Start](https://lumify.ai/docs/getting-started/quick-start)
or any docs page — no signup required. Keys look like `lmfy-xxxxxx.yyyyyyyy…`
and are passed as a Bearer token on every request.

For a persistent account:

1. Sign up at [lumify.ai/register](https://lumify.ai/register)
2. Verify your email — **Free Tier** includes **1,000 credits** that never expire (no credit card)
3. Create a key in the [API Keys dashboard](https://lumify.ai/api-keys) (shown only once)

## 2. Make your first call

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
      "starts_at": "2026-06-23T23:40:00Z",
      "venue": { "id": 42, "name": "Petco Park", "city": "San Diego" }
    }
  ],
  "total": 1,
  "next_after_id": null
}
```

That's a successful call — grab any `id` from `events` for the next request.

## 3. Next (2 minutes) — Get bet intelligence for a game

Take any `id` from the events response and fetch its intelligence payload. On
MLB, tennis, soccer, NFL, and NCAAF that includes predictive `bets[]`
(`probability` / `fair_price`). On NBA, NCAAB, and NHL, `available` is often
`false` and `bets[]` is empty — still read `forecasts[]`, or scan the daily
board with `GET /v1/intelligence/forecasts` (MCP `list_forecasts`). How to read
that payload: [Understanding Odds](https://lumify.ai/docs/understanding-odds).

```bash
curl "https://lumify.ai/v1/events/9199/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response (abbreviated):**
```json
{
  "event_id": 9199,
  "available": true,
  "has_recommend": false,
  "match_overview": "Padres host Braves with Eovaldi on the mound.",
  "rationale": ["Eovaldi listed as SP", "Braves on back end of road trip"],
  "bets": [
    {
      "bet_type": "ML_P1",
      "player_name": "San Diego Padres",
      "probability": 0.548,
      "fair_price": -121,
      "tier": null
    }
  ]
}
```

> One predictive surface: `probability`, `interval`, `fair_price`, `market`,
> `edge`/`tier` (null today), plus Price `fair` / `edges_by_book` / `best`.
> Framework plumbing like `phase` / `blend_w` / `p_model` is omitted.
> Full definitions: [API reference](https://lumify.ai/docs/reference#event-intelligence).

## 4. Explore the Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /v1/sports` | Supported sports, leagues, and current seasons |
| `GET /v1/events` | Paginated, filterable event list |
| `GET /v1/events/{id}` | Full event detail (optionally `?include_odds=true`, `?include_intelligence=true`) |
| `GET /v1/events/{id}/score` | Lightweight live-score snapshot |
| `GET /v1/events/{id}/odds` | Current moneyline, spread, and total lines |
| `GET /v1/events/{id}/odds/history` | Line movement history |
| `GET /v1/events/{id}/splits` | Public betting splits (bets % vs handle %) — MLB, NBA, NHL, NFL, NCAAF, NCAAB; not tennis/soccer |
| `GET /v1/events/{id}/stats` | Raw team/match stats — form, H2H, rates, standings/record (Data layer; soccer, MLB, tennis, NFL, NCAAF, NBA, NCAAB, NHL) |
| `GET /v1/events/{id}/intelligence` | Predictive per-bet analysis — probability, fair price, Price overlay (MLB, soccer, tennis, NFL, NCAAF) |
| `GET /v1/players` | Player/team lookup |
| `GET /v1/players/{id}` | Player or team profile |
| `GET /v1/players/{id}/events` | Player/team schedule and results |

## 5. Credits & Rate Limits

- Each successful API call costs **1 credit**. Compound calls
  (`include_odds` / `include_intelligence`) and multi-bookmaker odds
  (`bookmaker=all`) do not add extra.
- Failed requests (`4xx`/`5xx`) do not consume credits.
- Rate limits are enforced per API key on a sliding 60-second window. Every response
  includes `X-RateLimit-*` headers so you can throttle proactively. Exceeding the limit
  returns `429 Too Many Requests` with a `retry_after` value.

## Next Steps

- [Understanding Odds](https://lumify.ai/docs/understanding-odds) — how to read a wager from an intelligence response
- [API Reference](https://lumify.ai/docs/reference) — full endpoint documentation with curl, Python, and JavaScript examples
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
