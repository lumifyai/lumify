# llamaindex-lumify

LlamaIndex integration for [Lumify](https://lumify.ai) — the agent-ready sports
intelligence API. Load **all Lumify tools** (schedules, live scores, odds,
public betting splits, and explainable AI bet confidence across 8+ sports) into
any LlamaIndex agent in one call.

LlamaIndex already speaks [MCP](https://modelcontextprotocol.io) natively via
[`llama-index-tools-mcp`](https://pypi.org/project/llama-index-tools-mcp/)
(`BasicMCPClient` + `McpToolSpec`), so this package is a thin convenience layer:
it wires up Lumify's auth headers and turns Lumify's raw 401/402 transport
failures into readable tool output instead of a crashed agent run.

## Install

```bash
pip install llamaindex-lumify
# Agent examples also need:
pip install llama-index
```

Or install the latest from source:

```bash
pip install "git+https://github.com/lumifyai/lumify.git#subdirectory=clients/llamaindex-lumify"
```

## Get a key

Grab a **free instant key in seconds — no signup, email, or card** at
<https://lumify.ai/docs/ai> (100 credits, 14-day expiry). For a persistent
account with 1,000 starter credits, use <https://lumify.ai/api-keys>.

Set it as `LUMIFY_API_KEY`, or pass it explicitly. `get_lumify_tools` **requires
a key by default** so the first tool call does not fail with an opaque 401.
Pass `require_api_key=False` only if you want to introspect the public
`tools/list` catalog. Raw `lmfy-...` values and `Bearer lmfy-...` copy-pastes
are both accepted.

## Quick start

```python
import asyncio
from llamaindex_lumify import get_lumify_tools
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI


async def main():
    tools = await get_lumify_tools()  # reads LUMIFY_API_KEY
    agent = FunctionAgent(tools=tools, llm=OpenAI(model="gpt-4.1"))
    result = await agent.run("What's the best MLB bet today, with the rationale?")
    print(result)


asyncio.run(main())
```

Pass a key explicitly or point at a self-hosted endpoint:

```python
tools = await get_lumify_tools(api_key="lmfy-...", url="https://lumify.ai/mcp")
```

### Tool spec

```python
from llamaindex_lumify import LumifyToolSpec

tool_spec = LumifyToolSpec()          # sync init; reads LUMIFY_API_KEY
tools = await tool_spec.to_tool_list_async()
agent = FunctionAgent(tools=tools, llm=OpenAI(model="gpt-4.1"))
```

`LumifyToolSpec` is a `McpToolSpec` subclass, so `allowed_tools`,
`global_partial_params`, `partial_params_by_tool`, and `include_resources` all
work as documented in
[`llama-index-tools-mcp`](https://pypi.org/project/llama-index-tools-mcp/).

## Tools

Loads the full Lumify MCP tool surface (18 tools): `list_sports`,
`list_seasons`, `list_events`, `get_event`, `batch_get_events`,
`query_events`, `get_live_score`, `get_odds`, `get_odds_history`, `get_stats`,
`get_splits`, `get_intelligence`, `list_teams`, `get_team`, `search_players`,
`get_player`, `get_player_events`, and `estimate_cost` (free pre-call
credit-cost estimate).

## Links

- Docs / instant key: <https://lumify.ai/docs/ai>
- MCP guide: <https://lumify.ai/docs/guides#mcp>
- API reference: <https://lumify.ai/docs/reference>

## License

MIT
