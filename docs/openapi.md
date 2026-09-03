# OpenAPI for Lumify Sports Intelligence

> HTML twin: [/docs/openapi](/docs/openapi)

Machine-readable HTTP contract for Lumify sports schedules, scores, odds, and intelligence.

**Important:** The schema URL is [`https://lumify.ai/openapi.json`](/openapi.json). This page is the human/SEO landing. Do not treat `/docs/openapi` as the OpenAPI document.

## Surfaces

| URL | Audience | Use |
|---|---|---|
| [/openapi.json](/openapi.json) | Machines | Codegen, validators, agent grounding |
| [/api/docs](/api/docs) | Humans | Swagger UI (try-it-out) |
| [/api/redoc](/api/redoc) | Humans | ReDoc (read-focused) |
| [/openapi-llms.txt](/openapi-llms.txt) | LLMs | Compact endpoint dump (~6k tokens) |
| [/docs/openapi.md](/docs/openapi.md) | Agents / crawlers | This markdown twin |

## Auth

`Authorization: Bearer lmfy-…` on protected `/v1` and `/api/agent` paths.

Instant trial key (no signup): [/docs/ai](/docs/ai). Free Tier account: [/register](/register).

## Fetch the schema

```bash
curl -sS https://lumify.ai/openapi.json | head -c 400
```

For token-tight agent context, start with [/openapi-llms.txt](/openapi-llms.txt) or [/llms.txt](/llms.txt), then pull `/openapi.json` when you need full request/response models.

## What's in the schema

- `/v1/*` — sports, seasons, events, scores, odds, history, stats, splits, intelligence, teams, players, estimate
- `/api/agent/*` — agent self-service where applicable
- Documented Bearer security + production server URL

Narrative field docs: [/docs/reference](/docs/reference).

## OpenAPI vs MCP

| | OpenAPI / REST | MCP |
|---|---|---|
| Human landing | `/docs/openapi` | [/sports-mcp-server](/sports-mcp-server) |
| Machine endpoint | `/openapi.json` + `/v1/…` | [/mcp](/mcp) (JSON) |
| Best for | Codegen, custom loops, SDKs | Cursor, Claude Desktop, VS Code tools |

## Related

- [Sports API for AI Agents](/sports-api-for-ai-agents)
- [Sports MCP Server](/sports-mcp-server)
- [API reference](/docs/reference)
- [Agent manifest](/.well-known/agent.json)
- Schema: [/openapi.json](/openapi.json)
