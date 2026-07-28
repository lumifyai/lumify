# Lumify — Client SDKs & MCP

[![smithery badge](https://smithery.ai/badge/lumify/sports-intelligence)](https://smithery.ai/servers/lumify/sports-intelligence)
[![lumify MCP server](https://glama.ai/mcp/servers/lumifyai/lumify/badges/score.svg)](https://glama.ai/mcp/servers/lumifyai/lumify)

Official client libraries and [Model Context Protocol](https://modelcontextprotocol.io)
(MCP) integration for [**Lumify**](https://lumify.ai), the agent-ready
sports-intelligence API: real-time schedules, live scores, odds, line movement,
public betting splits, and explainable AI bet confidence across MLB, NFL,
NCAAF, NCAAB, NBA, NHL, tennis, and soccer (FIFA World Cup + MLS, EPL, La Liga,
Serie A, Bundesliga, Ligue 1, and UEFA Champions League).

> This repository is the public home for the **client SDKs, the MCP stdio
> bridge, and developer docs/examples**. Lumify itself is a hosted API at
> `https://lumify.ai` — you don't run a server yourself.

## Get an API key

Everything here authenticates with a Lumify API key (`lmfy-...`).

- **Fastest — no signup:** grab a free **instant trial key** at
  **<https://lumify.ai/docs/ai>** (click "Get instant trial key"). No account,
  email, or credit card — 100 credits, 14-day expiry. Paste it and start calling.
- **Persistent account:** create a key at **<https://lumify.ai/api-keys>** —
  free trial with 1,000 credits, no credit card required.

```bash
export LUMIFY_API_KEY="lmfy-xxxxxx.yyyyyyyy"
```

## Packages

| Runtime | Package | Install | Docs |
|---|---|---|---|
| TypeScript / JavaScript | [`@lumifyai/sdk`](https://www.npmjs.com/package/@lumifyai/sdk) | `npm install @lumifyai/sdk` | [README](./clients/lumify-sdk/README.md) |
| Python | [`lumify-sdk`](https://pypi.org/project/lumify-sdk/) | `pip install lumify-sdk` | [README](./clients/lumify-sdk-python/README.md) |
| MCP stdio bridge | [`@lumifyai/mcp`](https://www.npmjs.com/package/@lumifyai/mcp) | `npx -y @lumifyai/mcp` | [README](./clients/lumify-mcp/README.md) |

## Quick start

### TypeScript

```ts
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: process.env.LUMIFY_API_KEY! });

const { sports } = await client.sports.list();
const event = await client.events.get(12345, { includeOdds: true, includeIntelligence: true });
console.log(event.status, event.intelligence?.bets);
```

### Python

```python
import os
from lumify import Lumify

client = Lumify(api_key=os.environ["LUMIFY_API_KEY"])

sports = client.sports.list()
event = client.events.get(12345, include_odds=True, include_intelligence=True)
print(event["status"], event.get("intelligence"))
```

### curl

```bash
curl https://lumify.ai/v1/events?sport=nfl&status=inprogress \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

## Use it from an AI agent (MCP)

Lumify runs a hosted MCP server at `https://lumify.ai/mcp` (Streamable HTTP,
JSON mode, stateless). Point any MCP-compatible client at it.

**Remote (Cursor, VS Code, Claude Desktop with remote support):**

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

**Local stdio (clients without remote MCP support):**

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

See the [MCP bridge README](./clients/lumify-mcp/README.md) and the
[MCP guide](https://lumify.ai/docs/guides#mcp) for the full tool catalog.

## Documentation

- **API reference:** <https://lumify.ai/docs/reference>
- **Guides (incl. MCP):** <https://lumify.ai/docs/guides>
- **Quick start:** [`docs/getting-started/quick-start.md`](./docs/getting-started/quick-start.md)
- **Agent cookbook:** [`docs/agent-cookbook.md`](./docs/agent-cookbook.md)
- **Postman collection:** [`docs/lumify.postman_collection.json`](./docs/lumify.postman_collection.json)

## Support & contributing

- Questions and bugs: [open an issue](https://github.com/lumifyai/lumify/issues)
- Contribution guidelines: [`CONTRIBUTING.md`](./CONTRIBUTING.md)

## License

[MIT](./LICENSE) © 2026 Lumify AI
