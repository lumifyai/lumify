# Sports Odds API for Developers & AI Agents

> HTML twin: [/sports-odds-api](/sports-odds-api)

Multi-sportsbook sports odds API — moneyline, spread, and totals across 16 books, pregame and **in-play**, plus line-movement history. Canonical landing for **sports odds API** and **betting odds API** intent (no separate `/betting-odds-api`).

## Endpoints

- `GET /v1/events/{id}/odds` — current lines, pregame and in-play (default Pinnacle or `bookmaker=all` / a list = 1 credit)
- `GET /v1/events/{id}/odds/history` — recorded price/point moves (same credit rules)
- `GET /v1/events/{id}/player-props` — NFL/NCAAF/NBA/NCAAB/NHL/MLB player-prop mains + live box progress (1 credit; `available:false` is free)
- `GET /v1/events/{id}/team-props` — NFL/NCAAF/MLB/soccer team-total Over/Under mains + this-event score (1 credit)
- `GET /v1/events/{id}/period-odds` — first-half (NFL/NCAAF/NBA/NCAAB/soccer), first-five (MLB), and first-set (tennis) mains + period-score settlement (1 credit)
- Optional: `GET /v1/events/{id}?include_odds=true` embeds odds on the event detail

Always `200` when the event exists — check `available` before reading `bookmakers[]`. `available: false` is free.

## Sportsbooks

`pinnacle`, `fanduel`, `draftkings`, `betmgm`, `caesars`, `bet365`, `circa`, `westgate`, `wynn`, `south_point`, `stations`, `hardrock`, `betonline`, `betr`, `betrivers`, `lowvig`.

## Markets

`h2h` (moneyline; soccer is 3-way including Draw), `spreads`, `totals`. American odds integers. Default is **main lines**; pass `include_alts=true` for alternate rungs.

**Live / in-play:** moneyline, spread, and totals keep updating on the same ~10-minute cycle after kickoff, not just pregame. While an event is in progress, books that have not posted a quote since kickoff are omitted from the response instead of shown stale. Final events grade `result` (`won`/`lost`/`push`/`void`) and `close` from the **pre-kickoff closing line**, not the last in-play price. Player props, team totals, and period lines (1H / F5 / S1) are a separate persisted surface that still freezes at kickoff. MLB, tennis, and soccer (MLS + big-five) mains also mirror `fair_price` and `consensus`. `GET /odds` stays on h2h/spreads/totals only. Player props: [catalog](/docs/player-props). Futures are not on v1. Odds cadence ~10 minutes, pregame and in-play.

## Example — multi-book odds

```bash
curl "https://lumify.ai/v1/events/4821/odds?bookmaker=all" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
odds = client.events.odds(4821, bookmaker="all")
```

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const odds = await client.events.odds(4821, { bookmaker: "all" });
```

## Example — line history

```bash
curl "https://lumify.ai/v1/events/4821/odds/history?limit=20" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Agents / MCP

Hosted MCP at `https://lumify.ai/mcp` — tools `get_odds`, `get_odds_history`, `get_player_props` (NFL/NCAAF/NBA/NCAAB/NHL/MLB). Pair with `get_intelligence` for probability / fair price / Price overlay, or `list_ev` to scan main-line +EV (Beta; `market=h2h|spreads|totals`) on soccer/MLB/tennis/NFL/NCAAF. Setup: [/docs/ai](/docs/ai).

## Pricing

| Call | Credits |
|---|---|
| Single-book odds or history | 1 |
| `bookmaker=all` or a list | 1 |
| `available: false` / errors | 0 |

Free Tier: 1,000 credits (never expire). Instant trial: 100 credits / 14 days, no signup. Details: [/pricing](/pricing).

## Related

- [Best sports betting APIs 2026](/compare/best-sports-betting-apis)
- [Sports Data API](/sports-data-api)
- [NFL API](/sports/nfl-api)
- [NCAAF API](/sports/ncaaf-api)
- [NBA API](/sports/nba-api)
- [NCAAB API](/sports/ncaab-api)
- [MLB API](/sports/mlb-api)
- [Soccer API](/sports/soccer-api)
- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [Odds reference](/docs/reference#event-odds)
- [Player props catalog](/docs/player-props)
- [Player props endpoint](/docs/reference#event-player-props)
- [Odds history](/docs/reference#event-odds-history)
- [Odds movement guide](/docs/guides#recipe-odds-movement)
- [Bet intelligence](/docs/reference#event-intelligence)
