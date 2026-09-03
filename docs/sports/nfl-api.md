# NFL API for Scores, Schedules, Odds & AI Agents

> HTML twin: [/sports/nfl-api](/sports/nfl-api)

NFL-specific sports API landing — schedules, live scores, multi-book odds, betting splits, Stage-1 raw team stats, and seasonal bet intelligence. Canonical for **NFL API** and **NFL odds API** intent (odds are an H2 here; no separate `/odds/nfl-odds-api` yet).

Filter: `sport=nfl` (league slug `nfl`).

## Available data

| Layer | Endpoint | NFL notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=nfl`; status, date, `include_odds` / `include_scores` |
| Live score | `GET /v1/events/{id}/score` · SSE | Periods `1`–`4` / `OT`; `clock` when available |
| Odds | `GET …/odds` · `…/odds/history` | Two-way `h2h`, spreads, totals · 16 books |
| Player props | `GET …/player-props` | Settleable yards / TD / receptions mains + live box progress |
| Team totals | `GET …/team-props` | Each team's full-game points Over/Under + this-event score |
| Period odds | `GET …/period-odds` | First-half spreads/totals (Q1+Q2) |
| Splits | `GET …/splits` | Pre-game ticket% vs handle% (in-season) |
| Intelligence | `GET …/intelligence` | Customer surface: fair probability + Price overlay + main-line `ev` (Beta) |
| EV scan (Beta) | `GET /v1/intelligence/ev` | Pregame main-line +EV list (`sport=nfl`; `market=h2h\|spreads\|totals`). MCP `list_ev` |
| Forecasts | `GET /v1/intelligence/forecasts` | Daily board of forecasted prop wagers (`sport=nfl`). MCP `list_forecasts` |
| Raw stats | `GET …/stats` | Stage-1 team context (record, form, H2H, rest, offense/defense rates) |

## Schedules

`GET /v1/events?sport=nfl` — status, `date` or `from`/`to` (max 90 days/request), `after_id` / `limit`. Teams: `GET /v1/teams?sport=nfl`. Seasons: `GET /v1/seasons?sport=nfl`.

## Scores

Football period labels (`1`–`4`, `OT`) + `clock`. Live board: `?sport=nfl&status=inprogress&include_scores=true`. Poll `/score` or SSE `/stream`.

## Odds

Two-way moneyline / spreads / totals. Default Pinnacle or `bookmaker=all` = 1 credit. Game markets only. Cross-sport detail: [/sports-odds-api](/sports-odds-api).

## Player props

`GET /v1/events/{id}/player-props` (1 credit when lines exist; `available:false` is free). MCP: `get_player_props`. Market keys: [/docs/player-props](/docs/player-props). Endpoint fields: [/docs/reference#event-player-props](/docs/reference#event-player-props).

## Intelligence & splits

Probability / Price surface. Tokens: `ML_P1`/`ML_P2`, `SPREAD_P1`/`SPREAD_P2`, `OVER`/`UNDER`. Per bet: `probability`, `interval`, `fair_price`, `market`, `fair` (Pinnacle+Circa when both quote), `edges_by_book`, `best`, main-line `ev` (Beta). Today `edge`/`tier` are null and `has_recommend` is false — vig-stripped fair + line-shopping. `best.edge` is a line-shopping price gap vs sharp consensus; main-line `ev` (Beta) packages a positive gap as `ev_pct` + Kelly. Splits are pre-game only. NCAAF is a separate `sport=ncaaf` filter (same probability surface, including splits) — see [/sports/ncaaf-api](/sports/ncaaf-api).

## Raw stats

`GET /v1/events/{id}/stats` — Stage-1 **NFL-native** team context (record, form, H2H, rest, offense/defense rates). Judgment stays on `/intelligence`. Check `available`. Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Sportsbooks

Odds: `pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

Splits use the same bookmaker slugs under `bookmakers[].bookmaker` (e.g. `draftkings`).

## Example — NFL slate with odds

```bash
curl "https://lumify.ai/v1/events?sport=nfl&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="nfl",
    status="scheduled",
    include_odds=True,
    limit=5,
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "nfl",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — intelligence

```bash
curl "https://lumify.ai/v1/events/4821/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Splits | Pre-game only |
| Stats | Scheduled box ingest (persist-then-read) |
| Intelligence | After analysis runs (in-season) |

## Pricing

| Call | Credits |
|---|---|
| Most successful GETs | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [NCAAF API](/sports/ncaaf-api)
- [NBA API](/sports/nba-api)
- [MLB API](/sports/mlb-api)
- [Soccer API](/sports/soccer-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
- [Intelligence reference](/docs/reference#event-intelligence)
