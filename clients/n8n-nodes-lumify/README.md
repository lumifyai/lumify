# n8n-nodes-lumify

An [n8n](https://n8n.io) community node for [Lumify](https://lumify.ai) — the
agent-ready sports intelligence API. Pulls schedules, live scores, odds,
public betting splits, and explainable AI bet confidence (with rationale)
across 8+ sports directly into your n8n workflows.

## Get an API key

Grab a **free instant key in seconds — no signup, email, or card** at
[lumify.ai/docs/ai](https://lumify.ai/docs/ai) (100 credits, 14-day expiry).

For a persistent account with 1,000 starter credits, use
[lumify.ai/api-keys](https://lumify.ai/api-keys).

## Installation

### Community Nodes (recommended)

1. Go to **Settings → Community Nodes** in your n8n instance.
2. Select **Install** and enter `n8n-nodes-lumify`.
3. Agree to the risks and select **Install**.

Requires n8n with community packages enabled (self-hosted:
`N8N_COMMUNITY_PACKAGES_ENABLED=true`). See the
[n8n community nodes installation guide](https://docs.n8n.io/integrations/community-nodes/installation/).

### Manual (npm)

```bash
npm install n8n-nodes-lumify
```

## Credentials

Create a **Lumify API** credential and paste your API key only (do not include
a `Bearer ` prefix — the node strips it if present).

Optional: override **Base URL** for local/staging (default
`https://lumify.ai`).

## Resources and operations

| Resource | Operations |
| --- | --- |
| Bet Intelligence | Get Bet Intelligence, Get Betting Splits |
| Event | List Events, Get Event, Get Many Events (Batch), Search (Natural Language) |
| Live Score | Get Live Score |
| Odd | Get Odds, Get Odds History |
| Player | List Players, Get Player, Get Player Events |
| Sport | List Sports, List Seasons |
| Team | List Teams, Get Team |

The node is flagged `usableAsTool`, so it can be wired into n8n's AI Agent
nodes as a callable tool.

## Pagination and item splitting

List operations return Lumify's envelope (`events` / `data`, plus
`next_after_id` / `has_more`). Use the **After ID** filter with the previous
page's `next_after_id` to walk pages. Turn on **Split Into Items** when you
want one n8n item per row for looping (leave it off when you still need the
cursor fields).

## Example workflow

List tonight's NFL games with a recommended bet, then post the intelligence
narrative to Slack:

1. **Lumify → List Events** — Resource: Event, Operation: List Events.
   Filters: Sport = `nfl`, Date = today (UTC `YYYY-MM-DD`), Only Events With
   Recommended Bets = true. Enable **Split Into Items**.
2. **Lumify → Get Bet Intelligence** — Resource: Bet Intelligence, Operation:
   Get Bet Intelligence. Set Event ID to `{{$json.id}}`.
3. **Slack → Send Message** with the intelligence narrative from the previous
   step.

## Links

- [Lumify docs](https://lumify.ai/docs/ai)
- [Agent cookbook](https://lumify.ai/docs/agent-cookbook.md)
- [Source](https://github.com/lumifyai/lumify/tree/main/clients/n8n-nodes-lumify)
- [n8n community nodes documentation](https://docs.n8n.io/integrations/#community-nodes)

## License

[MIT](LICENSE)
