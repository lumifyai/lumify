# Lumify Guides

> Canonical URL: https://lumify.ai/docs/guides.md
> HTML twin: https://lumify.ai/docs/guides

MCP setup, agent resources, and task-oriented recipes for building on Lumify.

<!-- Auto-generated from api/templates/public/docs_guides.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

# Guides

Task-oriented walkthroughs for connecting an agent to Lumify — MCP setup, integration recipes, and copy-paste code for common jobs.

> **Tip:** For agents: the machine-readable twin of this page is [/docs/guides.md](/docs/guides.md). For deeper copy-paste recipes see the [agent cookbook](/docs/agent-cookbook.md).

# Model Context Protocol (MCP)

Lumify runs a hosted MCP server so AI agents can call the entire sports-intelligence API as native tools — no wrapper code required.

> **Note:** Endpoint  https://lumify.ai/mcp

 Transport  Streamable HTTP (JSON mode, stateless)  ·
 Auth  Bearer API key  ·
 Protocol  2025-06-18

Any MCP-compatible client connects by pointing at https://lumify.ai/mcp and passing your Lumify API key as a Bearer token. The server is fully self-describing — a client's tools/list call returns the current tool catalogue with input schemas. You can inspect the discovery document with a browser GET to [/mcp](/mcp) (JSON). Tool calls use POST only — Lumify does not offer a GET Server-Sent Events stream on this URL. Some clients briefly probe with Accept: text/event-stream and receive 405 Allow: POST; that is expected transport negotiation, then they continue over POST JSON (streamable HTTP).

 [Add Lumify MCP to Cursor](cursor://anysphere.cursor-deeplink/mcp/install?name=lumify&config=eyJ1cmwiOiJodHRwczovL2x1bWlmeS5haS9tY3AiLCJoZWFkZXJzIjp7IkF1dGhvcml6YXRpb24iOiJCZWFyZXIgWU9VUl9BUElfS0VZIn19)
 [Get an API key first →](/register)
 [AI-assisted setup guide →](/docs/ai)

The one-click install opens Cursor with a placeholder key — replace YOUR_API_KEY with a key from your [dashboard](/api-keys) before approving.

### Connect from Cursor

Recommended (remote): add Lumify to ~/.cursor/mcp.json (or a project-local .cursor/mcp.json):

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

Stdio bridge (optional): if you prefer a local process, use the published @lumifyai/mcp package:

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

### Connect from Claude Desktop

Claude Desktop speaks stdio. Prefer the official bridge package:

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

Alternatively, bridge with mcp-remote:

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://lumify.ai/mcp",
        "--header", "Authorization: Bearer YOUR_API_KEY"
      ]
    }
  }
}
```

### Connect from VS Code / Copilot

Add a server entry under mcp.servers in your VS Code settings (or .vscode/mcp.json):

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

### Available tools

Each tool maps 1:1 to a REST endpoint and returns identical data. Credit cost mirrors the equivalent REST call.

| Tool | Description | Credits |
| --- | --- | --- |
| list_sports | Supported sports with current active season. | 1 |
| list_seasons | Seasons per sport/league; optional current-only filter. | 1 |
| list_events | Schedule / scores, filterable by sport, league, status, date, season. | 1 |
| get_event | Single event; optional include_odds (scoped by bookmaker, default pinnacle) / include_intelligence. | 1 (+1 odds single book / +2 multi or all; +1 intel) |
| batch_get_events | Multiple events by id in one call (max 25). Missing ids cost nothing. | Sum of each event's cost |
| query_events | Natural-language event search (e.g. "live nfl games today") — rule-based, mapped to list_events filters. | 1 |
| get_live_score | Lightweight live score snapshot. | 1 |
| get_odds | Current moneyline / spread / total lines. | 1 (2 for all books) |
| get_odds_history | Recorded line-movement history. | 1 (2 for all books) |
| get_stats | Raw team/match statistics — team strength/record, form, H2H, rest, boxscore rates (soccer + MLB). No scoring attached. | 1 |
| get_splits | Public betting splits (bets% / handle%). | 1 |
| get_intelligence | Confidence scores, signals, narratives, recommended bets. | 1 |
| list_teams | Team directory with sport/league/conference filters. | 1 |
| get_team | Single team profile with home venue. | 1 |
| search_players | Player search by name, sport, country, ranking. | 1 |
| get_player | Single player profile. | 1 |
| get_player_events | A player's schedule / results (±30 days by default). | 1 |
| estimate_cost | Pre-call credit-cost estimate (min–max range) for one or more planned tool calls. | Free |

### Billing

The MCP handshake is free: initialize, tools/list, and ping never cost credits. Only tools/call is metered, at the same rate as the matching REST endpoint. Each result reports its cost under _meta.credits_used. Calls that return no usable data because it isn't available yet — odds, line history, splits, or intelligence for a match that hasn't been priced/computed — are free (_meta.credits_used: 0).

> **Warning:** Web connectors (ChatGPT / Claude.ai): browser-based connectors require OAuth, which Lumify's key-based MCP server does not implement yet. Use Cursor, Claude Desktop (via npx @lumifyai/mcp), or any client that supports Bearer-token headers.

> **Tip:** Building with AI? See the [AI-assisted development guide](/docs/ai) for Cursor/Claude prompts, llms.txt, OpenAPI, and copy-paste agent recipes.

<!-- #mcp -->

## Cookbook & Postman

Deeper, copy-paste-ready references for building on Lumify:

| Resource | Description |
| --- | --- |
| [Agent cookbook](/docs/agent-cookbook.md) | End-to-end recipes for REST + MCP, including verified client configs and billing behaviour. |
| [Postman collection](/docs/lumify.postman_collection.json) | Importable collection covering the REST endpoints and MCP JSON-RPC calls. |
| [llms.txt](/llms.txt) | Compact machine-readable overview for LLM agents. |
| [agent.json](/.well-known/agent.json) | Agent manifest with the MCP endpoint and transport. |
| [OpenAPI schema](/openapi.json) | Full machine-readable spec for the REST surface. |

<!-- #agent-resources -->

### Task Recipes
 Copy-paste workflows that combine multiple endpoints for a specific job.

## Track live odds movement

Two ways to watch a line move without hammering [/v1/events/{id}/odds/history](/docs/reference#event-odds-history) on a tight poll loop:

- **Push (recommended):** create a [webhook subscription](/docs/reference#webhooks) with event_types: ["line_move"] — you'll be notified the moment a price or point changes. Transient delivery failures retry automatically; inspect [delivery history](/docs/reference#webhook-deliveries) if a callback looks stuck.

- **Pull:** poll [odds history](/docs/reference#event-odds-history) every few minutes and diff against the last recorded_at you've seen. History is not cached, so every call reflects the latest ingest.

```bash
# Subscribe once — deliveries arrive at your endpoint from then on
curl -X POST https://lumify.ai/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/hooks/lumify", "event_types": ["line_move"]}'
```

<!-- #recipe-odds-movement -->

## Build an MCP betting-splits agent

Give an LLM agent read access to public betting splits with no REST wrapper code — connect to the hosted [MCP server](#mcp) and call its tools directly:

1. Connect Cursor, Claude Desktop, or any MCP client to https://lumify.ai/mcp with your API key as the Bearer token (see the [MCP section](#mcp) for client configs).

2. Call the list_events tool filtered by sport/date to find event IDs.

3. Call the get_splits tool per event ID — the agent reasons over bets%/handle% directly, no JSON parsing code required.

> **Tip:** Prefer REST? The equivalent call is [GET /v1/events/{id}/splits](/docs/reference#event-splits) — MCP and REST share the same billing and rate limits.

<!-- #recipe-mcp-splits -->

## Pull a full event intelligence report in one call

Fetch schedule, odds, and bet intelligence together instead of three separate round trips:

```bash
curl "https://lumify.ai/v1/events/4812?include_odds=true&include_intelligence=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

This costs **3 credits** total (1 base + 1 per include) instead of 3 separate 1-credit calls, and saves two round trips. See [Get an event](/docs/reference#event-detail) for the full parameter reference.

<!-- #recipe-intelligence-report -->

## Provision API access programmatically

Let an agent onboard itself — mint a key, check its balance, and top up credits — without a human touching the dashboard:

```bash
# 1. Mint a key (needs an existing session or key to bootstrap)
curl -X POST https://lumify.ai/api/agent/keys \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "agent-worker-1"}'

# 2. Check balance before a big batch of calls
curl https://lumify.ai/api/agent/credits \
  -H "Authorization: Bearer YOUR_API_KEY"

# 3. Top up if running low
curl -X POST https://lumify.ai/api/agent/credits/topup \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": 1}'
```

Full parameter and error reference: [Manage API keys](/docs/reference#agent-keys) and [Credits & credit packs](/docs/reference#agent-credits).

<!-- #recipe-agent-onboarding -->
