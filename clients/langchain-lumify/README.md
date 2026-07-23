# langchain-lumify

LangChain integration for [Lumify](https://lumify.ai) — the agent-ready sports
intelligence API. Load **all Lumify tools** (schedules, live scores, odds,
public betting splits, and explainable AI bet confidence across 8+ sports) into
any LangChain or LangGraph agent in one call.

It's a thin, typed wrapper over
[`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters)
pointed at Lumify's hosted MCP server (`https://lumify.ai/mcp`).

## Install

```bash
pip install langchain-lumify
# Agent examples also need:
pip install langchain
```

Or install the latest from source:

```bash
pip install "git+https://github.com/lumifyai/lumify.git#subdirectory=clients/langchain-lumify"
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
from langchain_lumify import get_lumify_tools
from langchain.agents import create_agent


async def main():
    tools = await get_lumify_tools()  # reads LUMIFY_API_KEY
    agent = create_agent("openai:gpt-4.1", tools)
    result = await agent.ainvoke(
        {"messages": "What's the best MLB bet today, with the rationale?"}
    )
    print(result["messages"][-1].content)


asyncio.run(main())
```

Pass a key explicitly or point at a self-hosted endpoint:

```python
tools = await get_lumify_tools(api_key="lmfy-...", url="https://lumify.ai/mcp")
```

### Toolkit

```python
from langchain_lumify import LumifyToolkit

toolkit = await LumifyToolkit.acreate()          # loads the tools
agent = create_agent("openai:gpt-4.1", toolkit.get_tools())
```

Do **not** call `LumifyToolkit()` with no args — that raises. Always use
`acreate()`.

## Tools

Loads the full Lumify MCP tool surface: `list_sports`, `list_seasons`,
`list_events`, `get_event`, `batch_get_events`, `query_events`,
`get_live_score`, `get_odds`, `get_odds_history`, `get_splits`,
`get_intelligence`, `list_teams`, `get_team`, `search_players`, `get_player`,
and `get_player_events`.

## Links

- Docs / instant key: <https://lumify.ai/docs/ai>
- MCP guide: <https://lumify.ai/docs/guides#mcp>
- API reference: <https://lumify.ai/docs/reference>

## License

MIT
