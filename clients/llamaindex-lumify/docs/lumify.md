# Lumify

[Lumify](https://lumify.ai) is an agent-ready sports intelligence API: schedules,
live scores, odds, public betting splits, and explainable AI bet confidence
(with rationale) across 8+ sports. Lumify hosts a remote
[MCP](https://modelcontextprotocol.io) server, so it works with LlamaIndex
out of the box via `llama-index-tools-mcp` — no Lumify-specific package
required. `llamaindex-lumify` is an optional convenience wrapper.

## Native MCP (no extra install beyond `llama-index-tools-mcp`)

```bash
pip install llama-index-tools-mcp
```

```python
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec

client = BasicMCPClient(
    "https://lumify.ai/mcp",
    headers={"Authorization": "Bearer lmfy-YOUR_KEY"},
)
tool_spec = McpToolSpec(client=client)
tools = await tool_spec.to_tool_list_async()
```

No key yet? Grab a **free instant key in seconds (no signup, email, or card
required)** at [lumify.ai/docs/ai](https://lumify.ai/docs/ai) (100 credits,
14-day expiry), or create a persistent account key at
[lumify.ai/api-keys](https://lumify.ai/api-keys).

## Optional wrapper: `llamaindex-lumify`

```bash
pip install llamaindex-lumify
```

```python
import os
from llamaindex_lumify import get_lumify_tools

os.environ["LUMIFY_API_KEY"] = "lmfy-YOUR_KEY"  # or pass api_key=...
tools = await get_lumify_tools()
```

Adds over the native path:

- Reads `LUMIFY_API_KEY` and sets `Authorization`/`User-Agent` headers for you.
- Accepts a raw `lmfy-...` value or a `Bearer lmfy-...` copy-paste.
- Rewrites Lumify's raw HTTP 401/402 transport failures (invalid key /
  exhausted credits) into readable tool output with a `/register` or
  `/docs/ai` call-to-action, instead of an unhandled exception crashing the
  agent run.

## Tool features

Loads 18 tools: `list_sports`, `list_seasons`, `list_events`, `get_event`,
`batch_get_events`, `query_events`, `get_live_score`, `get_odds`,
`get_odds_history`, `get_stats`, `get_splits`, `get_intelligence`,
`list_teams`, `get_team`, `search_players`, `get_player`, `get_player_events`,
`estimate_cost`. All are read-only and return structured JSON.

## Use within an agent

```python
import asyncio
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.openai import OpenAI
from llamaindex_lumify import get_lumify_tools


async def main():
    tools = await get_lumify_tools()
    agent = FunctionAgent(tools=tools, llm=OpenAI(model="gpt-4.1"))
    return await agent.run("What's the best MLB bet today, and why?")


asyncio.run(main())
```

## API reference

- `get_lumify_tools(api_key=None, url="https://lumify.ai/mcp", *, require_api_key=True, friendly_errors=True)`
  returns the list of Lumify tools as LlamaIndex `FunctionTool`s.
- `LumifyToolSpec(api_key=None, url=..., *, require_api_key=True, friendly_errors=True, **kwargs)`
  is a `McpToolSpec` subclass; `**kwargs` forwards `allowed_tools`,
  `global_partial_params`, `partial_params_by_tool`, `include_resources`.
- `MissingApiKeyError` is raised when a key is required but none resolves.

Source: [github.com/lumifyai/lumify](https://github.com/lumifyai/lumify).
MCP endpoint: `https://lumify.ai/mcp`
