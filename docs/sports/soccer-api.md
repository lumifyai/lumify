# Soccer API for Scores, Odds & AI Agents

> HTML twin: [/sports/soccer-api](/sports/soccer-api)

Soccer / football API landing — MLS, EPL, La Liga, Serie A, Bundesliga, Ligue 1, and UCL as **sections of this page** (no thin per-league micros yet). Canonical for **soccer API** / **football API** intent.

Filter: `sport=soccer` + optional `league=` slug.

## Available data

| Layer | Endpoint | Soccer notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=soccer` + optional `league` |
| Live score | `GET …/score` · SSE | `1H` / `2H` / `ET*` / `PKs`; clock e.g. `67'` |
| Odds | `GET …/odds` · history | **3-way** `h2h` (+ Draw), spreads, totals |
| Team totals | `GET …/team-props` | Each team's full-game goals Over/Under + this-event score |
| Period odds | `GET …/period-odds` | First-half spreads/totals (native 1H) |
| Stats (Data) | `GET …/stats` | Soccer-native strength, form, H2H, rest, rates, lineups |
| Intelligence | `GET …/intelligence` | Live for MLS + big-five; UCL returns `available: false` |
| EV scan (Beta) | `GET /v1/intelligence/ev` | Pregame main-line +EV list (`sport=soccer`; `market=h2h\|spreads\|totals`). MCP `list_ev` |
| Splits | `GET …/splits` | **Not available** for soccer |

## Leagues

| Competition | Slug | Schedules / scores / odds | Intelligence |
|---|---|---|---|
| MLS | `mls` | Yes (in season) | Probability + Price surface |
| Premier League | `epl` | Yes (in season) | Probability + Price surface |
| La Liga | `la_liga` | Yes (in season) | Probability + Price surface |
| Serie A | `serie_a` | Yes (in season) | Probability + Price surface |
| Bundesliga | `bundesliga` | Yes (in season) | Probability + Price surface |
| Ligue 1 | `ligue_1` | Yes (in season) | Probability + Price surface |
| UEFA Champions League | `ucl` | Yes (in season) | — / `available: false` |

## Schedules

`GET /v1/events?sport=soccer&league=mls` (or `epl`, …). Status, date/`from`/`to` (max 90 days), `after_id` / `limit`. Compound `include_odds` / `include_scores`.

## Scores

Period labels `1H`, `2H`, `ET1`, `ET2`, `PKs`. Clock like `45'+2`, `67'`.

## Odds

**3-way** moneyline (home / Draw / away). Asian handicap spreads; Over/Under totals. Default Pinnacle or `bookmaker=all` = 1 credit. Player props are NFL, NCAAF, NBA, NCAAB, NHL, and MLB — [catalog](/docs/player-props). Detail: [/sports-odds-api](/sports-odds-api).

## Stats (Data layer)

Soccer-native `/stats` — strength, form, H2H, rest, rates, lineups. No scoring/narrative. Check `available`. Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Intelligence

- **MLS + big-five** (EPL, La Liga, Serie A, Bundesliga, Ligue 1) — probability customer surface (`probability` / `fair_price` + Price overlay). `best.edge` is a line-shopping price gap vs Pinnacle; main-line `ev` (Beta) packages a positive gap as `ev_pct` + Kelly. `has_recommend` stays false until Edge publishes.
- **UCL** — schedules, scores, odds, and `/stats`; intelligence returns `available: false`. Fields: [/docs/reference#event-intelligence](/docs/reference#event-intelligence).

Tokens: `ML_HOME`, `ML_AWAY`, `ML_DRAW`, `SPREAD_HOME`, `SPREAD_AWAY`, `OVER`, `UNDER`.

## Sportsbooks

`pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`. Availability varies by league/event.

## Example — MLS with odds

```bash
curl "https://lumify.ai/v1/events?sport=soccer&league=mls&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="soccer",
    league="mls",
    status="scheduled",
    include_odds=True,
    limit=5,
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "soccer",
  league: "mls",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — Premier League

```bash
curl "https://lumify.ai/v1/events?sport=soccer&league=epl&status=scheduled&include_odds=true&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Stats | After aggregates resolve |
| Intelligence | After publish / analysis (MLS + big-five; UCL is `available: false`) |

## Pricing

| Call | Credits |
|---|---|
| Most successful GETs | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [MLB API](/sports/mlb-api)
- [NFL API](/sports/nfl-api)
- [NBA API](/sports/nba-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
