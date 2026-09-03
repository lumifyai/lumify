# @lumifyai/mcp

**Hosted MCP:** [https://lumify.ai/mcp](https://lumify.ai/mcp)  
**Homepage:** [https://lumify.ai](https://lumify.ai)

Point any MCP client that supports remote Streamable HTTP at
`https://lumify.ai/mcp` with `Authorization: Bearer lmfy-…` — that is the
canonical Lumify sports-intelligence MCP server (JSON mode, stateless). You
do **not** need this package for that.

This package is a thin, **zero-dependency** **stdio** bridge for clients that
only speak local stdio. It forwards each JSON-RPC message verbatim to the
hosted endpoint with your API key attached, so the tool catalog, input schemas,
protocol negotiation, and billing all come from the live server — nothing is
duplicated locally. Responses are re-serialized to a single NDJSON line (MCP
stdio forbids embedded newlines), and `MCP-Protocol-Version` is pinned after
`initialize`.

```bash
npx -y @lumifyai/mcp
```

## Requirements

- Node.js 18 or newer
- A Lumify API key. Fastest is the free **instant trial key** — no signup,
  email, or card — at <https://lumify.ai/docs/ai> (100 credits, 14-day expiry).
  For a persistent account with 1,000 credits, create one at
  <https://lumify.ai/api-keys>.

## Usage

```bash
export LUMIFY_API_KEY=lmfy-xxxxxx.yyyyyyyy
npx -y @lumifyai/mcp

# or:
npx -y @lumifyai/mcp --api-key lmfy-xxxxxx.yyyyyyyy
```

The handshake (`initialize`, `tools/list`, `ping`) works without a key; tool
calls require one. All diagnostics go to stderr — stdout carries only the MCP
protocol.

### Options

| Flag | Env | Default | Purpose |
| --- | --- | --- | --- |
| `--api-key <key>` | `LUMIFY_API_KEY` | — | Lumify API key (`lmfy-...`). |
| `--url <endpoint>` | `LUMIFY_MCP_URL` | `https://lumify.ai/mcp` | Override the upstream endpoint. |
| `-h`, `--help` | | | Show help (stderr). |
| `-v`, `--version` | | | Print the version (stderr). |

## Client configuration

### Remote (preferred when your client supports it)

```json
{
  "mcpServers": {
    "lumify": {
      "url": "https://lumify.ai/mcp",
      "headers": { "Authorization": "Bearer lmfy-xxxxxx.yyyyyyyy" }
    }
  }
}
```

### Cursor (`~/.cursor/mcp.json`) — local stdio

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": ["-y", "@lumifyai/mcp"],
      "env": { "LUMIFY_API_KEY": "lmfy-xxxxxx.yyyyyyyy" }
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": ["-y", "@lumifyai/mcp"],
      "env": { "LUMIFY_API_KEY": "lmfy-xxxxxx.yyyyyyyy" }
    }
  }
}
```

## Tools

The tool set is served live by the hosted server (run `tools/list` to see the
current catalog). Today it exposes 24 tools: `list_sports`, `list_seasons`,
`list_events`, `get_event`, `batch_get_events`, `query_events`,
`get_live_score`, `get_odds`, `get_odds_history`, `get_stats`, `get_player_props`, `get_team_props`, `get_prediction_markets`, `get_period_odds`, `get_splits`,
`get_intelligence`, `list_ev`, `list_forecasts`, `list_teams`, `get_team`, `search_players`, `get_player`,
`get_player_events`, and `estimate_cost` (free pre-call credit-cost estimate).

## Billing

Metering happens server-side and mirrors the REST API. `initialize`,
`tools/list`, and `ping` are free; each `tools/call` is metered like the matching
REST call, and calls for data that isn't available yet (odds/intelligence/splits
on an unpriced match) are free (`_meta.credits_used: 0`). Your key is sent only
to `https://lumify.ai/mcp` over HTTPS and is never stored by this package.

## Troubleshooting

- **`tools/call` returns "Unauthorized"** — set `LUMIFY_API_KEY` (or `--api-key`).
- **"Rate limit exceeded"** — you hit the per-key limit; the error includes a
  `retry_after` (seconds). The anonymous limit is lower, so always pass a key.
- **`npx` can't find the package** — ensure Node ≥18 (`node --version`).

## License

[MIT](./LICENSE) © 2026 Lumify AI

## Docs & contact

- Hosted MCP: <https://lumify.ai/mcp>
- Homepage: <https://lumify.ai>
- MCP guide: <https://lumify.ai/docs/guides#mcp>
- Agent manifest: <https://lumify.ai/.well-known/agent.json>
- npm: <https://www.npmjs.com/package/@lumifyai/mcp>
- Contact: <dev@lumify.ai>
