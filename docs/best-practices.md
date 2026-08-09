# Lumify Best Practices

> Canonical URL: https://lumify.ai/docs/best-practices.md
> HTML twin: https://lumify.ai/docs/best-practices

Patterns and anti-patterns for building on Lumify — credit budgeting with `/v1/estimate`, polling, MCP, and agent hygiene.

## Patterns (do)

1. **Estimate before you spend.** `POST /v1/estimate` (MCP `estimate_cost`) is always free and returns min/max credit ranges.
2. **Compound when you need the full picture.** `GET /v1/events/{id}?include_odds=true&include_intelligence=true` is cheaper than three separate calls.
3. **Default to Pinnacle for a single book.** Use `bookmaker=all` only when you need cross-book comparison (2 credits).
4. **Treat `available: false` as success-with-no-data.** It is free — do not retry-storm; back off until the next ingest cycle (~30 min for odds/intel).
5. **Prefer MCP tools when the client supports them.** Hosted at `https://lumify.ai/mcp` — no npx for remote clients; `_meta.credits_used` mirrors REST.
6. **Read rate-limit and credit headers every call.** `X-RateLimit-*`, `X-Credits-Used`, `X-Credits-Remaining`.
7. **Use webhooks or SSE instead of tight polling** for score/status/line_move/intelligence changes.
8. **Cursor-paginate with `after_id`** and stop when `next_after_id` is null. Max `limit=100`.
9. **Branch intelligence on shape.** Presence of `probability` → MLS probability model; `confidence_score` → points model.
10. **Filter with `has_recommend=true`** when you only want events with actionable intelligence.
11. **Keep keys server-side.** Never expose `lmfy-...` in browsers or public repos.
12. **Provision keys/credits via `/api/agent/*`** for agent-autonomous loops after the first human-issued key.

## Anti-patterns (don't)

1. **Don't put the API key in the query string** except for SSE (`?api_key=` is required there because EventSource cannot set headers). Prefer the `Authorization` header everywhere else.
2. **Don't invent endpoints, fields, or credit costs.** Read llms.txt / OpenAPI; ask the user to paste docs if you cannot fetch them.
3. **Don't poll odds faster than the ingest cadence** (~30 minutes). You will burn credits for identical payloads.
4. **Don't assume every sport has intelligence or splits.** Intelligence: MLB/NFL/NCAAF/tennis/FIFA WC/MLS. Splits: MLB/NBA/NHL/NFL.
5. **Don't combine `sort=status` with `after_id`.** It returns 400 — fetch in one page or use `sort=time`.
6. **Don't treat MLS `edges_by_book` / `best.edge` as EV.** It is a line-shopping gap vs sharp consensus, not expected value.
7. **Don't call Lumify from the end-user's browser** with a real key — proxy through your backend.
8. **Don't ignore 429 `retry_after`.** Back off; rate-limited calls cost 0 credits but still waste wall time.
9. **Don't expect ChatGPT/Claude.ai web connectors to work yet** — OAuth is not shipped; use desktop/IDE MCP clients.
10. **Don't document footguns as features.** If an API behavior surprises you, open an issue — we fix APIs rather than warn forever.

## Credit budgeting with `/v1/estimate`

```bash
curl -s -X POST "https://lumify.ai/v1/estimate" \
  -H "Authorization: Bearer lmfy-YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "calls": [
      {"tool": "list_events", "arguments": {"sport": "mlb", "status": "scheduled", "limit": 25}},
      {"tool": "get_event", "arguments": {"event_id": 12345, "include_odds": true, "include_intelligence": true}}
    ]
  }'
```

```
daily_credits ≈ (events_tracked × polls_per_day × cost_per_poll)
              + webhook_or_sse_opens
              + intelligence_refreshes
```

Prefer webhooks/SSE for scores so polls collapse to the odds ingest cadence. Cap loops with `estimate_cost` before a burst.

## Adaptive polling

- **Live scores:** ~1 minute freshness — or open SSE / register a webhook.
- **Odds / splits / intelligence:** ~30 minute ingest — polling faster usually returns identical data.
- Respect `updated_at` / `intelligence_updated_at` / `computed_at`.
- On 429: sleep `retry_after` seconds.

Full limits: https://lumify.ai/docs/rate-limits.md

## Agent hygiene

- Start from https://lumify.ai/docs/ai#context
- Disambiguate: Lumify (lumify.ai) ≠ LUMIFY eye drops ≠ Philips Lumify ultrasound
- Poll https://lumify.ai/changelog.json for breaking changes (≥90 days notice within a major version)
