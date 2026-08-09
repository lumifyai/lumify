# crewai-lumify

CrewAI integration for [Lumify Sports Intelligence](https://lumify.ai) — the
agent-ready sports intelligence API. Connect Lumify's hosted MCP server
(schedules, live scores, odds, public betting splits, and explainable AI bet
confidence across 8+ sports) to any CrewAI agent in one call.

It's a thin, typed helper that returns a ready-to-use
[`MCPServerHTTP`](https://docs.crewai.com/en/mcp/overview) for CrewAI's
`Agent(mcps=[...])` DSL, pointed at `https://lumify.ai/mcp`.

## Install

```bash
pip install crewai-lumify
# Agent examples also need a model provider, e.g.:
# pip install 'crewai[openai]'
```

Or install the latest from source:

```bash
pip install "git+https://github.com/lumifyai/lumify.git#subdirectory=clients/crewai-lumify"
```

## Get a key

Grab a **free instant key in seconds — no signup, email, or card** at
<https://lumify.ai/docs/ai> (100 credits, 14-day expiry). For a persistent
account with 1,000 starter credits, use <https://lumify.ai/api-keys>.

Set it as `LUMIFY_API_KEY`, or pass it explicitly. `get_lumify_mcp`
**requires a key by default** so the first tool call does not fail with an
opaque 401. Pass `require_api_key=False` only if you want to introspect the
public `tools/list` catalog. Raw `lmfy-...` values and `Bearer lmfy-...`
copy-pastes are both accepted.

## Quick start

```python
from crewai import Agent, Task, Crew
from crewai_lumify import get_lumify_mcp

agent = Agent(
    role="Sports Analyst",
    goal="Find edges using odds and intelligence",
    backstory="Expert with access to sports market data",
    mcps=[get_lumify_mcp()],  # reads LUMIFY_API_KEY
)

task = Task(
    description="What's the best MLB bet today, with the rationale?",
    expected_output="A short recommendation with confidence and why.",
    agent=agent,
)

result = Crew(agents=[agent], tasks=[task]).kickoff()
print(result)
```

Pass a key explicitly or point at a self-hosted endpoint:

```python
mcp = get_lumify_mcp(api_key="lmfy-...", url="https://lumify.ai/mcp")
agent = Agent(..., mcps=[mcp])
```

Filter to a subset of tools with CrewAI's filter helpers:

```python
from crewai.mcp.filters import create_static_tool_filter
from crewai_lumify import get_lumify_mcp

mcp = get_lumify_mcp(
    tool_filter=create_static_tool_filter(
        allowed_tool_names=["list_events", "get_odds", "get_intelligence"],
    ),
)
```

> **Security note:** CrewAI's `MCPServerHTTP` stores your `Authorization`
> header verbatim, and its default `repr()` includes it. Avoid `print(mcp)`,
> `print(agent)`, or verbose/debug logging that dumps agent or MCP server
> config — it can leak your Lumify API key into logs or crash reports.

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
- CrewAI MCP docs: <https://docs.crewai.com/en/mcp/overview>

## License

MIT
