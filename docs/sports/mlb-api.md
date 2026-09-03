# MLB API for Scores, Stats, Odds & AI Agents

> HTML twin: [/sports/mlb-api](/sports/mlb-api)

MLB-specific sports API landing — schedules, live scores, multi-book odds, settleable player props, betting splits, baseball-native `/stats`, and predictive `/intelligence` with a sharp fair + Price surface. Canonical for **MLB API** and **MLB odds API** intent (odds are an H2 here; no separate `/odds/mlb-odds-api` yet).

Filter: `sport=mlb` (league slug `mlb`).

## Available data

| Layer | Endpoint | MLB notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=mlb`; status, date, `include_odds` / `include_scores` |
| Live score | `GET /v1/events/{id}/score` · SSE | `Top 7th` / `Bot 9th`; `clock` is null |
| Odds | `GET …/odds` · `…/odds/history` | Two-way `h2h`, run line (`spreads`), totals · 16 books |
| Player props | `GET …/player-props` | Settleable batting/pitching mains + live box progress |
| Team totals | `GET …/team-props` | Each team's full-game runs Over/Under + this-event score |
| Period odds | `GET …/period-odds` | First-five innings spreads/totals |
| Splits | `GET …/splits` | Pre-game ticket% vs handle% (in-season) |
| Stats (Data) | `GET …/stats` | Baseball-native Path A — post-final box aggregates |
| Intelligence | `GET …/intelligence` | Customer surface: fair probability + Price overlay + main-line `ev` (Beta) |
| EV scan (Beta) | `GET /v1/intelligence/ev` | Pregame main-line +EV list (`sport=mlb`; `market=h2h\|spreads\|totals`). MCP `list_ev` |
| Forecasts | `GET /v1/intelligence/forecasts` | Daily board of forecasted prop wagers (`sport=mlb`). MCP `list_forecasts` |

## Schedules

`GET /v1/events?sport=mlb` — status, `date` or `from`/`to` (max 90 days/request), `after_id` / `limit`. Dense daily slate: prefer date windows + compound includes.

## Scores

Inning labels (`Top 7th`, `Bot 9th`); `clock` null. Live board: `?sport=mlb&status=inprogress&include_scores=true`.

## Odds

Two-way moneyline / run line (typically ±1.5) / totals. Default Pinnacle or `bookmaker=all` = 1 credit. Game markets only — player props and team totals are separate endpoints below. Cross-sport detail: [/sports-odds-api](/sports-odds-api).

## Player props

`GET /v1/events/{id}/player-props` (1 credit when lines exist; `available:false` is free). MCP: `get_player_props`. MLB batting: hits, runs, RBIs, home runs, stolen bases, batter Ks, total bases (H + 2B + 2·3B + 3·HR), hits+runs+RBIs. Pitching: pitcher Ks, hits allowed, earned runs, outs recorded. `walks` is not catalogued (batter vs pitcher ambiguity). Market keys: [/docs/player-props](/docs/player-props). Endpoint fields: [/docs/reference#event-player-props](/docs/reference#event-player-props).

## Stats (Data layer)

`GET /v1/events/{id}/stats` — baseball-native box-score aggregates (record, form, H2H, rates, lineup, this-event `player_box`). Pregame probable SP stays on `/intelligence`. No scoring/narrative. Check `available`. Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Intelligence

Customer-facing probability / Price surface. Framework diagnostics are omitted.

**Returned per bet:** `bet_type`, participant ids/names, `probability`, `interval`, `fair_price`, `market`, `edge`, `tier`, `fair`, `edges_by_book`, `best`, `ev` (Beta, main-line), `computed_at`.

**Omitted (internal / diagnostic):** `p_model`, `p_market`, `blend_w`, `sufficiency`, `phase`, `model_version`, `drivers`, `alignment`.

Today `edge`/`tier` are null and `has_recommend` is false — vig-stripped fair reference + line-shopping. Price surface: `fair` (Pinnacle+Circa when both quote), `edges_by_book`, `best`. `best.edge` is a line-shopping price gap vs sharp consensus; main-line `ev` (Beta) packages a positive gap as `ev_pct` + Kelly. Tokens: `ML_P1`/`ML_P2`, `SPREAD_*`, `OVER`/`UNDER`. For pitcher/lineup Data use `/stats`.

## Splits

Pre-game ticket% vs handle% on moneyline, run line, and total. Stops after first pitch.

## Sportsbooks

Odds: `pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

Splits use the same bookmaker slugs as odds (`bookmakers[].bookmaker`, e.g. `draftkings`).

## Example — MLB slate with odds

```bash
curl "https://lumify.ai/v1/events?sport=mlb&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="mlb",
    status="scheduled",
    include_odds=True,
    limit=5,
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

## Example — intelligence + stats

```bash
curl "https://lumify.ai/v1/events/8815/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"

curl "https://lumify.ai/v1/events/8815/stats" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Player props | Lines ~10 min; live box ~1 min while in progress |
| Splits | Pre-game only |
| Stats | After box scores ingest (post-final) |
| Intelligence | After publish runs |

## Pricing

| Call | Credits |
|---|---|
| Most successful GETs | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [NFL API](/sports/nfl-api)
- [NBA API](/sports/nba-api)
- [Soccer API](/sports/soccer-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
- [Player props catalog](/docs/player-props)
- [Player props endpoint](/docs/reference#event-player-props)
- [Stats reference](/docs/reference#event-stats)
- [Intelligence reference](/docs/reference#event-intelligence)
