# Sports API Built for AI Agents

> HTML twin: [/sports-api-for-ai-agents](/sports-api-for-ai-agents)

Lumify is a sports intelligence API designed for autonomous agents: hosted metered MCP, OpenAPI schemas, free cost estimates, instant trial keys, and predictive intelligence (probability / fair price / Price overlay) on the same event IDs as schedules, scores, and odds.

## Agent loop

1. **Estimate** (free) — `POST /v1/estimate` or MCP `estimate_cost`
2. **Discover** — `list_events` / `GET /v1/events`
3. **Act** — `get_odds`, `get_player_props` (NFL/NCAAF/NBA/NCAAB/NHL/MLB), `get_live_score`, `get_intelligence`, `list_ev`, `list_forecasts`, …
4. **Cite** — quote structured fields; do not invent rationale from a price alone

## MCP

- Endpoint: `https://lumify.ai/mcp` (Streamable HTTP, Bearer `lmfy-…`)
- `GET /mcp` returns protocol JSON; human landing: [/sports-mcp-server](/sports-mcp-server)
- Setup: [/docs/guides#mcp](/docs/guides#mcp) · prompts: [/docs/ai](/docs/ai)

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

## OpenAPI & discovery

- OpenAPI (human): [/docs/openapi](/docs/openapi)
- OpenAPI schema: [/openapi.json](/openapi.json)
- LLM endpoint dump: [/openapi-llms.txt](/openapi-llms.txt)
- Agent manifest: [/.well-known/agent.json](/.well-known/agent.json)
- Orientation: [/llms.txt](/llms.txt)

## Intelligence

`GET /v1/events/{id}/intelligence` — predictive judgment (`probability` / `fair_price` / Price overlay) on MLB, soccer (MLS + big-five), tennis, NFL, and NCAAF. Other sports/leagues return `available: false`. Main-line `bets[].ev` (Beta) re-packages a positive sharp-fair gap as `ev_pct` + Kelly on moneyline, spreads, and totals (tennis totals unpublished). Scan a sport with `GET /v1/intelligence/ev?market=` (MCP `list_ev`). Forecasted wagers (a model prediction, not a beat-the-market claim): `GET /v1/intelligence/forecasts` (MCP `list_forecasts`) — player props plus tennis main-line (moneyline, spreads, totals), `p_hit` is P(the picked outcome hits), ranked by `conviction`. Soccer has no forecast board. How + field catalog: [/docs/forecasts](/docs/forecasts). Raw Data layer: `/stats` (soccer, MLB, tennis singles, NFL, NCAAF, NBA, NCAAB, NHL — sport-native payloads; college reuses pro sibling field catalogs but stays league-scoped). Coverage is sport-specific; check `available`.

## Example (Python)

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
client.estimate.cost([{
    "tool": "list_events",
    "arguments": {"sport": "mlb", "status": "scheduled"},
}])
page = client.events.list(
    sport="mlb", status="scheduled", limit=3
)
intel = client.events.intelligence(page["events"][0]["id"])
```

## Pricing

| Surface | Cost |
|---|---|
| estimate / estimate_cost | Free |
| Most successful calls | 1 credit |
| Multi-book odds | 1 credit |
| `available: false` / errors | 0 |

Instant trial: 100 credits / 14 days (no signup). Free Tier: 1,000 credits. [/pricing](/pricing)

## Related

- [Sports Data API](/sports-data-api)
- [Sports Odds API](/sports-odds-api)
- [Sports MCP Server](/sports-mcp-server)
- [Agent cookbook](/docs/agent-cookbook.md)
- [MCP guide](/docs/guides#mcp)
