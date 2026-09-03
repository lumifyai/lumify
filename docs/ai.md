# AI-Assisted Development

> Canonical URL: https://lumify.ai/docs/ai.md
> HTML twin: https://lumify.ai/docs/ai

MCP install, context files, starter prompts, and SDKs. The instant trial-key button lives on the HTML page.

<!-- Auto-generated from api/templates/public/docs_ai.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

# AI-assisted development

Use Cursor, Claude, Copilot, or any coding agent to build on Lumify — with MCP tools, machine-readable docs, and copy-paste prompts that prevent hallucinated endpoints.

## Overview

Lumify is built for agents. You can connect in two ways:

1. **MCP tools** — the agent calls schedules, odds, splits, and intelligence directly (no wrapper code).

2. **REST + SDKs** — the agent reads llms.txt / OpenAPI and writes correct client code.

| Resource | URL | Measured size | Use when |
| --- | --- | --- | --- |
| MCP server | [https://lumify.ai/mcp](/mcp) | 24 tools | Agent needs live sports intelligence as tools |
| Cheat sheet | [/docs/cheat-sheet](/docs/cheat-sheet) | ~1 page | Human re-entry + compact LLM context |
| Player props catalog | [/docs/player-props](/docs/player-props) | ~1 page | NFL/NCAAF/NBA/NCAAB/NHL/MLB market keys — settleable vs returned-not-graded, plus the forecastable 1:1 subset |
| How forecasts work | [/docs/forecasts](/docs/forecasts) | ~1 page | Player-prop rate model, field catalog, forecastable vs settleable |
| Sports Coverage | [/docs/sports-coverage](/docs/sports-coverage) | ~1 page | Sport × surface map — what is live today, with links to each endpoint |
| Agent Skill | [/SKILL.md](/SKILL.md) | ~1.4k tokens (measured) | Agent Skills-format self-onboarding (get key, connect MCP, safe research loop) |
| llms.txt | [/llms.txt](/llms.txt) | ~5.4k tokens (measured) | Lookup / answer-engine overview |
| llms-full.txt (GEO) | [/llms-full.txt](/llms-full.txt) | ~11.7k tokens (measured) | Orientation: FAQ, pricing, coverage, comparisons |
| docs/llms-full.txt | [/docs/llms-full.txt](/docs/llms-full.txt) | ~81k tokens (measured) | Full technical docs + endpoint dump |
| openapi-llms.txt | [/openapi-llms.txt](/openapi-llms.txt) | ~6.3k tokens (measured) | OpenAPI-derived endpoint dump alone |
| OpenAPI (human) | [/docs/openapi](/docs/openapi) · [.md](/docs/openapi.md) | — | Discoverability landing · schema at /openapi.json |
| OpenAPI | [/openapi.json](/openapi.json) | ~64.7k tokens (measured) | Exact schemas for clients and validators |
| Agent manifest | [/.well-known/agent.json](/.well-known/agent.json) | — | Discovery of transport + MCP endpoint |
| Agent cookbook | [/docs/agent-cookbook.md](/docs/agent-cookbook.md) | — | Copy-paste REST + MCP recipes |
| Changelog | [/changelog](/changelog) · [JSON](/changelog.json) | — | Date-stamped changes agents can poll |

Token budgets are **measured** (UTF-8 bytes ÷ 4), not estimated. Re-measure after regenerating llms-full.txt or OpenAPI.

<!-- #overview -->

## One-click install

Install the hosted MCP server directly, then replace the placeholder API key:

 [Add Lumify MCP to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=lumify&config=eyJ1cmwiOiJodHRwczovL2x1bWlmeS5haS9tY3AiLCJoZWFkZXJzIjp7IkF1dGhvcml6YXRpb24iOiJCZWFyZXIgWU9VUl9BUElfS0VZIn19)
 [Add Lumify MCP to VS Code](vscode:mcp/install?%7B%22name%22%3A%22lumify%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Flumify.ai%2Fmcp%22%2C%22headers%22%3A%7B%22Authorization%22%3A%22Bearer%20YOUR_API_KEY%22%7D%7D)
 [Import Lumify collection to Postman](/docs/lumify.postman_collection.json)
 [Create a free API key →](/register)

### Claude Code (CLI)

```text
claude mcp add --transport http lumify https://lumify.ai/mcp \
  --header "Authorization: Bearer YOUR_API_KEY"
```

### Cursor (remote HTTP)

```json
{
  "mcpServers": {
    "lumify": {
      "url": "https://lumify.ai/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

### Cursor / Claude Desktop (stdio via npm)

Use the published bridge when the client only speaks local stdio:

```text
npx -y @lumifyai/mcp
```

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": ["-y", "@lumifyai/mcp"],
      "env": { "LUMIFY_API_KEY": "YOUR_API_KEY" }
    }
  }
}
```

### VS Code / Copilot

```json
{
  "servers": {
    "lumify": {
      "type": "http",
      "url": "https://lumify.ai/mcp",
      "headers": { "Authorization": "Bearer YOUR_API_KEY" }
    }
  }
}
```

CLI one-liner: code --add-mcp '{"name":"lumify","type":"http","url":"https://lumify.ai/mcp","headers":{"Authorization":"Bearer YOUR_API_KEY"}}'

> **Warning:** Web connectors: ChatGPT and Claude.ai browser connectors need OAuth, which Lumify does not implement yet. Use Cursor, Claude Desktop, VS Code, or any Bearer-header MCP client.

<!-- #one-click -->

## Give your agent context

Paste this into CLAUDE.md, .cursorrules, or a project rule file. It is the API's essence compressed for agents (~2.5k tokens of guidance + links to measured artifacts):

```text
You are integrating with Lumify (also: Lumify AI, lumify.ai) —
the agent-ready sports intelligence API at https://lumify.ai.
NOT affiliated with LUMIFY eye drops, Philips Lumify ultrasound,
lumifyai.com, or the archived lumifyio/lumify project.

## Read these first (measured token budgets)
- https://lumify.ai/SKILL.md              (~1.4k tokens) — Agent Skills-format self-onboarding
- https://lumify.ai/llms.txt              (~5.4k tokens) — overview + pricing + limitations
- https://lumify.ai/docs/cheat-sheet      — base URL, auth, credits, hero query, errors
- https://lumify.ai/docs/player-props     — NFL/NCAAF/NBA/NCAAB/NHL/MLB player-prop market catalog
- https://lumify.ai/llms-full.txt         (~11.7k tokens) — GEO orientation (FAQ, coverage)
- https://lumify.ai/docs/llms-full.txt    (~81k tokens) — full technical docs + dump
- https://lumify.ai/openapi-llms.txt      (~6.3k tokens) — endpoint dump alone
- https://lumify.ai/openapi.json         (~64.7k tokens) — exact schemas
- https://lumify.ai/docs/agent-cookbook.md — copy-paste recipes
- https://lumify.ai/changelog.json       — date-stamped changes

## Auth
Authorization: Bearer lmfy-...
Instant trial key (no signup): https://lumify.ai/docs/ai
Never invent an API key. If you cannot access URLs, ask the user to paste
the relevant resource instead of guessing.

## MCP (preferred when available)
URL: https://lumify.ai/mcp  (Streamable HTTP, JSON mode, stateless)
24 tools: list_sports, list_seasons, list_events, get_event,
batch_get_events, query_events, get_live_score, get_odds,
get_odds_history, get_stats, get_player_props, get_team_props, get_prediction_markets, get_period_odds, get_splits, get_intelligence, list_ev, list_forecasts,
list_teams, get_team, search_players, get_player,
get_player_events, estimate_cost.
initialize / tools/list / ping are free; tools/call metered like REST.
_meta.credits_used reports the charge. Prefer MCP tools over hand-rolled REST.

## Billing rule (two budgets)
- Data plane: schedules, scores, odds, splits, stats — typically 1 credit.
- Intelligence plane: /intelligence — 1 credit when available.
- One request = 1 credit. include_odds / include_intelligence on GET /v1/events/{id}
  do not add extra.
- Errors and available:false responses are NEVER charged.
- Always estimate first with POST /v1/estimate or MCP estimate_cost (free).

## Boundary litmus
- /stats and raw odds = deterministic data. No scoring, no tiers.
- /intelligence = predictive judgment (probability / fair_price / Price overlay / main-line ev).

## Hero endpoints
GET  /v1/events?sport=mlb&status=scheduled
GET  /v1/events/{id}?include_odds=true&include_intelligence=true
GET  /v1/events/{id}/odds?bookmaker=all
GET  /v1/events/{id}/splits
GET  /v1/events/{id}/intelligence
POST /v1/estimate
POST /v1/trial-key   (human Turnstile-gated; prefer /docs/ai button)

## Coverage (keep in sync with llms.txt)
Intelligence live: MLB, NFL, NCAAF, tennis, soccer (MLS + big-five).
Forecasts: MLB, NFL, NCAAF, NBA, NCAAB, NHL — https://lumify.ai/docs/forecasts
UCL and other clubs: available: false.
Splits: MLB, NBA, NHL, NFL.
Books: pinnacle (default), fanduel, draftkings, betmgm, caesars,
bet365, circa, westgate, wynn, south_point, stations, hardrock,
betonline, betr, betrivers, lowvig.
Player props: NFL/NCAAF/NBA/NCAAB/NHL/MLB on GET /v1/events/{id}/player-props (MCP get_player_props).
Catalog: https://lumify.ai/docs/player-props
GET /odds stays moneyline/spread/totals. Futures not on v1.
Alternate spread/total rungs via include_alts=true. Final /odds includes result.
Odds cadence ~10 min.

## Model behavior
- Do not guess or invent endpoints, fields, sport IDs, or credit costs.
- Help the user choose filters (sport, status, date, has_recommend).
- When data is unavailable, explain available:false rather than retrying forever.
- Gate volume, not capability existence — streaming/webhooks are self-serve.
```

In Cursor, you can also add https://lumify.ai/llms.txt as a docs/@ reference.

<!-- #context -->

## Starter prompts

Try these after MCP is connected (or with the context block above):

### Live slate + intelligence

```text
Using Lumify MCP, list today's MLB games that are scheduled or live.
For the top 3 by start time, pull get_intelligence and summarize
probability, fair_price, and any main-line ev (Beta).
```

### Main-line EV scan (Beta)

```text
Using Lumify MCP list_ev, scan MLB for pregame moneyline +EV
opportunities (min_ev 1). Rank by ev_pct. For the top row, call
get_intelligence on that event_id and quote fair / ev as Beta
display packaging of the price gap. Try market=spreads or
market=totals for the same scan on other main lines.
```

### Splits vs public

```text
Find NFL games this week where betting splits show a clear ticket%
vs handle% divergence. Use list_events then get_splits. Rank by
the largest handle/ticket gap and explain what it implies.
```

### Line movement watcher

```text
For a given event_id, call get_odds and get_odds_history.
Show opening vs current moneyline/spread/total across supported
books (Pinnacle, FanDuel, DraftKings, BetMGM, Caesars, Bet365,
Circa, Hard Rock, BetOnline), and flag any reverse line moves.
```

### Scaffold a small agent

```text
Read https://lumify.ai/openapi.json and scaffold a TypeScript
script that: (1) lists today's MLB events, (2) fetches intelligence
for each, (3) prints bets[] probability / fair_price when available
is true. Do not filter has_recommend — it stays false until Edge.
Use @lumifyai/sdk if helpful. Do not invent fields.
```

<!-- #prompts -->

## SDKs

When you want typed REST clients instead of (or alongside) MCP:

```text
npm install @lumifyai/sdk
pip install lumify-sdk
```

Docs: [@lumifyai/sdk](https://www.npmjs.com/package/@lumifyai/sdk) · [lumify-sdk](https://pypi.org/project/lumify-sdk/) · MCP bridge [@lumifyai/mcp](https://www.npmjs.com/package/@lumifyai/mcp)

<!-- #sdks -->

## Next steps

- [Full MCP tool catalogue & billing](/docs/guides#mcp)

- [Build an MCP betting-splits agent](/docs/guides#recipe-mcp-splits)

- [REST API reference](/docs/reference)

- [Pricing & free credits](/pricing)

<!-- #next -->
