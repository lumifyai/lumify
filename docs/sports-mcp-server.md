# Sports MCP Server for AI Agents

> HTML twin: [/sports-mcp-server](/sports-mcp-server)

Hosted Model Context Protocol server for Lumify sports data and intelligence.

**Important:** The protocol endpoint is [`https://lumify.ai/mcp`](/mcp) (JSON discovery + POST tool calls). This page is the human/SEO landing. Do not treat `/mcp` as HTML.

## Endpoint

| | |
|---|---|
| URL | `https://lumify.ai/mcp` |
| Transport | Streamable HTTP (JSON mode, stateless) |
| Auth | `Authorization: Bearer lmfy-…` |
| Protocol | 2025-06-18 |

## Auth

Instant trial key (no signup): [/docs/ai](/docs/ai). Free Tier account: [/register](/register).

## Cursor config

```json
{
  "mcpServers": {
    "lumify": {
      "url": "https://lumify.ai/mcp",
      "headers": { "Authorization": "Bearer lmfy-YOUR_KEY" }
    }
  }
}
```

## Claude Desktop (stdio)

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": ["-y", "@lumifyai/mcp"],
      "env": { "LUMIFY_API_KEY": "lmfy-YOUR_KEY" }
    }
  }
}
```

## Tools (24)

`list_sports`, `list_seasons`, `list_events`, `get_event`, `batch_get_events`, `query_events`, `get_live_score`, `get_odds`, `get_odds_history`, `get_stats`, `get_player_props`, `get_team_props`, `get_prediction_markets`, `get_period_odds`, `get_splits`, `get_intelligence`, `list_ev`, `list_forecasts`, `list_teams`, `get_team`, `search_players`, `get_player`, `get_player_events`, `estimate_cost`.

`get_player_props` is NFL/NCAAF/NBA/NCAAB/NHL/MLB only. Sport × market catalog (settleable vs returned-not-graded): [/docs/player-props](/docs/player-props). `get_team_props` is NFL/NCAAF/MLB/soccer team totals. `get_prediction_markets` is Fanatics Markets / Kalshi / Polymarket 0–1 game-line probabilities (not sportsbook odds). `get_period_odds` is NFL/NCAAF/NBA/NCAAB/soccer first-half, MLB first-five, and tennis first-set. `list_ev` is a Beta main-line EV scan for soccer, MLB, tennis, NFL, and NCAAF (`market=h2h|spreads|totals`; tennis totals 400). `list_forecasts` is a daily board of forecasted wagers — a model prediction, not a beat-the-market claim. Player props (MLB, NCAAF, NFL, NBA, NCAAB, NHL) plus tennis main-line (moneyline, spreads, totals), ranked by conviction — `p_hit` is P(the picked outcome hits). How to read: [/docs/understanding-odds#forecasts](/docs/understanding-odds#forecasts).

Credits match REST. `initialize` / `tools/list` / `ping` are free. Results include `_meta.credits_used`.

## Billing note

ChatGPT / Claude.ai **web** connectors need OAuth (not yet). Desktop/IDE clients with Bearer headers work.

## Related

- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [OpenAPI](/docs/openapi) (schema: [/openapi.json](/openapi.json))
- [MCP docs guide](/docs/guides#mcp)
- Protocol JSON: [/mcp](/mcp)
