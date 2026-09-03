# Build a live sports scoreboard with the Lumify API

> HTML twin: [/use-cases/live-scoreboard](/use-cases/live-scoreboard)
> Open-source demo: https://github.com/lumifyai/lumify/tree/main/examples/scoreboard

Tutorial: discover in-progress games, stream score updates over SSE (or poll `/score`), and run a cloneable Node demo with a Lumify API key.

## What you'll build

A live scoreboard that lists every game currently `inprogress`, shows team names, scores, period, and clock, and updates in real time — without putting your API key in the browser.

## How it works

1. **Discover** — `GET /v1/events?status=inprogress&include_scores=true&sort=status`
2. **Update** — per game, push with `GET /v1/events/{id}/stream` (SSE) or poll `GET /v1/events/{id}/score`
3. **Render** — map `scores[]`, `period_label`, and `clock` into cards; close when the game finishes

> **Warning:** Keep keys server-side. Don't call Lumify from browser JS with a real `lmfy-…` key — proxy through a small backend. See [/docs/best-practices](/docs/best-practices).

## 1. List live games

```bash
curl "https://lumify.ai/v1/events?status=inprogress&include_scores=true&sort=status" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
live = client.events.list(status="inprogress", include_scores=True, sort="status")
for event in live["events"]:
    print(event["id"], event["name"], event["status"])
```

```js
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
const { events } = await client.events.list({
  status: "inprogress",
  includeScores: true,
  sort: "status",
});
```

Optional: add `sport=nba` (or `mlb`, `nhl`, `soccer`, …) to scope the board.

## 2. Render a scoreboard card

Prefer the lightweight score snapshot for ticks:

`GET /v1/events/{id}/score`

```json
{
  "event_id": 4812,
  "status": "inprogress",
  "period": "3",
  "period_label": "Q3",
  "clock": "8:42",
  "scores": [
    { "role": "home", "name": "Boston Celtics", "abbreviation": "BOS", "score": "101" },
    { "role": "away", "name": "New York Knicks", "abbreviation": "NYK", "score": "98" }
  ],
  "updated_at": "2026-05-10T01:18:44Z"
}
```

Live score responses are cached ~15s while in progress — a natural poll cadence. See [/docs/reference#event-score](/docs/reference#event-score).

## 3. Keep it live — poll vs SSE

- **Push (recommended):** [`GET /v1/events/{id}/stream`](/docs/reference#event-stream) emits `event: score` only on change.
- **Pull:** poll `/score` every ~15–30s.

SSE connections are capped at **5 minutes**; Lumify sends `event: reconnect` before closing. Each key may hold a limited number of concurrent streams (5). Official SDKs reconnect automatically.

```bash
curl -N "https://lumify.ai/v1/events/4812/stream" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```python
from lumify import Lumify

client = Lumify(api_key="YOUR_API_KEY")
for evt in client.events.stream(4812):
    if evt.event == "score":
        print(evt.data["period_label"], evt.data["clock"], evt.data["scores"])
    elif evt.event == "done":
        break
```

```js
import { Lumify } from "@lumifyai/sdk";

const client = new Lumify({ apiKey: "YOUR_API_KEY" });
for await (const evt of client.events.stream(4812)) {
  if (evt.event === "score") renderScore(evt.data);
  if (evt.event === "done") break;
}
```

## 4. Handle game end

- SSE emits `event: done` and closes.
- `/score` returns `status: "final"` (or `walkover`) with `finished: true`.
- The game drops out of `?status=inprogress` on the next discovery poll.

Also handle `429` with `Retry-After`. See [/docs/rate-limits](/docs/rate-limits).

## Get the code

```bash
git clone https://github.com/lumifyai/lumify.git
cd lumify/examples/scoreboard
npm install
cp .env.example .env   # set LUMIFY_API_KEY=lmfy-…
npm start              # → http://localhost:3000
```

Source: https://github.com/lumifyai/lumify/tree/main/examples/scoreboard

## Next steps

- [/docs/reference#event-score](/docs/reference#event-score) · [/docs/reference#event-stream](/docs/reference#event-stream)
- [/docs/guides#recipe-odds-movement](/docs/guides#recipe-odds-movement)
- [/docs/rate-limits](/docs/rate-limits)
- SDKs: `npm i @lumifyai/sdk` · `pip install lumify-sdk`
- [/pricing](/pricing)
