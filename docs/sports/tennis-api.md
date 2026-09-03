# Tennis API for Scores, Odds & AI Agents

> HTML twin: [/sports/tennis-api](/sports/tennis-api)

ATP/WTA tennis sports API landing — set-by-set schedules and live scores, moneyline/games-handicap/total-games odds, tennis-native `/stats` (rankings, form, career serve/return rates), and Stage-1 predictive `/intelligence`. Individual sport: no player props, team totals, or betting splits.

Filter: `sport=tennis`, tour `league=atp` or `league=wta`.

## Available data

| Layer | Endpoint | Tennis notes |
|---|---|---|
| Schedule / board | `GET /v1/events` | `sport=tennis`; `league=atp`/`wta`; status, date, `include_odds` / `include_scores` |
| Live score | `GET /v1/events/{id}/score` · SSE | Set-by-set `sets_won` / `sets[]`; `clock` is null |
| Odds | `GET …/odds` · `…/odds/history` | Moneyline (`h2h`), games handicap (`spreads`), total games (`totals`) · 16 books |
| Period odds | `GET …/period-odds` | First-set (`S1`) games handicap / total |
| Player props | `GET …/player-props` | **Not available** for tennis |
| Team totals | `GET …/team-props` | **Not available** — individual sport |
| Splits | `GET …/splits` | **Not available** for tennis |
| Stats (Data) | `GET …/stats` | Rankings, form, surface form, H2H, career serve/return rates — singles main-draw only |
| Intelligence | `GET …/intelligence` | Stage 1: moneyline + games handicap Price overlay; totals not yet published |
| EV scan (Beta) | `GET /v1/intelligence/ev` | `market=h2h\|spreads` (`totals` returns 400). MCP `list_ev` |

## Schedules

`GET /v1/events?sport=tennis` — add `league=atp` or `league=wta`. Status, `date` or `from`/`to` (max 90 days/request), `after_id` / `limit`. Retirements/walkovers surface via status/result fields.

## Scores

Set-based: `sets_won` (`player_1`/`player_2`), `winner_role` once decided, `sets[]` with `player_1_games` / `player_2_games` / `tiebreak_score`. `clock` is null.

## Odds

Two-way moneyline / games handicap / total games. Default Pinnacle or `bookmaker=all` = 1 credit. Tennis is the one grading gap on final events — game-count isn't tracked through settlement, so `result`/`close` populate for moneyline only; `spreads`/`totals` stay unresolved after the match ends. Cross-sport detail: [/sports-odds-api](/sports-odds-api).

## Stats (Data layer)

`GET /v1/events/{id}/stats` — player-keyed (`player_1`/`player_2`), tennis-native:

- Current ATP/WTA singles `ranking` + `ranking_points` · `rest_days` since each player's last completed match
- `recent_form` (all surfaces) and `surface_form` (this match's surface) — trailing results, sets for/against
- `record` — win/loss over a trailing lookback window from our own event history
- `career_rates` — career hold %, break-point conversion/save %, first/second-serve-won % when persisted
- `career_surface` — trailing win/loss on this match's surface
- `head_to_head` — up to 10 prior meetings with set scores and surface

`available` is `false` unless `draw_type` is `singles` and both players resolve (doubles/qualifying out of scope today). Fields: [/docs/reference#event-stats](/docs/reference#event-stats).

## Intelligence

Stage 1 customer surface — moneyline and games handicap only. Framework diagnostics are omitted.

**Returned per bet:** `bet_type`, participant ids/names, `probability`, `interval`, `fair_price`, `market`, `edge`, `tier`, `fair`, `edges_by_book`, `best`, `ev` (Beta), `computed_at`.

Tokens: `ML_P1`/`ML_P2`, `SPREAD_P1`/`SPREAD_P2` — no `OVER`/`UNDER` yet (total games stays unpublished; `GET /v1/intelligence/ev?market=totals` returns 400). `edge`/`tier` are null and `has_recommend` is false today — vig-stripped fair reference + line-shopping. `fair` uses a single sharp book (Pinnacle) since tennis has no second sharp quote. **Price ≠ Edge.**

## Sportsbooks

Odds: `pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

## Example — WTA slate with odds

```bash
curl "https://lumify.ai/v1/events?sport=tennis&league=wta&status=scheduled&include_odds=true&limit=5" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
page = client.events.list(
    sport="tennis",
    league="wta",
    status="scheduled",
    include_odds=True,
    limit=5,
)
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  sport: "tennis",
  league: "wta",
  status: "scheduled",
  includeOdds: true,
  limit: 5,
});
```

## Example — intelligence + stats

```bash
curl "https://lumify.ai/v1/events/17438/intelligence" \
  -H "Authorization: Bearer YOUR_API_KEY"

curl "https://lumify.ai/v1/events/17438/stats" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Freshness

| Feed | Cadence |
|---|---|
| Scores | ~1 minute (+ SSE/webhooks) |
| Odds | ~10 minutes (2-min response cache) |
| Stats | Rankings/form on ingest; career rates after vendor persists |
| Intelligence | After publish runs; moneyline + spreads only |

## Pricing

| Call | Credits |
|---|---|
| Most successful GETs | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 / 14 days. Details: [/pricing](/pricing).

## Related

- [MLB API](/sports/mlb-api)
- [Soccer API](/sports/soccer-api)
- [NFL API](/sports/nfl-api)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Events reference](/docs/reference#events)
- [Stats reference](/docs/reference#event-stats)
- [Intelligence reference](/docs/reference#event-intelligence)
