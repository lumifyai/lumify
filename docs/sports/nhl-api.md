# NHL API for Scores, Schedules, Odds & AI Agents

> HTML twin: [/sports/nhl-api](/sports/nhl-api)

NHL-specific sports API landing — schedules, live scores, multi-book odds, settleable player props, public betting splits, and Stage-1 raw team stats. Canonical for **NHL API** and **NHL odds API** intent (odds are an H2 here; no separate `/odds/nhl-odds-api` yet).

Filter: `sport=nhl` (league slug `nhl`).

## Available data

| Layer | Endpoint | NHL notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=nhl`; status, date, `include_odds` / `include_scores` |
| Teams | `GET /v1/teams` | `conference=Eastern` / `Western`, division filters |
| Live score | `GET /v1/events/{id}/score` · SSE | Periods `1`–`3` / `OT` / `SO`; `clock` often null |
| Odds | `GET …/odds` · `…/odds/history` | Two-way `h2h`, spreads, totals · 16 books |
| Player props | `GET …/player-props` | Settleable goals / assists / SOG / points mains + live box progress |
| Splits | `GET …/splits` | Pre-game ticket% vs handle% (in-season) |
| Intelligence | `GET …/intelligence` | `bets[]` not yet — `available: false`; `forecasts[]` still populate |
| Forecasts | `GET /v1/intelligence/forecasts` | Daily board of forecasted prop wagers (`sport=nhl`). MCP `list_forecasts` |
| Raw stats | `GET …/stats` | Stage-1 team context (record, form, H2H, rest, SOG/hits/PIM rates) |

## Schedules

`GET /v1/events?sport=nhl` — status, `date` or `from`/`to` (max 90 days/request), `after_id` / `limit`. Dense puck-drop nights: prefer date windows + `include_odds` / `include_scores`.

## Scores

Hockey period labels (`1`–`3`, `OT`, `SO`). Clock is often null on this feed. Live board: `?sport=nhl&status=inprogress&include_scores=true`. Poll `/score` or SSE `/stream`.

## Odds

Two-way moneyline / spreads / totals (NHL totals often around 6.0). Default Pinnacle or `bookmaker=all` = 1 credit. Game markets only — player props are a separate endpoint below. Team totals stay out of v1. Cross-sport detail: [/sports-odds-api](/sports-odds-api).

## Player props

`GET /v1/events/{id}/player-props` (1 credit when lines exist; `available:false` is free). MCP: `get_player_props`. NHL markets: goals, assists (`hockey_assists`), shots on goal, and points (`hockey_points` = goals + assists). Market keys: [/docs/player-props](/docs/player-props). Endpoint fields: [/docs/reference#event-player-props](/docs/reference#event-player-props).

## Splits

Public ticket% vs handle% on moneyline, spread, and total — pre-game only. Without intelligence yet, pair splits with `/odds` and `/stats` for sharp-vs-public + team-context. Always check `available`.

## Raw stats

`GET /v1/events/{id}/stats` — Stage-1 **NHL-native** team context (record, form, H2H, rest, team box rates). Check `available`. Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Sportsbooks

Odds: `pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

Splits use the same bookmaker slugs as odds (`bookmakers[].bookmaker`, e.g. `draftkings`).

## Example — NHL slate with odds

```bash
curl "https://lumify.ai/v1/events?sport=nhl&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="nhl",
    status="scheduled",
    include_odds=True,
    limit=5,
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "nhl",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — Eastern Conference teams

```bash
curl "https://lumify.ai/v1/teams?sport=nhl&conference=Eastern" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Player props | Lines ~10 min; live box ~1 min while in progress |
| Splits | Pre-game only |
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
- [NFL API](/sports/nfl-api)
- [MLB API](/sports/mlb-api)
- [Soccer API](/sports/soccer-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
