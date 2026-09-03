# Sports Data API — Scores, Schedules, Odds & Intelligence

> HTML twin: [/sports-data-api](/sports-data-api)

Agent-ready sports data API: schedules, live scores, teams/players, multi-book odds, splits, raw `/stats`, and predictive `/intelligence` on one event graph. Canonical landing for **sports data API** / **sports API** intent. Live scores and schedules are sections here (no separate thin URLs). Deep odds: [/sports-odds-api](/sports-odds-api).

## Core endpoints

| Need | Endpoint |
|---|---|
| Sport catalog | `GET /v1/sports` |
| Seasons | `GET /v1/seasons` |
| Schedule / live board | `GET /v1/events` |
| Event detail | `GET /v1/events/{id}` (`include_odds`, `include_scores`, `include_intelligence`) |
| Live score | `GET /v1/events/{id}/score` or `/stream` (SSE) |
| Odds | `GET /v1/events/{id}/odds` (+ `/odds/history`) |
| Player props | `GET /v1/events/{id}/player-props` (NFL + NCAAF + NBA + NCAAB + NHL + MLB) |
| Data layer | `GET /v1/events/{id}/stats` (soccer, MLB, tennis singles, NFL, NCAAF, NBA, NCAAB, NHL) |
| Judgment | `GET /v1/events/{id}/intelligence` (main-line `ev` Beta on soccer/MLB/tennis/NFL/NCAAF) |
| EV scan (Beta) | `GET /v1/intelligence/ev` (MCP `list_ev`) |
| Forecasts | `GET /v1/intelligence/forecasts` (MCP `list_forecasts`) |
| Splits | `GET /v1/events/{id}/splits` (MLB/NBA/NHL/NFL in-season) |

## Coverage notes

- Scores ~1 min; odds ~10 min.
- Predictive intelligence (`bets[]`) live: MLB, NFL, NCAAF, tennis, soccer (MLS + big-five). Forecasts: MLB, NFL, NCAAF, NBA, NCAAB, NHL. UCL returns `available: false`.
- Historical queries capped at 90 days per request.
- Player props are NFL/NCAAF/NBA/NCAAB/NHL/MLB only on `GET /player-props`. Futures are not on v1. Alternate spread/total rungs via `include_alts=true` on `/odds`.

## Example — schedule + odds

```bash
curl "https://lumify.ai/v1/events?sport=mlb&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="mlb", status="scheduled", include_odds=True, limit=5
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "mlb",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — live scores

```bash
curl "https://lumify.ai/v1/events?status=inprogress&include_scores=true&sort=status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Tutorial + demo: [/use-cases/live-scoreboard](/use-cases/live-scoreboard).

## Agents / MCP

Hosted MCP: `https://lumify.ai/mcp`. Tools include `list_events`, `get_odds`, `get_intelligence`, `list_ev`, `list_forecasts`. Setup: [/docs/ai](/docs/ai).

## Pricing

Most successful calls = **1 credit**. Multi-book odds = **1**. `available: false` / errors = free. Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [NFL API](/sports/nfl-api)
- [NCAAF API](/sports/ncaaf-api)
- [NBA API](/sports/nba-api)
- [NCAAB API](/sports/ncaab-api)
- [NHL API](/sports/nhl-api)
- [MLB API](/sports/mlb-api)
- [Soccer API](/sports/soccer-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
- [Live score](/docs/reference#event-score)
- [Intelligence](/docs/reference#event-intelligence)
