# NCAAB API for Scores, Schedules, Odds & AI Agents

> HTML twin: [/sports/ncaab-api](/sports/ncaab-api)

Men's college-basketball sports API landing — schedules, live scores, multi-book odds, settleable player props (same catalog as NBA), and Stage-1 raw team stats. Canonical for **NCAAB API** / **college basketball API** intent (odds are an H2 here; no separate `/odds/ncaab-odds-api`).

Filter: `sport=ncaab` (league slug `ncaab`).

## Available data

| Layer | Endpoint | NCAAB notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=ncaab`; status, date, `include_odds` / `include_scores` |
| Live score | `GET /v1/events/{id}/score` · SSE | Periods `1`–`4` / `OT`; `clock` when available |
| Odds | `GET …/odds` · `…/odds/history` | Two-way `h2h`, spreads, totals · 16 books |
| Player props | `GET …/player-props` | Settleable points/rebounds/assists/etc. mains + live box progress |
| Period odds | `GET …/period-odds` | First-half spreads/totals (native 1H row) |
| Splits | `GET …/splits` | Pre-game ticket% vs handle% (empty off-season) |
| Intelligence | `GET …/intelligence` | `bets[]` not yet — `available: false`; `forecasts[]` still populate |
| Forecasts | `GET /v1/intelligence/forecasts` | Daily board of forecasted prop wagers (`sport=ncaab`). MCP `list_forecasts` |
| Raw stats | `GET …/stats` | Stage-1 team context (record, form, H2H, rest, shooting/rebounding rates) |

## Schedules

`GET /v1/events?sport=ncaab` — status, `date` or `from`/`to` (max 90 days/request), `after_id` / `limit`. Dense tip-off nights: prefer date windows + `include_odds` / `include_scores`.

## Scores

Basketball period labels (`1`–`4`, `OT`) + `clock`. Live board: `?sport=ncaab&status=inprogress&include_scores=true`. Poll `/score` or SSE `/stream`.

## Odds

Two-way moneyline / spreads / totals. Default Pinnacle or `bookmaker=all` = 1 credit. Game markets only — player props are a separate endpoint below. Team totals stay out of v1. Cross-sport detail: [/sports-odds-api](/sports-odds-api).

## Player props

`GET /v1/events/{id}/player-props` (1 credit when lines exist; `available:false` is free). MCP: `get_player_props`. Same basketball catalog as NBA. Market keys: [/docs/player-props](/docs/player-props). Endpoint fields: [/docs/reference#event-player-props](/docs/reference#event-player-props).

## Raw stats

`GET /v1/events/{id}/stats` — Stage-1 **NCAAB-native** team context (same basketball catalog as NBA, scoped to `ncaab`). Check `available`. Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Sportsbooks

Odds: `pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

## Example — NCAAB slate with odds

```bash
curl "https://lumify.ai/v1/events?sport=ncaab&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="ncaab",
    status="scheduled",
    include_odds=True,
    limit=5,
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "ncaab",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — Stage-1 stats

```bash
curl "https://lumify.ai/v1/events/5201/stats" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Stats | Scheduled box ingest (persist-then-read) |
| Intelligence | `bets[]` not yet; `forecasts[]` / `list_forecasts` live |

## Pricing

| Call | Credits |
|---|---|
| Most successful GETs | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [NBA API](/sports/nba-api)
- [NCAAF API](/sports/ncaaf-api)
- [NHL API](/sports/nhl-api)
- [NFL API](/sports/nfl-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
