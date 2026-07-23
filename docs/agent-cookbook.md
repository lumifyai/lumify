# Lumify Agent Cookbook

Copy-paste recipes for wiring Lumify into AI agents and apps. Every request needs
an API key (`Authorization: Bearer lmfy-...`).

**Bootstrap:** the fastest start is the free **instant trial key** — no signup,
email, or card — at <https://lumify.ai/docs/ai> (100 credits, 14-day expiry).
For a persistent account plus 1,000 starter credits, create a key in the
dashboard at <https://lumify.ai/api-keys>. After that, agents can create
additional keys and top up credits via `/api/agent/*` using an existing key.

- Base URL: `https://lumify.ai`
- Full machine reference: <https://lumify.ai/llms-full.txt>
- OpenAPI: <https://lumify.ai/openapi.json>
- MCP endpoint: `https://lumify.ai/mcp`
- Postman collection: `docs/external/lumify.postman_collection.json`

---

## 1. Quick tasks (curl)

Get today's best MLB bets (recommended only):

```bash
curl "https://lumify.ai/v1/events?sport=mlb&status=scheduled&has_recommend=true" \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

Find a team's upcoming games (resolve the id first — NL query does not map team names):

```bash
TEAM_ID=$(curl -sS "https://lumify.ai/v1/teams?q=bruins&sport=nhl" \
  -H "Authorization: Bearer $LUMIFY_API_KEY" | jq '.data[0].id')
curl "https://lumify.ai/v1/events?team_id=$TEAM_ID&status=scheduled" \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

Then fetch the intelligence for one event:

```bash
curl "https://lumify.ai/v1/events/12345/intelligence" \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

Poll a live score (or stream it — see §6):

```bash
curl "https://lumify.ai/v1/events/12345/score" \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

---

## 2. Cursor / Claude Desktop (MCP)

Lumify hosts a remote MCP server at `https://lumify.ai/mcp` (Streamable HTTP,
JSON mode). Authenticate with your Lumify API key as a Bearer token. The server
is stateless — no session negotiation is required.

Human-oriented install + prompts: <https://lumify.ai/docs/ai>

**Cursor (one-click)** — open this deeplink, then replace the placeholder key:

```
cursor://anysphere.cursor-deeplink/mcp/install?name=lumify&config=eyJ1cmwiOiJodHRwczovL2x1bWlmeS5haS9tY3AiLCJoZWFkZXJzIjp7IkF1dGhvcml6YXRpb24iOiJCZWFyZXIgWU9VUl9BUElfS0VZIn19
```

**Cursor (remote config)** — add to `~/.cursor/mcp.json` (or a project `.cursor/mcp.json`):

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

**Claude Desktop / stdio** — prefer the published bridge (`@lumifyai/mcp`):

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

Alternatively, bridge with `mcp-remote`:

```json
{
  "mcpServers": {
    "lumify": {
      "command": "npx",
      "args": [
        "-y", "mcp-remote", "https://lumify.ai/mcp",
        "--header", "Authorization: Bearer lmfy-YOUR_KEY"
      ]
    }
  }
}
```

Verify any client interactively with the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector
# Transport: Streamable HTTP  ·  URL: https://lumify.ai/mcp
# Header: Authorization: Bearer lmfy-YOUR_KEY
```

Tools exposed: `list_sports`, `list_seasons`, `list_events`, `get_event`,
`batch_get_events`, `query_events`, `get_live_score`, `get_odds`,
`get_odds_history`, `get_splits`, `get_intelligence`, `list_teams`,
`get_team`, `search_players`, `get_player`, `get_player_events`,
`estimate_cost` (free — pre-call credit-cost estimate for planned calls).

### Recipe — natural-language search then batch detail

```bash
# 1) Parse free text into list filters (1 credit)
curl -sS https://lumify.ai/v1/query \
  -H "Authorization: Bearer $LUMIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"live nhl games today","limit":5}'

# 2) Fetch full detail for the returned ids in one round-trip
curl -sS https://lumify.ai/v1/events/batch \
  -H "Authorization: Bearer $LUMIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"event_ids":[101,102],"include_odds":true}'
```

`query_events` is rule-based (not an LLM). Always inspect `interpreted`,
`equivalent_request`, and `unrecognized_terms` before acting — bare
`football` is ambiguous and left unrecognized on purpose.

Billing: `initialize`, `tools/list`, and `ping` are free; each `tools/call`
costs the same credits as the equivalent REST call (variable-cost tools like
`get_event` with `include_odds` are metered accordingly). Calls that return no
usable data because it isn't available yet — `get_odds`, `get_odds_history`,
`get_splits`, or `get_intelligence` for a match that hasn't been priced/computed
— are **free**: they report `_meta.credits_used: 0` (REST: `X-Credits-Used: 0`).

> Local stdio bridge (for clients that only speak stdio):
> `npx -y @lumifyai/mcp` (forwards to the hosted `/mcp` endpoint; set
> `LUMIFY_API_KEY`). Cursor can also hit the remote endpoint directly as shown
> above. Note: ChatGPT and Claude.ai *web* connectors require OAuth, which is
> not yet supported — use the API-key configs above with desktop/IDE clients.

---

## 3. OpenAI tool calling (Python)

```python
import os
from openai import OpenAI
import requests, json

client = OpenAI()
LUMIFY = "https://lumify.ai"
LUMIFY_API_KEY = os.environ["LUMIFY_API_KEY"]
HEADERS = {"Authorization": "Bearer " + LUMIFY_API_KEY}

tools = [{
    "type": "function",
    "function": {
        "name": "get_intelligence",
        "description": "Get Lumify bet intelligence for an event.",
        "parameters": {
            "type": "object",
            "properties": {"event_id": {"type": "integer"}},
            "required": ["event_id"],
        },
    },
}]

def get_intelligence(event_id: int) -> dict:
    r = requests.get(f"{LUMIFY}/v1/events/{event_id}/intelligence", headers=HEADERS)
    return r.json()

resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the best bet for event 12345?"}],
    tools=tools,
)
call = resp.choices[0].message.tool_calls[0]
args = json.loads(call.function.arguments)
result = get_intelligence(**args)
```

---

## 4. Anthropic tool use (Python)

```python
import os
import anthropic, requests

LUMIFY_API_KEY = os.environ["LUMIFY_API_KEY"]
client = anthropic.Anthropic()
tools = [{
    "name": "list_events",
    "description": "List Lumify events (schedules and live scores).",
    "input_schema": {
        "type": "object",
        "properties": {
            "sport": {"type": "string"},
            "status": {"type": "string"},
        },
    },
}]

def list_events(sport=None, status=None):
    r = requests.get(
        "https://lumify.ai/v1/events",
        params={"sport": sport, "status": status},
        headers={"Authorization": "Bearer " + LUMIFY_API_KEY},
    )
    return r.json()

msg = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "List today's scheduled MLB games."}],
)
```

---

## 5. LangChain / LangGraph (MCP adapters)

Point LangChain at the hosted MCP server and **all 16 Lumify tools load
automatically** — no per-tool wrappers to write or keep in sync. `get_tools()`
(a `tools/list` call) needs no key; tool execution uses the Bearer key you pass.

**Python** — `pip install langchain-mcp-adapters langchain`:

```python
import asyncio
import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_agent


async def main():
    client = MultiServerMCPClient({
        "lumify": {
            "transport": "streamable_http",  # Python adapter name
            "url": "https://lumify.ai/mcp",
            "headers": {
                "Authorization": f"Bearer {os.environ['LUMIFY_API_KEY']}",
            },
        }
    })
    tools = await client.get_tools()  # list_events, get_intelligence, …
    agent = create_agent("openai:gpt-4.1", tools)
    return await agent.ainvoke(
        {"messages": "What's the best MLB bet today?"}
    )


asyncio.run(main())
```

**JavaScript / TypeScript** — `npm i @langchain/mcp-adapters langchain`:

```typescript
import { MultiServerMCPClient } from "@langchain/mcp-adapters";
import { createAgent } from "langchain";

const client = new MultiServerMCPClient({
  mcpServers: {
    lumify: {
      transport: "http", // JS adapter name for Streamable HTTP
      url: "https://lumify.ai/mcp",
      headers: { Authorization: `Bearer ${process.env.LUMIFY_API_KEY}` },
    },
  },
});

const tools = await client.getTools();
const agent = createAgent({ model: "openai:gpt-4.1", tools });
```

Prefer a one-liner? The [`langchain-lumify`](https://pypi.org/project/langchain-lumify/)
package wraps the above:

```bash
pip install langchain-lumify
```

```python
import asyncio
from langchain_lumify import get_lumify_tools
from langchain.agents import create_agent

async def main():
    tools = await get_lumify_tools()  # requires LUMIFY_API_KEY
    agent = create_agent("openai:gpt-4.1", tools)
    return await agent.ainvoke({"messages": "Best MLB bet today?"})

asyncio.run(main())
```

No key yet? Grab a free instant key (no signup) at <https://lumify.ai/docs/ai>.

---

## 6. Live scores without polling (SSE)

`EventSource` cannot set headers, so pass the key as a query param:

```javascript
const es = new EventSource(
  "https://lumify.ai/v1/events/12345/stream?api_key=lmfy-YOUR_KEY"
);
es.addEventListener("score", (e) => console.log(JSON.parse(e.data)));
es.addEventListener("done", () => es.close());
```

Or subscribe a webhook to be pushed score/status/line-move events:

```bash
curl -X POST "https://lumify.ai/v1/webhooks" \
  -H "Authorization: Bearer $LUMIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your.app/hooks/lumify","event_types":["score","line_move"],"sport":"mlb"}'
```

Callback URLs must be public `https` endpoints (localhost, private RFC1918, and
cloud metadata IPs are rejected). Verify deliveries with the
`Lumify-Signature: t=<ts>,v1=<hmac>` header (HMAC-SHA256 of `"<ts>.<body>"`
using your subscription's `signing_secret`). Opening an SSE stream costs
1 credit, is metered against the same API key as Bearer calls, and is capped at
5 concurrent streams per key (`error.code = stream_limit_exceeded` on 429).
Event types: `score`, `status`, `line_move`, `intelligence`.
---

## 7. Handling errors

All errors share one envelope:

```json
{ "error": { "code": "rate_limit_exceeded", "message": "Rate limit exceeded", "status": 429, "doc_url": "https://lumify.ai/docs/reference#error-codes", "retry_after": 42 }, "detail": "Rate limit exceeded" }
```

Switch on `error.code`. Respect `Retry-After` on 429. Budget with the
`X-Credits-Used` / `X-Credits-Remaining` response headers.

Errors (4xx/5xx) are never charged. Requests for odds, line-movement history,
splits, or intelligence on a match where that data isn't available yet succeed
with `200` + `available: false` (or an empty list) and are **not** charged
(`X-Credits-Used: 0`). Read the header rather than assuming a fixed per-call cost.
