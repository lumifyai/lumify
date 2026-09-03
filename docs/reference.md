# Lumify API Reference

> Canonical URL: https://lumify.ai/docs/reference.md
> HTML twin: https://lumify.ai/docs/reference

Every v1 capability — endpoints, parameters, streaming, webhooks, agent onboarding, and error codes.

<!-- Auto-generated from api/templates/public/docs_reference.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

# API Reference

Every capability of the Lumify v1 API, grouped by what it does rather than its raw path. New to the API? Start with the [Docs](/docs) overview for auth and rate limits.

> **Tip:** For agents: the Markdown twin of this page is [/docs/reference.md](/docs/reference.md). Full concatenated technical payload: [/docs/llms-full.txt](/docs/llms-full.txt). Endpoint dump alone: [/openapi-llms.txt](/openapi-llms.txt). GEO orientation (FAQ/pricing/coverage): [/llms-full.txt](/llms-full.txt). Explore interactively via [ReDoc](/api/redoc) / [/openapi.json](/openapi.json). Discovery/manifest for autonomous agents lives at [/.well-known/agent.json](/.well-known/agent.json).

### Reference Data
 Sports catalogue and season lookup — stable metadata used to filter all other endpoints.

 [MCP: list_sports, list_seasons →](/docs/guides#mcp)

## List sports

`GET /v1/sports`

Returns all supported sports and their associated leagues. Each league entry includes the currently active season where one exists. Use the slug values to filter other endpoints.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| active_only | boolean | optional | true | When true, exclude sports marked inactive. Pass false to include all sports regardless of status. |

**Request**

```bash
curl https://lumify.ai/v1/sports \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "sports": [
    {
      "id":           1,
      "slug":         "nhl",           // use as ?sport= filter on other endpoints
      "name":         "NHL",
      "is_team_sport": true,           // false for Tennis (individual sport)
      "leagues": [
        {
          "id":             1,
          "slug":           "nhl",         // use as ?league= filter
          "name":           "National Hockey League",
          "abbreviation":   "NHL",
          "league_type":    "team_league", // team_league | individual_tour | tournament
          "country_code":   "USA",
          "current_season": {
            "id":         1,             // use as ?season_id= on /v1/events
            "year":       2026,
            "name":       "NHL 2025-26",
            "phase":      "playoffs",    // preseason | regular_season | playoffs
            "start_date": "2025-10-07",
            "end_date":   "2026-06-30"
          }                              // null if no season is currently active
        }
      ]
    }
  ],
  "total": 6
}
```

<!-- #sports -->

## List seasons

`GET /v1/seasons`

Returns seasons across all leagues. By default only currently active seasons are returned. Use this endpoint to look up a season_id before filtering events by season; pass current_only=false to include historical seasons.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| sport | string | optional | — | Filter to seasons for a single sport slug (e.g. nhl, tennis). Returns an empty list for unknown slugs. |
| current_only | boolean | optional | true | When true (default), return only seasons currently in progress (is_current = true). Pass false to include historical seasons. |

**Request**

```bash
curl "https://lumify.ai/v1/seasons?sport=nhl&current_only=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "seasons": [
    {
      "id":         1,
      "year":       2026,
      "name":       "NHL 2025-26",
      "phase":      "playoffs",     // preseason | regular_season | playoffs
      "start_date": "2025-10-07",
      "end_date":   "2026-06-30",
      "is_current": true,
      "sport":      { "slug": "nhl", "name": "NHL" },
      "league":     { "slug": "nhl", "name": "National Hockey League", "abbreviation": "NHL" }
    }
  ],
  "total": 1
}
```

<!-- #seasons -->

### Schedule & Scores
 Event calendar, natural-language search, batch lookup, full event detail, and live score polling.

 [MCP: list_events, query_events, get_event, batch_get_events, get_live_score →](/docs/guides#mcp)
 [Guide: Track live odds movement →](/docs/guides#recipe-odds-movement)

## List events

`GET /v1/events`

Returns a paginated, filterable list of events — games, matches, or contests across all supported sports. Results are sorted chronologically by starts_at ASC.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| sport | string | optional | — | Filter by sport slug: nfl, nba, mlb, nhl, tennis, soccer, ncaaf, ncaab. Unknown slugs return an empty list. |
| league | string | optional | — | Narrow to a specific league slug (e.g. atp, mls). More specific than sport. |
| status | string | optional | — | Filter by lifecycle status. See the [Status Values](#status-values) table. Returns 400 for unrecognised values. |
| date | string | optional | — | Single-day filter. Format: YYYY-MM-DD (UTC). Mutually exclusive with from / to — combining them returns 400. |
| from | string | optional | — | Range start date (UTC, inclusive). Pair with to. Format: YYYY-MM-DD. |
| to | string | optional | — | Range end date (UTC, inclusive). Max range: 90 days. Returns 400 if exceeded. |
| season_id | integer | optional | — | Restrict to a single season. Obtain the ID from /v1/seasons. |
| team_id | integer | optional | — | Restrict to events where this team participates. Resolve the ID via GET /v1/teams?q=…. Preferred over natural-language team names on POST /v1/query. |
| after_id | integer | optional | — | Pagination cursor. Pass the next_after_id from the previous response to retrieve the next page. |
| limit | integer | optional | 25 | Page size. Range: 1–100. |
| include_scores | boolean | optional | false | When true, each event in the list includes full participants, draw_type, broadcast, court, and order_of_play. Bypasses cache. Intended for small result sets (≤ 200 events). |
| has_recommend | boolean | optional | — | When true, returns only events where the intelligence pipeline has found at least one recommended bet (has_recommend = true). Useful for polling a filtered picks feed without fetching intelligence for every event individually. Requires the analysis pipeline to have run — events not yet analyzed will not appear. |
| sort | string | optional | time | time — chronological by effective start time (default). status — priority order Live → Delayed/Upcoming → Final → Cancelled/Postponed, then chronological within each group. Cursor pagination (after_id) is not supported with sort=status — combining them returns 400. |

**Request**

```bash
# All live NHL games today
curl "https://lumify.ai/v1/events?sport=nhl&status=inprogress" \
  -H "Authorization: Bearer YOUR_API_KEY"

# A week of NBA games
curl "https://lumify.ai/v1/events?sport=nba&from=2026-05-10&to=2026-05-17&limit=50" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "events": [
    {
      "id":                   4812,
      "name":                 "Bruins vs Maple Leafs",
      "sport":                "nhl",
      "league":               "nhl",
      "season_id":            1,
      "starts_at":            "2026-05-10T23:00:00Z",   // UTC
      "scheduled_start_at":   null,                      // set for tennis when start drifts
      "starts_at_qualifier":  null,                      // exact | not_before | following | tbd
      "inprogress_since":     null,                      // first live ingest; stays set after final
      "status":               "scheduled",               // see Status Values table
      "result_type":          null,                      // regulation | overtime | shootout | …
      "period":               null,                      // "3", "Top 7th", "Set 2" when live
      "period_label":         null,                      // human-readable: "Set 2", "Q3" — sport-aware
      "clock":                null,                      // "8:42" when live (sport-dependent)
      "round":                "Round 2",
      "neutral_site":         false,
      "competition": {           // null if event is not linked to a competition
        "id":      1,
        "name":    "ATP Rome",    // clean tournament name, e.g. "ATP Rome", "WTA Roland Garros"
        "surface": "clay",        // clay | grass | hard | indoor_hard | null
        "tier":    "masters_1000" // grand_slam | masters_1000 | atp_500 | atp_250 | wta_1000 | wta_500 | wta_250 | null
      },
      "venue": {
        "id": 1, "name": "TD Garden", "city": "Boston",
        "surface": null, "roof_type": null, "timezone": "America/New_York"
      }
    }
  ],
  "total":          25,         // events on this page
  "next_after_id":  4836       // null on the last page — no more results
}
```

> **Note:** Pagination: Pass next_after_id as ?after_id= on the next request. Repeat until next_after_id is null. The cursor is stable even if new events are ingested between pages.

> **Warning:** Date filter note: ?date and ?from / ?to are mutually exclusive. Combining them returns 400.

<!-- #events -->

## Natural-language event search

`POST /v1/query`

Map free text to the same filters GET /v1/events accepts, then return those events. This is a small **rule-based** mapper — not an LLM call — so results are deterministic and auditable. Costs **1 credit**, same as listing events; interpreting the query text is free.

The response includes the parsed filters (interpreted), the literal equivalent REST call (equivalent_request), and any words that didn't map (unrecognized_terms) so agents can see exactly what was understood.

### Request body

| Field | Type | | Description |
| --- | --- | --- | --- |
| query | string | required | Free text, max 500 characters. Example: live nfl games today. |
| limit | integer | optional | Overrides any limit parsed from the text. Range: 1–100. |

### What the mapper recognizes

| Filter | Examples |
| --- | --- |
| sport | nfl, nba, mlb, nhl, tennis, soccer, ncaaf, ncaab; aliases hockey, basketball, baseball, american football, college football, college basketball. Bare football is ambiguous and left unrecognized. |
| status | live / in progress / in-progress → inprogress; final, upcoming, postponed, cancelled, delayed, suspended, walkover. |
| date / range | today, tomorrow, yesterday; this week / next week / last week (rolling UTC days); next 3 days / last 2 weeks; one YYYY-MM-DD → date, two → from/to. |
| limit | A bare integer 1–100 in the text (e.g. 5 nhl games), overridden by the body field when present. |

**Request**

```bash
curl -X POST https://lumify.ai/v1/query \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"live nhl games today","limit":5}'
```

**Response**

```json
{
  "query": "live nhl games today",
  "interpreted": {
    "sport": "nhl",
    "status": "inprogress",
    "date": "2026-07-16",
    "from": null,
    "to": null,
    "limit": 5
  },
  "unrecognized_terms": [],
  "equivalent_request": "GET /v1/events?sport=nhl&status=inprogress&date=2026-07-16&limit=5",
  "events": [/* same EventSummary objects as GET /v1/events */ ],
  "total": 2,
  "next_after_id": null
}
```

> **Note:** Agent tip: Always check unrecognized_terms and equivalent_request before acting on results. An empty interpreted.sport with unrecognized terms like football means the query was ambiguous — clarify rather than searching all sports.

<!-- #query-events -->

## Get an event

`GET /v1/events/{id}`

Returns the full record for a single event — all participants (teams or players), complete venue data, schedule metadata, and result. Completed events are cached for **1 hour**; all other statuses for **5 minutes**.

Use ?include_odds=true and/or ?include_intelligence=true to embed the current odds and bet intelligence directly in this response, saving extra round trips. Odds are scoped by bookmaker (default Pinnacle). Includes do not add credits — one request is 1 credit. Use [/v1/events/{id}/score](#event-score) when you only need live score data.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Non-integer values return 422. Unknown IDs return 404. |

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| include_odds | boolean | optional | false | When true, embeds the current odds payload under an odds key — same shape as [GET /v1/events/{id}/odds](#event-odds), scoped by bookmaker (default: pinnacle). Does not add credits — the event call stays 1 credit. |
| include_intelligence | boolean | optional | false | When true, embeds the bet intelligence payload under an intelligence key — same shape as [GET /v1/events/{id}/intelligence](#event-intelligence). Does not add credits — the event call stays 1 credit. |
| bookmaker | string | optional | system default | Bookmaker for inlined odds (when include_odds=true) and for intelligence.bets[].market prices (when include_intelligence=true). Valid values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, westgate, wynn, south_point, stations, hardrock, betonline, betr, betrivers, lowvig, all. Defaults to pinnacle. |
| include_alts | boolean | optional | false | When include_odds=true, include alternate spread/total rungs. Default is mains only. |

| Call | Credits |
| --- | --- |
| Event only | 1 |
| include_odds=true and/or include_intelligence=true | 1 — includes do not add credits |

**Request**

```bash
# Basic — 1 credit
curl https://lumify.ai/v1/events/4812 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Compound — event + odds + intelligence in one call (1 credit)
curl "https://lumify.ai/v1/events/4812?include_odds=true&include_intelligence=true" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
// Team sport example (NHL)
{
  "id":                   4812,
  "name":                 "Bruins vs Maple Leafs",
  "sport":                "nhl",
  "league":               "nhl",
  "season_id":            1,
  "starts_at":            "2026-05-10T23:00:00Z", // UTC
  "scheduled_start_at":   null,                   // original time before drift; set for tennis
  "starts_at_qualifier":  null,                   // exact | not_before | following | tbd
  "inprogress_since":     "2026-05-10T23:05:12Z", // first live ingest; stays set after final
  "status":               "final",
  "result_type":          "overtime",             // regulation | overtime | shootout | retired | walkover
  "period":               null,                   // null after game ends; "3", "OT" while live
  "period_label":         null,                   // human-readable period, e.g. "Set 2", "Q3"
  "clock":                null,                   // null after game ends; "8:42" while live
  "round":                "Round 2",
  "draw_type":            null,                   // singles | doubles (tennis); null for team sports
  "neutral_site":         false,
  "broadcast":            "ESPN",
  "court":                null,                   // named court, e.g. "Centre Court" (tennis)
  "order_of_play":        null,                   // 1 = first match of the day on this court
  "competition": null,                          // populated for tennis ATP/WTA events — see tennis example below
  "venue": {
    "id":       1,
    "name":     "TD Garden",
    "city":     "Boston",
    "country":  "USA",
    "surface":  "ice",
    "capacity": 17850,
    "timezone": "America/New_York"       // convert starts_at to local time with this
  },
  "participants": [
    {
      "role":          "home",              // home | away (team sports); player_1 | player_2 (tennis)
      "score":         "3",                // null before game starts; "6-4, 7-5" for tennis
      "game_score":    null,               // live in-game score, e.g. "40-15" (tennis); null otherwise
      "is_winner":     true,               // null until final; true/false after
      "team": {
        "id": 1, "name": "Boston Bruins", "abbreviation": "BOS", "country_code": "USA", "image_url": "https://lumify.ai/media/teams/nhl/1.png"
      },
      "player":        null,               // null for team sports; see tennis example below
      "period_scores": []                 // per-period breakdown; empty [] if unavailable
    },
    {
      "role": "away", "score": "2", "game_score": null, "is_winner": false,
      "team": { "id": 2, "name": "Toronto Maple Leafs", "abbreviation": "TOR", "country_code": "CAN", "image_url": "https://lumify.ai/media/teams/nhl/2.png" },
      "player": null, "period_scores": []
    }
  ],
  "updated_at": "2026-05-11T02:14:37Z"
}

// Tennis singles example — note name format, competition object, and player shape
{
  "id":                   4821,
  "name":                 "Jacob Fearnley v. Giovanni Mpetshi Perricard", // "First Last v. First Last"
  "sport":                "tennis",
  "league":               "atp",
  "season_id":            12,
  "starts_at":            "2026-05-08T10:00:00Z",
  "scheduled_start_at":   "2026-05-08T11:00:00Z", // original announced time
  "starts_at_qualifier":  "not_before",
  "inprogress_since":     "2026-05-08T22:14:03Z", // first ball — not starts_at (session floor)
  "status":               "final",
  "result_type":          "regulation",
  "period":               null,
  "period_label":         null,
  "clock":                null,
  "round":                "Round of 16",
  "draw_type":            "singles",
  "neutral_site":         false,
  "broadcast":            null,
  "court":                "Campo Centrale",
  "order_of_play":        2,
  "competition": {
    "id":      1,
    "name":    "ATP Rome",
    "surface": "clay",           // clay | grass | hard | indoor_hard
    "tier":    "masters_1000"   // grand_slam | masters_1000 | atp_500 | atp_250 | wta_1000 | wta_500 | wta_250
  },
  "venue": {
    "id": 7, "name": "Foro Italico", "city": "Rome", "country": "ITA",
    "surface": "clay", "capacity": null, "timezone": "Europe/Rome"
  },
  "participants": [
    {
      "participant_id": 307,                        // stable Lumify join ID for this participant in this event
      "role":          "player_1",
      "score":         "6-4, 3-6, 6-3",
      "game_score":    null,                       // live: "40-15"; null when not in a game point
      "is_winner":     true,
      "team": null,
      "player": {
        "id":           102,
        "name":         "Jacob Fearnley",          // "First Last" format
        "country_code": "GBR",                     // ISO 3-letter code
        "image_url":    "https://lumify.ai/media/players/tennis/028BdVOj.png"
      },
      "period_scores": [// per-set scores
        { "period": "S1", "score": 6, "tiebreak": null, "confirmed": true },
        { "period": "S2", "score": 3, "tiebreak": null, "confirmed": true },
        { "period": "S3", "score": 6, "tiebreak": null, "confirmed": true }
      ]
    },
    {
      "participant_id": 308,
      "role":          "player_2",
      "score":         "4-6, 6-3, 3-6",
      "game_score":    null,
      "is_winner":     false,
      "team": null,
      "player": {
        "id":           217,
        "name":         "Giovanni Mpetshi Perricard",
        "country_code": "FRA",
        "image_url":    null                         // null until enrichment runs; format: lumify.ai/media/players/tennis/{hash}.png
      },
      "period_scores": [
        { "period": "S1", "score": 4, "tiebreak": null, "confirmed": true },
        { "period": "S2", "score": 6, "tiebreak": null, "confirmed": true },
        { "period": "S3", "score": 3, "tiebreak": null, "confirmed": true }
      ]
    }
  ],
  "updated_at": "2026-05-08T14:31:00Z"
}
```

**Compound response — with `include_odds=true&include_intelligence=true`**

```json
// Standard event fields are unchanged — two additional top-level keys are appended
{
  "id": 4812,
  // ... all standard event fields ...
  "updated_at": "2026-05-10T02:14:37Z",

  "odds": {
    "available": true,
    "bookmakers": [
      {
        "bookmaker": "pinnacle",
        "markets": [
          {
            "key": "h2h",
            "label": "moneyline",
            "outcomes": [
              { "outcome": "Boston Bruins",       "price": -140, "point": null },
              { "outcome": "Toronto Maple Leafs", "price": 120,  "point": null }
            ]
          }
        ],
        "captured_at": "2026-05-10T01:30:00Z"
      }
    ],
    "last_updated": "2026-05-10T01:30:00Z"
  },

  "intelligence": {
    "available": true,
    "odds_source": "pinnacle",
    "has_recommend": true,
    "match_overview": null,
    "rationale": null,
    "intelligence_updated_at": "2026-05-10T01:45:00Z",
    "bets": [/* same bet objects as GET /v1/events/{id}/intelligence */ ]
  }
}
```

> **Warning:** Caching note: When include_odds=true, the compound response is cached for 2 minutes (pre-game/live) rather than the standard 5-minute event TTL, to reflect the faster-moving odds data. Final events remain cached for 1 hour.

> **Note:** Tennis scheduling: For tennis, starts_at is a floor (not a fixed time). scheduled_start_at preserves the original announced time. starts_at_qualifier will be not_before for order-of-play matches. inprogress_since is first ball (first live ingest) — null until the match actually starts, and it stays set after final. Use court and order_of_play to understand draw position.

<!-- #event-detail -->

## Batch get events

`POST /v1/events/batch`

Fetch multiple events by id in a single round-trip — for agents that already have a list of ids (e.g. from GET /v1/events) and want full detail for each without one GET per event. Max **25** ids per call. Each returned event has the same shape as [GET /v1/events/{id}](#event-detail).

Credits are the sum of each event's normal compound cost. Duplicate ids are billed once. Ids that don't exist are returned under not_found and cost nothing. Unavailable odds/intelligence add-ons remain free (billing fairness).

### Request body

| Field | Type | | Description |
| --- | --- | --- | --- |
| event_ids | integer[] | required | 1–25 event ids. Order is preserved in the response. |
| include_odds | boolean | optional | Inline current odds scoped by bookmaker (default: pinnacle). Does not add credits. |
| include_intelligence | boolean | optional | Inline bet intelligence on each event. Does not add credits. |
| bookmaker | string | optional | Bookmaker for inlined odds and intelligence market prices. Defaults to pinnacle. Valid: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, westgate, wynn, south_point, stations, hardrock, betonline, betr, betrivers, lowvig, all. |

**Request**

```bash
curl -X POST https://lumify.ai/v1/events/batch \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"event_ids":[101,102,999],"include_odds":true}'
```

**Response**

```json
{
  "events": [/* EventDetail objects, same shape as GET /v1/events/{id} */ ],
  "not_found": [999],
  "total": 2
}
```

<!-- #events-batch -->

## Get an event's score

`GET /v1/events/{id}/score`

Lightweight score snapshot optimised for live-polling. Returns only the fields needed to render a scoreboard: status, period, clock, and per-participant scores. Cache TTL is **30 seconds** when status=inprogress, and 5 minutes otherwise — poll this endpoint instead of /v1/events/{id} when you only need score state.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Non-integer values return 422. Unknown IDs return 404. |

**Request**

```bash
curl https://lumify.ai/v1/events/4812/score \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "event_id":     4812,
  "status":       "inprogress",
  "period":       "3",            // sport-specific — see period format table below
  "period_label": "Q3",           // human-readable; null if unavailable
  "clock":        "8:42",         // null for MLB, Tennis, NHL (not in source)
  "scores": [
    {
      "role":          "home",
      "name":          "Boston Celtics",
      "abbreviation":  "BOS",
      "score":         "101",
      "game_score":    null,          // live in-game score (tennis only, e.g. "40-15")
      "is_winner":     null,          // null while in-progress; true/false when final
      "period_scores": []             // per-period breakdown; empty [] if unavailable
    },
    {
      "role":          "away",
      "name":          "Los Angeles Lakers",
      "abbreviation":  "LAL",
      "score":         "98",
      "game_score":    null,
      "is_winner":     null,
      "period_scores": []
    }
  ],
  "updated_at":   "2026-05-10T01:18:44Z"  // last ingest write — use to detect staleness
}
```

### Period format by sport

The period field is a free-form string. null when the event has not yet started or the source does not provide this data.

| Sport | Example period | Example clock |
| --- | --- | --- |
| NHL | "1" "2" "3" "OT" "SO" | null |
| NBA / NFL | "1" "2" "3" "4" "OT" | "8:42" "0:00" |
| MLB | "Top 7th" "Bot 9th" | null |
| Tennis | "Set 1" "Set 2" "Set 3" | null |
| Soccer | "1H" "2H" "ET1" "ET2" "PKs" | "45'+2" "67'" |

<!-- #event-score -->

### Bet Intelligence
 Raw team/match statistics (Data), predictive probability / fair price / Price overlay (Intelligence), and public betting splits per event.

 [MCP: get_stats, get_player_props, get_intelligence, get_splits →](/docs/guides#mcp)
 [Guide: Build an MCP betting-splits agent →](/docs/guides#recipe-mcp-splits)
 [Guide: Pull a full intelligence report →](/docs/guides#recipe-intelligence-report)

## Get raw match statistics for an event

`GET /v1/events/{id}/stats`

Returns the deterministic, reproducible team and match statistics behind an event — computed directly from completed results and box scores already in the public record. This is the **Data** layer: no market/odds data (see /v1/events/{id}/odds for that) and no scoring, weighting, confidence, or narrative is attached. /v1/events/{id}/intelligence is the **Intelligence** layer built on top of these same inputs — use this endpoint when you want to run your own analysis on Lumify's underlying aggregates instead of (or alongside) Lumify's judgment. Always returns 200 when the event exists — check available to determine whether both teams have resolved. Returns 404 only if the event ID does not exist, and 400 if the event's sport is not yet supported.

> **Note:** Eight sports today. Other sports return 400. The payload is sport-specific — branch on the event's sport / league_slug, not on whether a given key is present.

| Sport | Shape | Notes |
| --- | --- | --- |
| Soccer | teams.home/away | Club leagues. [Fields](#stats-soccer) |
| MLB | teams.home/away | Includes this-event player_box. [Fields](#stats-mlb) |
| Tennis | players.player_1/player_2 | Main-draw singles. Doubles / qualifying → available: false (free). [Fields](#stats-tennis) |
| NFL | teams.home/away | Team rates + this-event player_box (final). Player settleables: [/player-props](/docs/player-props). [Fields](#stats-nfl) |
| NCAAF | teams.home/away | Same football catalog as NFL (incl. player_box), scoped to ncaaf. [Fields](#stats-nfl) |
| NBA | teams.home/away | Team rates + this-event player_box (final). Player settleables: [/player-props](/docs/player-props). [Fields](#stats-nba) |
| NCAAB | teams.home/away | Same basketball catalog as NBA (incl. player_box), scoped to ncaab. [Fields](#stats-nba) |
| NHL | teams.home/away | Team rates + this-event player_box (skaters/goalies, final). Player settleables: [/player-props](/docs/player-props). [Fields](#stats-nhl) |

- Tennis form / record / rest / H2H count final / complete only — walkovers excluded, retirements included.

- NFL / NCAAF / NBA / NCAAB exclude season_type=preseason from form, rates, record, and H2H.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/8815/stats \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response — club league (e.g. MLS)**

```json
{
  "event_id":     8815,
  "available":    true,
  "league_slug":  "mls",
  "profile":      "club",
  "neutral_site": false,
  "teams": {
    "home": {
      "team_id":      210,
      "name":         "LA Galaxy",
      "abbreviation": "LAG",
      "image_url":    "https://lumify.ai/media/teams/soccer/210.png",
      "rest_days":    6,
      "recent_form": {
        "window":         5,
        "results":        ["W", "W", "D", "L", "W"],
        "goals_scored":   [2, 1, 1, 0, 3],
        "goals_conceded": [0, 1, 1, 2, 0]
      },
      "team_strength": {
        "source": "league_table_ppg",
        "ppg":    1.8,
        "games":  20
      },
      "venue": {
        "source":     "home_away_ppg_split",
        "home_ppg":   2.1,
        "home_games": 12,
        "away_ppg":   1.5,
        "away_games": 12
      },
      "rates_l5": {
        "source": "event_stats_avg",
        "window": "l5",
        "window_size": 5,
        "games": 5,
        "shots_for": 14.2,
        "shots_against": 11.0,
        "shots_on_target_for": 5.1,
        "shots_on_target_against": 4.0,
        "possession_pct": 52.3,
        "corners_for": 5.4,
        "corners_against": 4.2,
        "fouls": 11.0,
        "yellow_cards": 2.1,
        "red_cards": 0.1,
        "passes": 420.0,
        "pass_accuracy_pct": 84.1,
        "saves": 3.2,
        "offsides": 1.8,
        "tackles": 14.0,
        "interceptions": 9.2,
        "blocked_shots": 3.4,
        "assists": 1.6,
        "save_rate": 0.71,
        "field_games": { /* per-field sample size, e.g. "possession_pct": 4 */ }
      },
      "rates_season": { /* same fields; window: "season", no window_size */ }
    },
    "away": { /* same shape as "home" */ }
  },
  "windows": {
    "recent_form": 5,
    "rates_l5": 5,
    "rates_season": "season",
    "head_to_head": 10,
    "sos": 5
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "home_goals": 2, "away_goals": 1 },
      { "home_goals": 0, "away_goals": 0 }
    ],
    "total": 2
  },
  "league_context": {
    "avg_goals_per_team": 1.35
  }
}
```

### Response fields — Soccer

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | false when both teams for this fixture haven't resolved yet. No charge in that case. |
| profile | string | "world_cup" or "club" — which SoccerLeagueProfile this fixture uses, driving which source values appear below. |
| windows | object | Explicit sample depths so agents never guess: recent_form (5), rates_l5 (5), rates_season ("season"), head_to_head (10), sos (5). |
| teams.{home,away}.recent_form | object | Up to the last window (5) completed results, most-recent-first. results is a list of "W"/"D"/"L"; goals_scored/goals_conceded align by index. |
| teams.{home,away}.rest_days | integer \| null | Days since this team's last completed match in the same league. null if this is their first match of the competition. |
| teams.{home,away}.team_strength | object | Club leagues (source: "league_table_ppg"): season table row — ppg, games, points, w/d/l, gf/ga/gd, and ordinal rank (points → GD → GF). |
| teams.{home,away}.sos | object \| null | Strength-of-schedule lite — average opponent PPG/rank across the last 5 completed league games (source: "opp_ppg_avg"). null until enough league games exist. |
| teams.{home,away}.lineup | object | Formation + starters/bench from ingested rosters (available: false until then). Each player has name, position, jersey, formation_place, espn_athlete_id. |
| teams.{home,away}.venue | object | Club leagues (source: "home_away_ppg_split"): this team's own points-per-game when playing at home vs. away this season (each null until a minimum sample of completed games exists). |
| teams.{home,away}.rates_l5 | object | Per-game averages from the last 5 completed matches with team box scores (source: "event_stats_avg"): shots / SoT, possession, corners, cards, saves / save_rate, plus offsides / tackles / interceptions / blocked_shots / assists (team assists summed from per-player goalAssists). Shot location is not exposed. games is 0 (rates null) until boxes land; field_games is how many of those games had each field. |
| teams.{home,away}.rates_season | object | Same shape as rates_l5 but averaged over the current season. window is "season" (no window_size). |
| head_to_head | object | Up to the last window (10) meetings between these two teams in this league, most-recent-first from the current home team's perspective. |
| league_context.avg_goals_per_team | number \| null | Season-to-date league-wide average goals scored per team per game. null before enough club-season games exist. |

**Response — MLB**

```json
{
  "event_id":     88410,
  "available":    true,
  "league_slug":  "mlb",
  "teams": {
    "home": {
      "team_id":      120,
      "name":         "Washington Nationals",
      "abbreviation": "WSH",
      "rest_days":    1,
      "recent_form": {
        "window":        5,
        "results":       ["W", "L"],
        "runs_scored":   [11, 3],
        "runs_allowed":  [4, 6]
      },
      "record": {
        "source":           "season_to_date",
        "wins":             55,
        "losses":           53,
        "games":            108,
        "win_pct":          0.5093,
        "run_differential": 14
      },
      "rates_l5": {
        "source": "player_game_stats_sum",
        "window": "l5",
        "window_size": 5,
        "games": 5,
        "batting_avg": 0.244,
        "obp": 0.318,
        "slg": 0.392,
        "ops": 0.710,
        "era": 4.72,
        "whip": 1.38,
        /* + at_bats, hits, runs, home_runs, walks, strikeouts, doubles, triples, rbi, hit_by_pitch, stolen_bases, total_bases, innings_pitched, earned_runs, hits_allowed, walks_allowed, strikeouts_pitched, home_runs_allowed, k9, bb9 */
        "field_games": { /* per-field sample size, e.g. "hits": 5 */ }
      },
      "rates_season": { /* same fields; window: "season", no window_size */ },
      "starting_pitcher": {
        "available": true,
        "player_id": 674841,
        "name": "Home Starter",
        "games_started": 22,
        "innings_pitched": 128.1,
        "era": 3.92,
        "whip": 1.21,
        "k9": 8.4,
        "bb9": 2.6
      },
      "lineup": {
        "available": true,
        "batting_order": [/* 9 batters, ordered, each {name, position, player_id, role, batting_order, starter} */ ],
        "starting_pitcher": { "name": "Home Starter", "player_id": 674841, "role": "pitcher", "starter": true },
        "bench": [/* pinch hitters / relievers / subs who appeared */ ],
        "captured_at": "2026-08-03 22:15:00"
      },
      "player_box": {
        "available": true,
        "batters": [/* {player_id, name, position, at_bats, runs, hits, rbi, doubles, triples, home_runs, walks, strikeouts, stolen_bases, caught_stealing, hit_by_pitch, left_on_base} */ ],
        "pitchers": [/* {player_id, name, position, innings_pitched, outs, games_started, earned_runs, hits_allowed, runs_allowed, walks_allowed, strikeouts_pitched, home_runs_allowed, hit_batsmen, pitches_thrown, strikes_thrown, batters_faced} */ ]
      }
    },
    "away": { /* same shape as "home" */ }
  },
  "windows": {
    "recent_form": 5,
    "rates_l5": 5,
    "rates_season": "season",
    "head_to_head": 10
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "home_runs": 3, "away_runs": 1 }
    ],
    "total": 1
  }
}
```

### Response fields — MLB

| Field | Type | Description |
| --- | --- | --- |
| windows | object | recent_form (5), rates_l5 (5), rates_season ("season"), head_to_head (10) — no sos, unlike soccer. |
| teams.{home,away}.recent_form | object | Up to the last window (5) completed results, most-recent-first. results is "W"/"L" (no ties in MLB); runs_scored/runs_allowed align by index. |
| teams.{home,away}.rest_days | integer or null | Days since this team's last completed game in the same league. null if this is their first game of the season. |
| teams.{home,away}.record | object | Season-to-date source: "season_to_date" record: wins, losses, games, win_pct, runs_for, runs_against, run_differential. |
| teams.{home,away}.rates_l5 / rates_season | object | Team batting/pitching rate aggregates (source: "player_game_stats_sum") — every player's per-game box-score line summed to the team-game level, then averaged/derived across the window. batting_avg/obp/slg/ops/era/whip/k9/bb9 are derived from the sum of their component totals, not an average of per-game ratios. Counting fields include rbi, triples, total_bases, and hit_by_pitch. obp uses (H+BB+HBP)/(AB+BB+HBP) — sacrifice flies are not in Path A ingest. Includes field_games per field, same convention as soccer. |
| teams.{home,away}.starting_pitcher | object | The game's own starting pitcher's season-to-date era/whip/k9/bb9, derived via outs-based ratio-of-sums from his own box-score rows. available: false until a post-final box score with lineup lands — pregame probable pitchers stay on /intelligence, not /stats. |
| teams.{home,away}.lineup | object | batting_order (9 batters, ordered) + starting_pitcher + bench (pinch hitters/relievers/subs) from the ingested final box score. No formation field — not a baseball concept. available: false until post-game ingest. |
| teams.{home,away}.player_box.batters | object[] | This event's batting lines (sorted by name): at_bats, runs, hits, rbi, doubles, triples, home_runs, walks, strikeouts, stolen_bases, caught_stealing, hit_by_pitch, left_on_base. No per-player AVG/OBP. Two-way players also appear under pitchers. |
| teams.{home,away}.player_box.pitchers | object[] | This event's pitching lines (starter first, then outs desc): innings_pitched (baseball notation), outs, games_started, earned_runs, hits_allowed, runs_allowed, walks_allowed, strikeouts_pitched, home_runs_allowed, hit_batsmen, pitches_thrown, strikes_thrown, batters_faced. No per-player ERA. player_box.available is false until post-final ingest. Player settleables: [/player-props](/docs/player-props). |
| head_to_head | object | Up to the last window (10) meetings between these two teams, most-recent-first. meetings use home_runs/away_runs — not home_goals/away_goals. |

**Response — NFL**

```json
{
  "event_id":    12001,
  "available":   true,
  "league_slug": "nfl",
  "windows": {
    "recent_form": 5,
    "rates_l5": 5,
    "rates_season": "season",
    "head_to_head": 10
  },
  "teams": {
    "home": {
      "team_id": 12,
      "name": "Kansas City Chiefs",
      "abbreviation": "KC",
      "rest_days": 7,
      "recent_form": {
        "window": 5,
        "results": ["W", "L"],
        "points_scored": [27, 17],
        "points_allowed": [20, 24]
      },
      "record": {
        "source": "season_to_date",
        "wins": 10, "losses": 3, "games": 13,
        "win_pct": 0.7692,
        "points_for": 312, "points_against": 245,
        "point_differential": 67
      },
      "rates_l5": {
        "source": "event_stats_avg", "window": "l5",
        "window_size": 5, "games": 5,
        "total_yards": 368.2, "yards_allowed": 312.4,
        "passing_yards": 241.0, "rushing_yards": 127.2,
        "turnovers": 1.2, "third_down_pct": 42.5
      },
      "rates_season": { /* same keys as rates_l5; window "season" */ }
    },
    "away": { /* same shape as "home" */ }
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "home_points": 27, "away_points": 20 }
    ],
    "total": 1
  }
}
```

### Response fields — NFL

| Field | Type | Description |
| --- | --- | --- |
| windows | object | recent_form (5), rates_l5 (5), rates_season ("season"), head_to_head (10). |
| teams.{home,away}.recent_form | object | Up to the last window (5) completed results, most-recent-first. results is "W"/"L" (ties omitted); points_scored/points_allowed align by index. |
| teams.{home,away}.rest_days | integer or null | Days since this team's last completed game in the same league (NFL or NCAAF). null if this is their first game of the season. Preseason is excluded from the lookback. |
| teams.{home,away}.record | object | Season-to-date record: wins, losses, games, win_pct, points_for, points_against, point_differential. |
| teams.{home,away}.rates_l5 / rates_season | object | Team box averages (source: "event_stats_avg"): total_yards, yards_allowed, passing_yards (net), rushing_yards, attempts, turnovers, third_down_pct (ratio-of-sums). |
| teams.{home,away}.player_box.players | object[] | This event's per-player counting stats (final games only; available: false pregame/in-progress): passing/rushing/receiving/defense/kicking fields on one line per athlete. Sorted passing_yards desc. NCAAF uses the same football shape. Settleables: [/player-props](/docs/player-props). |
| head_to_head | object | Up to the last window (10) meetings. meetings use home_points/away_points. |

**NCAAF** uses the same football-native field catalog as NFL above (league_slug: "ncaaf"). Aggregates are scoped to the NCAAF league so college rates never mix with NFL. Judgment stays on /intelligence.

**Response — NBA**

```json
{
  "event_id":    8579,
  "available":   true,
  "league_slug": "nba",
  "windows": {
    "recent_form": 5,
    "rates_l5": 5,
    "rates_season": "season",
    "head_to_head": 10
  },
  "teams": {
    "home": {
      "team_id": 35,
      "name": "New York Knicks",
      "abbreviation": "NYK",
      "rest_days": 2,
      "recent_form": {
        "window": 5,
        "results": ["L", "W", "W"],
        "points_scored": [111, 105, 105],
        "points_allowed": [115, 104, 95]
      },
      "record": {
        "source": "season_to_date",
        "wins": 13, "losses": 1, "games": 14,
        "win_pct": 0.9286,
        "points_for": 1673, "points_against": 1404,
        "point_differential": 269
      },
      "rates_l5": {
        "source": "event_stats_avg", "window": "l5",
        "window_size": 5, "games": 3,
        "rebounds": 46.33, "assists": 22.33,
        "steals": 7.67, "blocks": 5.33,
        "turnovers": 12.33, "fouls": 23.0,
        "fg_pct": 42.67, "three_point_pct": 35.0, "free_throw_pct": 82.33
      },
      "rates_season": { /* same keys as rates_l5; window "season" */ }
    },
    "away": { /* same shape as "home" */ }
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "home_points": 111, "away_points": 115 }
    ],
    "total": 1
  }
}
```

### Response fields — NBA

| Field | Type | Description |
| --- | --- | --- |
| windows | object | recent_form (5), rates_l5 (5), rates_season ("season"), head_to_head (10). |
| teams.{home,away}.recent_form | object | Up to the last window (5) completed results, most-recent-first. results is "W"/"L" (NBA games don't tie); points_scored/points_allowed align by index. |
| teams.{home,away}.rest_days | integer or null | Days since this team's last completed game in the same league (NBA or NCAAB). null if this is their first game of the season. Preseason is excluded from the lookback. |
| teams.{home,away}.record | object | Season-to-date record: wins, losses, games, win_pct, points_for, points_against, point_differential. |
| teams.{home,away}.rates_l5 / rates_season | object | Team box averages (source: "event_stats_avg"): rebounds, assists, steals, blocks, turnovers, fouls; fg_pct / three_point_pct / free_throw_pct as ratio-of-sums. |
| teams.{home,away}.player_box.players | object[] | This event's per-player counting stats (final games only): points, rebounds, assists, turnovers, steals, blocks, fouls, three_pointers_made, three_pointers_attempted. Sorted points desc. NCAAB uses the same basketball shape. Settleables: [/player-props](/docs/player-props). |
| head_to_head | object | Up to the last window (10) meetings. meetings use home_points/away_points. |

**NCAAB** uses the same basketball-native field catalog as NBA above (league_slug: "ncaab"). Aggregates are scoped to the NCAAB league so college rates never mix with NBA.

**Response — NHL**

```json
{
  "event_id":    8756,
  "available":   true,
  "league_slug": "nhl",
  "windows": {
    "recent_form": 5,
    "rates_l5": 5,
    "rates_season": "season",
    "head_to_head": 10
  },
  "teams": {
    "home": {
      "team_id": 124,
      "name": "Vegas Golden Knights",
      "abbreviation": "VGK",
      "rest_days": 3,
      "recent_form": {
        "window": 5,
        "results": ["L", "L", "W"],
        "goals_scored": [2, 3, 5],
        "goals_allowed": [4, 5, 4]
      },
      "record": {
        "source": "season_to_date",
        "wins": 13, "losses": 6, "games": 19,
        "win_pct": 0.6842,
        "goals_for": 70, "goals_against": 54,
        "goal_differential": 16
      },
      "rates_l5": {
        "source": "event_stats_avg", "window": "l5",
        "window_size": 5, "games": 5,
        "shots_on_goal": 26.0, "hits": 39.2,
        "penalty_minutes": 6.0, "power_play_goals": 0.4,
        "giveaways": 17.8, "takeaways": 4.6,
        "blocked_shots": 20.2
      },
      "rates_season": { /* same keys as rates_l5; window "season" */ }
    },
    "away": { /* same shape as "home" */ }
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "home_goals": 2, "away_goals": 4 }
    ],
    "total": 5
  }
}
```

### Response fields — NHL

| Field | Type | Description |
| --- | --- | --- |
| windows | object | recent_form (5), rates_l5 (5), rates_season ("season"), head_to_head (10). |
| teams.{home,away}.recent_form | object | Up to the last window (5) completed results, most-recent-first. results is "W"/"L" (NHL games always resolve via OT/shootout — no ties); goals_scored/goals_allowed align by index. |
| teams.{home,away}.rest_days | integer or null | Days since this team's last completed game. null if this is their first game of the season. |
| teams.{home,away}.record | object | Season-to-date record: wins, losses (includes OT/shootout losses), games, win_pct, goals_for, goals_against, goal_differential. |
| teams.{home,away}.rates_l5 / rates_season | object | Team box averages from persisted NHL box scores (source: "event_stats_avg"): shots_on_goal, hits, penalty_minutes, power_play_goals, giveaways, takeaways, blocked_shots. |
| teams.{home,away}.player_box.skaters / goalies | object[] | This event's per-player counting stats (final games only). Skaters: goals, assists (slug assists_nhl), plus_minus, penalty_minutes, hits (slug hits_nhl), power_play_goals, shots_on_goal, blocked_shots, giveaways, takeaways. Goalies: saves, goals_against, shots_against, penalty_minutes. Settleables: [/player-props](/docs/player-props). |
| head_to_head | object | Up to the last window (10) meetings. meetings use home_goals/away_goals. |

**Response — tennis (ATP/WTA main-draw singles)**

```json
{
  "event_id":    17438,
  "available":   true,
  "league_slug": "wta",
  "draw_type":   "singles",
  "windows": {
    "recent_form": 10,
    "surface_form": 10,
    "head_to_head": 10,
    "record_lookback_days": 365,
    "career_surface_years": 3
  },
  "match": {
    "surface": "hard",
    "competition_name": "Canadian Open",
    "tier": "1000",
    "round": "Round of 16",
    "court": null,
    "status": "final",
    "scoreboard": {
      "sets_won": { "player_1": 2, "player_2": 0 },
      "winner_role": "player_1",
      "sets": [
        { "period_num": 1, "player_1_games": 6, "player_2_games": 4, "tiebreak_score": null }
      ]
    }
  },
  "players": {
    "player_1": {
      "player_id": 1,
      "name": "Alexandra Eala",
      "ranking": 64,
      "rest_days": 2,
      "recent_form": { "window": 10, "results": ["W", "L"], "sets_for": [2, 0], "sets_against": [0, 2] },
      "surface_form": { "surface": "hard", "window": 10, "results": ["W"], "sets_for": [2], "sets_against": [0] },
      "record": { "source": "tour_lookback", "lookback_days": 365, "wins": 12, "losses": 8, "games": 20 },
      "career_rates": {
        "source": "tennis_api", "window": "career",
        "hold_pct": 0.78, "break_pts_converted": 0.42, "break_pts_saved": 0.61,
        "first_serve_pct": 0.63, "first_serve_won": 0.71, "second_serve_won": 0.52,
        "aces": null, "double_faults": null
      },
      "career_surface": {
        "source": "tennis_api", "window_years": 3, "surface": "hard",
        "wins": 40, "losses": 18, "win_pct": 0.6897
      }
    },
    "player_2": { /* same shape as player_1 */ }
  },
  "head_to_head": {
    "window": 10,
    "meetings": [
      { "event_id": 9001, "surface": "hard", "winner_role": "player_1", "sets_won": { "player_1": 2, "player_2": 1 } }
    ],
    "total": 1
  }
}
```

### Response fields — tennis

| Field | Type | Description |
| --- | --- | --- |
| draw_type | string | Always singles when available is true. Doubles, qualifying, or unresolved players return available: false (free). |
| match | object | Surface, competition, tier, round, court, status, result_type, and scoreboard (sets won + per-set games from lumify_period_scores). round uses ingested labels (Round of 16, Quarterfinal, … — not abbreviated codes like R16). court and sets[].tiebreak_score are not currently populated by ingest. |
| players.{player_1,player_2} | object | Identity, current ranking/points (not as-of match day), rest days, recent_form / surface_form (W/L + sets), record (tour_lookback wins/losses over 365 days), plus Stage-2 career_rates (serve/return percentages; null until ingest) and career_surface (match-surface W/L over windows.career_surface_years). Form/record/rest count final/complete only — walkovers excluded; retirements included. |
| head_to_head | object | Prior singles meetings (final/complete only — walkovers excluded). winner_role / sets_won are relative to this fixture's player_1 / player_2 ids. |

> **Tip:** Pairs with /intelligence: /stats is the sport-specific Data layer (no scoring). /intelligence is judgment. Soccer, MLB, tennis, NFL, and NCAAF expose predictive bets[] (fair-probability + Price). MLB, NFL, NCAAF, NBA, NCAAB, and NHL also score player-prop forecasts[] — including when available is still false on NBA / NCAAB / NHL. Fetch both when you want Data alongside judgment. How forecasts work: [/docs/forecasts](/docs/forecasts).

<!-- #event-stats -->

## Get player-prop lines and live progress

`GET /v1/events/{id}/player-props`

NFL, NCAAF, NBA, NCAAB, NHL, and MLB only. Joins persisted player-prop mains to this-event player box counts and grades over/under/push (1:1 slugs, combo sums, weighted total bases, anytime TD, double-double/triple-double, hockey points). GET /odds stays on moneyline/spread/total — this is the settleable surface. Always returns 200 when the event exists and the sport is supported — check available. Returns 404 if the event ID does not exist, and 400 if the sport is not NFL, NCAAF, NBA, NCAAB, NHL, or MLB. available:false is free.

> **Note:** Coverage inventory (sport × market key, settleable vs returned-not-graded): [/docs/player-props](/docs/player-props). Other sports return 400.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/12345/player-props \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id": 12345,
  "available": true,
  "sport": "nfl",
  "status": "inprogress",
  "period": "3",
  "clock": "8:42",
  "player_props": [
    {
      "player": "Patrick Mahomes",
      "player_id": 42,
      "market": "passing_yards",
      "line": 275.5,
      "current": 187.0,
      "pct_of_line": 67.9,
      "settleable": true,
      "result": "in_progress",
      "books": {
        "pinnacle": { "over": -115, "under": -105 },
        "fanduel": { "over": -110, "under": -110 }
      }
    }
  ]
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | False when no player-prop mains have been ingested. Not charged. |
| sport | string | Event sport slug (nfl, ncaaf, nba, ncaab, nhl, mlb). |
| status | string | Event status. Same enum as [#status-values](#status-values). |
| period / clock | string or null | Live clock. Same sport-specific formats as [#event-score](#event-score). Both null before tip / kickoff / first pitch. |
| player_props[].player | string | Display name from the priced line (generational suffixes stripped). Bind to a roster via player_id. |
| player_props[].player_id | integer or null | Lumify player ID. Join key to GET /v1/players/{id}. Null when the priced name did not bind to this event's roster. |
| player_props[].market | string | Prop market category (used as lumify_odds.market_key). Inventory: [/docs/player-props](/docs/player-props). |
| player_props[].line | number | Posted main Over/Under for this player × market. Half-points are typical. A book that posted a different number is a separate row, not an alternate on this one. |
| player_props[].current | number or null | This-event counting stat from the live/final box — a direct 1:1 slug, a combo sum, or a yes/no threshold (1.0/0.0). Null before the box lands, when the player is unmatched, or when settleable is false. |
| player_props[].pct_of_line | number or null | current / line × 100, one decimal. Can exceed 100. Null when current or line is null, when line is 0, or on yes/no markets (double-double / triple-double / anytime TD) — those grade from a 1.0/0.0 threshold, not a percent of line. |
| player_props[].settleable | boolean | True when this market has a settlement rule. When false, current and result are null — the line is returned, not graded. Catalog: [/docs/player-props#fields](/docs/player-props#fields). |
| player_props[].result | string or null | in_progress while the event is not final. over / under / push once final and current is present. Null when settleable is false. |
| player_props[].books | object | Per-book Over/Under American-odds integers at this exact line. A missing side is null. A book that posted a different number appears on a separate row. |

<!-- #event-player-props -->

## Get team-total lines and live progress

`GET /v1/events/{id}/team-props`

NFL, NCAAF, MLB, and soccer. Joins persisted Pinnacle team-total mains (each team's full-game points/runs/goals Over/Under) to this-event participant scores and grades over/under/push. GET /odds stays on moneyline/spread/total — this is the settleable surface. Always returns 200 when the event exists and the sport is supported — check available. Returns 404 if the event ID does not exist, and 400 if the sport is not supported. available:false is free.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/12345/team-props \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id": 12345,
  "available": true,
  "sport": "nfl",
  "status": "inprogress",
  "period": "3",
  "clock": "8:42",
  "team_props": [
    {
      "team": "Buffalo Bills",
      "team_id": 12,
      "side": "away",
      "market": "team_total",
      "line": 21.5,
      "current": 14.0,
      "pct_of_line": 65.1,
      "settleable": true,
      "result": "in_progress",
      "books": {
        "pinnacle": { "over": -105, "under": -115 }
      }
    }
  ]
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | False when no team-total mains have been ingested. Not charged. |
| sport / status / period / clock | string or null | Same live-progress envelope as player-props. Clock formats: [#event-score](#event-score). |
| team_props[].team | string | Display name of the side this total is priced on. |
| team_props[].team_id | integer or null | Lumify team ID. Join key to GET /v1/teams/{id}. |
| team_props[].side | string | home or away. |
| team_props[].market | string | Always team_total in v1 — each team's full-game points, runs, or goals Over/Under. |
| team_props[].line | number | Posted main Over/Under for this team's full-game points. Half-points are typical. |
| team_props[].current | number or null | This-event team score from the live/final box. Null before kickoff. |
| team_props[].pct_of_line | number or null | current / line × 100, one decimal. Can exceed 100. Null when current or line is null. |
| team_props[].settleable | boolean | True when this market grades from the team score. When false, result is null. |
| team_props[].result | string or null | in_progress while the event is not final. over / under / push once final and current is present. |
| team_props[].books | object | Per-book Over/Under American-odds integers at this exact line. |

<!-- #event-team-props -->

## Get prediction-market game-line probabilities

`GET /v1/events/{id}/prediction-markets`

NFL, NCAAF, NBA, NHL, MLB, soccer, and tennis. Persist-then-read implied probabilities from Fanatics Markets, Kalshi, and Polymarket. Prices are in (0, 1] — never American odds, never a 17th sportsbook, never GET /odds. Game-line contracts only (moneyline / spread / total; soccer 1X2 as three outcomes). Always returns 200 when the event exists and the sport is supported — check available. Returns 404 if the event ID does not exist, and 400 if the sport is not supported (including NCAAB). available:false is free.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/12345/prediction-markets \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id": 12345,
  "available": true,
  "sport": "nfl",
  "venues": [
    {
      "venue": "kalshi",
      "display_name": "Kalshi",
      "markets": [
        {
          "key": "h2h",
          "outcomes": [
            { "label": "Kansas City Chiefs", "probability": 0.62, "contract_id": "KXNFLGAME-..." }
          ]
        }
      ]
    }
  ]
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | False when no prediction-market rows have been ingested. Not charged. |
| sport | string or null | Sport slug. Supported: nfl, ncaaf, nba, nhl, mlb, soccer, tennis. |
| venues[].venue | string | fanaticsmarkets, kalshi, or polymarket. Not a BOOK_SLUGS sportsbook. |
| venues[].display_name | string | Human venue name. |
| venues[].markets[].key | string | h2h, spreads, or totals. |
| venues[].markets[].point | number or null | Spread or total number. Omitted on moneyline. |
| venues[].markets[].outcomes[].label | string | Team name, Draw, Over, or Under. |
| venues[].markets[].outcomes[].probability | number | Implied probability in (0, 1]. Never American odds. |
| venues[].markets[].outcomes[].contract_id | string or null | Nadex symbol, Kalshi ticker, or Polymarket condition id. |

<!-- #event-prediction-markets -->

## Get first-half / first-five / first-set lines and live progress

`GET /v1/events/{id}/period-odds`

NFL, NCAAF, NBA, NCAAB, MLB, soccer, and tennis. Joins persisted first_half_spreads / first_half_totals mains to this-event period scores and grades the period, not the full game (1H = Q1+Q2, or NCAAB/soccer native 1H; MLB F5 = innings 1–5; tennis S1 = first-set games). GET /odds stays on moneyline/spread/total. Always returns 200 when the event exists and the sport is supported — check available. Returns 404 if the event ID does not exist, and 400 if the sport is not supported. available:false is free.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/12345/period-odds \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id": 12345,
  "available": true,
  "sport": "nfl",
  "status": "inprogress",
  "period": "3",
  "clock": "8:42",
  "period_odds": [
    {
      "scope": "1H",
      "market": "first_half_totals",
      "line": 24.5,
      "home_score": 17.0,
      "away_score": 10.0,
      "current": 27.0,
      "pct_of_line": 110.2,
      "settleable": true,
      "scope_complete": true,
      "result": "over",
      "books": {
        "fanduel": { "over": -110, "under": -110 }
      }
    }
  ]
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | False when no first-half / first-five / first-set mains have been ingested. Not charged. |
| sport / status / period / clock | string or null | Same live-progress envelope as player-props. Clock formats: [#event-score](#event-score). |
| period_odds[].scope | string | 1H (NFL/NCAAF/NBA/NCAAB — Q1+Q2, or NCAAB/soccer native 1H), F5 (MLB innings 1–5), or S1 (tennis first-set games). |
| period_odds[].market | string | first_half_spreads or first_half_totals. |
| period_odds[].line | number | Posted main for this scope. Spread point or total number. Half-points are typical. |
| period_odds[].home_score / away_score | number or null | Points (or runs) scored in this scope so far. Null until the first period row lands. |
| period_odds[].current | number or null | Totals: home_score + away_score. Spreads: the home-minus-away differential used to grade the home side. Null until both scores are present. |
| period_odds[].pct_of_line | number or null | Totals only: current / line × 100, one decimal. Can exceed 100. Null on spreads, or when current / line is null. |
| period_odds[].settleable | boolean | True when this market has a settlement rule. Grade only when scope_complete is also true. |
| period_odds[].scope_complete | boolean | True when every required period label is numeric for both sides and the following period has started (e.g. Q3 for 1H, inning 6 for F5) — or the event is final/walkover. Grade only then. |
| period_odds[].result | string or null | Totals only: in_progress / over / under / push. Null on spreads — those use the two result fields below. |
| period_odds[].home_result / away_result | string or null | Spreads only: won / lost / push once scope_complete. Null on totals and while the scope is still open. |
| period_odds[].books | object | Per-book American-odds integers. Spreads use home/away; totals use over/under. |

<!-- #event-period-odds -->

## Get bet intelligence for an event

`GET /v1/events/{id}/intelligence`

Returns the full bet intelligence payload for an event. This endpoint is not cached — it always returns the latest computed data. Always returns 200 when the event exists — check available to determine whether intelligence has been computed yet. Returns 404 only if the event ID does not exist.

- **Predictive bets[]** — vig-stripped probability / fair_price plus Price overlay. How to read: [/docs/understanding-odds](/docs/understanding-odds).

- **Main-line ev (Beta)** — the same sharp-fair gap packaged as ev_pct + Kelly on moneyline, spreads, and totals (tennis totals stay unpublished). Scan a sport: [GET /intelligence/ev](#intelligence-ev).

- **forecasts[]** — probability-based prediction, not a beat-the-market claim. Player-prop shrunken-rate Over/Under on MLB/NFL/NCAAF/NBA/NCAAB/NHL; tennis main-line — moneyline (ML_P1/ML_P2), game handicap (SPREAD_P1/SPREAD_P2), and total games (OVER/UNDER). Same objects as [GET /intelligence/forecasts](#intelligence-forecasts). How + fields: [/docs/forecasts](/docs/forecasts).

available gates bets[] only. forecasts[] can still populate when available is false (NBA / NCAAB / NHL, tennis main-line, or an MLB/NFL/NCAAF game that has not been priced yet). Do not drop the payload because available is false.

| Sport | Surface | Notes |
| --- | --- | --- |
| MLB | Predictive + forecasts | [bets[] fields](#intelligence-mlb-fields) · [forecasts[]](#intelligence-forecasts) |
| Tennis | Predictive + forecasts | [bets[] fields](#intelligence-mlb-fields) · [forecasts[]](#intelligence-forecasts) moneyline |
| Soccer | Predictive | MLS, EPL, La Liga, Serie A, Bundesliga, Ligue 1. [Fields](#intelligence-mlb-fields) |
| NFL | Predictive + forecasts | In season. [bets[]](#intelligence-mlb-fields) · [forecasts[]](#intelligence-forecasts) |
| NCAAF | Predictive + forecasts | In season. [bets[]](#intelligence-mlb-fields) · [forecasts[]](#intelligence-forecasts) |
| NBA, NCAAB, NHL | Forecasts | bets[] is empty and available is false; forecasts[] still scores player props. [Fields](#intelligence-forecasts) |
| Other | — | available: false (free when forecasts is also empty) |

- Two sibling arrays: bets[] is vig-stripped probability / fair_price plus Price overlay and main-line ev (Beta) — a gated beat-the-market claim. forecasts[] is an ungated probability-based prediction — player props plus tennis moneyline/spreads/totals, same objects as [GET /intelligence/forecasts](#intelligence-forecasts).

- Check available before reading bets[]. forecasts[] can populate when available is false (NBA / NCAAB / NHL, or an MLB/NFL/NCAAF game that has not been priced yet).

- has_recommend stays false until a model-backed edge is published.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Returns 404 if the event doesn't exist. If the event exists but predictive bets[] have not been computed yet, returns 200 with available: false and empty bets. forecasts[] can still populate on MLB / NFL / NCAAF / NBA / NCAAB / NHL. |

**Request**

```bash
curl https://lumify.ai/v1/events/4821/intelligence \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Top-level fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | false when predictive bets[] have not been computed yet. forecasts[] can still populate. Free only when available is false and forecasts is empty. |
| sport | string \| null | Sport slug for this event. |
| league | string \| null | League slug for this event, if any — e.g. mls, epl. |
| odds_source | string \| null | Bookmaker the bets[].market prices came from — the book the assessment was priced against, not a live overlay. Per-bet market.book is authoritative if the two ever differ. |
| players | object | Participant identification keyed by role — {role: {name, player_id, team_id}}, where role is player_1/player_2 or home/away. Cross-reference with participants[] in GET /v1/events/{id}. |
| has_recommend | boolean \| null | true if at least one bet meets the recommendation threshold; false if none do; null if the pipeline hasn't run yet. Stays false until a model-backed edge/tier is published. |
| intelligence_updated_at | string \| null | ISO-8601 UTC timestamp of the most recent change anywhere in this payload — the maximum of the per-bet computed_at values. Individual markets are only rewritten when they move, so use the per-bet computed_at when reasoning about one specific bet. |
| match_overview | string \| null | Event-level pre-game matchup preview. Written before kickoff (sport-shaped Search overlay). The request path only reads the stored row. Null until the pre-kickoff job has run. |
| rationale | string[] \| null | Event-level factual pre-game matchup chips (context overlay). Not a pick. |
| bets | array | One entry per scored bet token. MLB / tennis order: ML_P1 → ML_P2 → SPREAD_P1 → SPREAD_P2 → OVER → UNDER. Soccer order: ML_HOME → ML_AWAY → ML_DRAW → SPREAD_HOME → SPREAD_AWAY → OVER → UNDER. |
| forecasts | array | Forecasted wagers for this event — player-prop rows on MLB/NFL/NCAAF/NBA/NCAAB/NHL, tennis main-line: moneyline (ML_P1/ML_P2), game handicap (SPREAD_P1/SPREAD_P2), total games (OVER/UNDER). Same object as [GET /intelligence/forecasts](#intelligence-forecasts). selected marks the top-conviction rows on the daily slate. How + fields: [/docs/forecasts](/docs/forecasts). |
| matchup | object \| null | Not returned. Use GET /v1/events/{id}/stats for pitcher/lineup Data. |

### Predictive intelligence fields

The same keys for **MLB**, **soccer** (MLS + big-five), **tennis**, **NFL**, and **NCAAF**. Fair probability + Price overlay — framework plumbing is omitted. edge/tier are null and has_recommend is false until Edge clears. best.edge / edges_by_book are line-shopping price gaps vs sharp consensus; main-line ev (Beta) is the same gap packaged as ev_pct + Kelly. Example below is MLS; other live sports use the same keys with sport-specific tokens and fair books.

**Response**

```json
{
  "event_id":   11632,
  "available":  true,
  "sport":      "soccer",
  "league":     "mls",
  "odds_source": "pinnacle",
  "players": {
    "home": { "name": "D.C. United", "player_id": null, "team_id": 858 },
    "away": { "name": "Nashville SC", "player_id": null, "team_id": 843 }
  },
  "has_recommend": false,
  "match_overview":  null,
  "rationale":       null,
  "bets": [
    {
      "bet_type":      "ML_HOME",
      "player_role":   "home",
      "team_id":       858,
      "player_name":   "D.C. United",
      "probability":   0.31903,
      "interval":     [0.2631, 0.37496],
      "fair_price":   213,
      "market": { "price": 199, "line": null, "book": "pinnacle" },
      "edge":         null,
      "tier":         null,
      "fair": {
        "probability": 0.31903,
        "books": ["pinnacle"],
        "n_books": 1,
        "is_consensus": false
      },
      "edges_by_book": { "fanduel": 0.031, "hardrock": -0.012 },
      "best": { "book": "fanduel", "price": 220, "edge": 0.031, "quote_age_seconds": 180.0 },
      "ev": { "beta": true, "book": "fanduel", "price": 220, "ev_pct": 3.1, "kelly_fraction": 0.0141, "quote_age_seconds": 180.0, "n_books": 1 },
      "computed_at":  "2026-07-27T10:07:20Z"
    }
  ]
}
```

| Returned | Omitted |
| --- | --- |
| probability, interval, fair_price, market, edge, tier, fair, edges_by_book, best, ev (Beta), computed_at, participant fields | p_model, p_market, blend_w, sufficiency, phase, model_version, drivers, alignment |

### Field reference

Same keys across every live intelligence sport. Framework plumbing listed as omitted above is never present in the JSON.

| Field | Type | Description |
| --- | --- | --- |
| bet_type | string | Token for this outcome. Enumerated by sport in [#intelligence-tokens](#intelligence-tokens). |
| player_role / player_name / player_id / team_id | string or integer or null | Participant this token is priced on. null on match-level tokens (soccer ML_DRAW, every sport's Over/Under). |
| probability | number or null | Published probability for this outcome, 0–1. Outcomes of a market are solved together and sum to 1. |
| fair_price | integer \| null | American-odds fair price implied by probability — the vig-free line. Comparing it to market.price gives the book's margin on this side. |
| edge | number \| null | Expected profit per 1 unit staked at market.price. null on Stage 1 until a model-backed edge is published — reserved for recommend gating. |
| interval | number[] \| null | [lo, hi] band around probability. Read it as how much evidence backs this number, not as a statistical confidence interval. A freshly-opened line gets a wider band than a heavily-traded one. |
| tier | string \| null | very_high, strong, moderate, or avoid. null whenever edge is null. |
| fair | object \| null | Sharp-consensus fair: {probability, books, n_books, is_consensus}. MLS/tennis: Pinnacle. MLB: Pinnacle+Circa when both quote. |
| edges_by_book | object \| null | Price gap vs fair.probability per soft book — a line-shopping metric. See ev for Beta display packaging on main-line tokens. |
| best | object \| null | Highest price-gap book: {book, price, edge, quote_age_seconds}. Same line-shopping metric as edges_by_book. See ev for Beta display packaging on main-line tokens. |
| ev | object \| null | Beta. {beta, book, price, ev_pct, kelly_fraction, quote_age_seconds, n_books} — the same sharp-fair price gap as best, re-expressed as an EV% and a full-Kelly stake (capped at 1). Main-line tokens (moneyline, spreads, totals). Tennis totals stay unpublished. A single sharp book (n=1 Pinnacle) is a valid fair. Gaps ≤ 0 or above 25% are dropped. When best is a suppressed MLB moneyline book, the next eligible book is used. Not a backtested +EV claim. Scan a sport with [GET /v1/intelligence/ev](#intelligence-ev). |
| market.book | string or null | Bookmaker this bet's price/line came from. The ?bookmaker= parameter is ignored. |
| market.price | integer or null | American-odds integer quoted by market.book. Walkthrough: [/docs/understanding-odds#fair-price](/docs/understanding-odds#fair-price). |
| market.line | number or null | Spread or total number this token is priced on (e.g. 8.5 on OVER/UNDER). null on moneyline. |
| best.quote_age_seconds | number or null | Age of best.book's posted price at publish, in seconds. Explained on [/docs/understanding-odds](/docs/understanding-odds). |
| computed_at | string \| null | ISO-8601 UTC time this bet's numbers last materially changed — not when they were last checked. |

> **Tip:** Reading a market-anchored event. probability and fair_price are a vig-stripped fair-price reference. Read fair / edges_by_book / best for cross-book line-shopping (Price overlay; Edge is unpublished). Main-line ev (Beta) packages a positive gap as ev_pct + Kelly. edge / tier / has_recommend stay null/false until Edge clears — code against them now and they will fill in without a response-shape change. For a worked numeric walkthrough of every field on this page, see [Understanding Odds & Probability](/docs/understanding-odds).

### Bet tokens by sport

| Sports | Tokens |
| --- | --- |
| MLB, tennis, NFL, NCAAF | ML_P1 (home / player_1), ML_P2 (away / player_2), SPREAD_P1, SPREAD_P2, OVER, UNDER |
| Soccer | ML_HOME, ML_AWAY, ML_DRAW, SPREAD_HOME, SPREAD_AWAY, OVER, UNDER. ML_DRAW is match-level — player_role / team_id are null, same as Over/Under. |

> **Tip:** List, then fetch. GET /v1/events with sport / league / status=scheduled, then GET /v1/events/{id}/intelligence.

- has_recommend stays false until edge is published. Use probability / fair_price and fair / edges_by_book / best for line-shopping. ev (Beta) badges the same gap on main-line tokens. Scan a sport with [GET /v1/intelligence/ev](#intelligence-ev) (market=h2h|spreads|totals; tennis totals return 400).

<!-- #event-intelligence -->

## List main-line EV (Beta)

`GET /v1/intelligence/ev`

**Beta.** Pregame main-line opportunities (moneyline, spreads, or totals) whose sharp-fair price gap is positive and at most 25% EV, for soccer, MLB, tennis, NFL, and NCAAF. Pass market=h2h (default), spreads, or totals. Tennis totals return 400 — Stage 1 intelligence is moneyline + spreads only. Same number as bets[].ev on [GET /intelligence](#event-intelligence). Always 200 when the market is offered; an empty list means nothing currently clears the gates. 1 credit.

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| sport | string | required | soccer, mlb, tennis, nfl, or ncaaf. |
| league | string | | Optional league slug. Soccer without a league scans every published soccer league (MLS + big-five). |
| market | string | | h2h (default, moneyline), spreads, or totals. Tennis + totals returns 400. |
| min_ev | number | | Minimum EV%. Default 0. Clamped to 0–25. |
| book | string | | Restrict to one sportsbook slug. |
| limit | integer | | Max rows (1–200). Default 50. |

```json
{
  "sport": "soccer",
  "league": "mls",
  "market": "h2h",
  "min_ev": 0,
  "max_ev": 25,
  "book": null,
  "beta": true,
  "opportunities": [{
    "event_id": 84213,
    "side": "home",
    "team": "LA Galaxy",
    "bet_type": "ML_HOME",
    "fair_probability": 0.4123,
    "ev": { "beta": true, "book": "fanduel", "price": 155, "ev_pct": 3.1, "kelly_fraction": 0.02, "n_books": 1 }
  }],
  "total": 1
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| sport | string | Sport slug this scan was run for. |
| league | string or null | League filter, or null when the scan covered the whole sport. |
| market | string | h2h, spreads, or totals — the family scanned. |
| min_ev / max_ev | number | EV% gates applied to this response. Default 0–25. Gaps ≤ 0 or above 25% are dropped. |
| book | string or null | Book filter, or null when every eligible book was considered. |
| beta | boolean | Always true — this surface is an unverified market-consensus estimate. |
| opportunities[].event_id | integer | Lumify event ID. Fetch the full payload with [GET /intelligence](#event-intelligence). |
| opportunities[].side | string | home, away, p1, p2, draw, over, or under. |
| opportunities[].team | string or null | Display name of the side; Draw / Over / Under for those tokens. |
| opportunities[].bet_type | string | Main-line token for the scanned family (e.g. ML_HOME, SPREAD_P1, OVER). |
| opportunities[].line | number or null | Posted line for spreads and totals. Null on moneyline. |
| opportunities[].fair_probability | number | Sharp-fair probability (0–1) the gap is measured against. A single sharp book (n=1 Pinnacle) is a valid fair. |
| opportunities[].ev.ev_pct | number | Price gap vs sharp-fair, in percent points (0–25 after the gate). Same number as bets[].ev.ev_pct. |
| opportunities[].ev.kelly_fraction | number | Full-Kelly stake from that gap, capped at 1.0. Not a recommended bet size. |
| opportunities[].ev.n_books | integer | Sharp books used to build the fair. n=1 Pinnacle is valid. |
| opportunities[].ev.quote_age_seconds | number or null | Age of the quoted book's posted price at publish, in seconds. Present on bets[].ev; may be omitted on this list. |
| total | integer | Count of opportunities on this page. Empty list is still 200, still 1 credit. |

<!-- #intelligence-ev -->

## List forecasted wagers

`GET /v1/intelligence/forecasts`

Daily board of forecasted wagers from Lumify's model — a probability-based prediction, not a beat-the-market claim (no OOS/independence gate; see [GET /intelligence/ev](#intelligence-ev) for the gated main-line +EV claim). Player-prop wagers from the shrunken rate model — MLB, NCAAF, NFL, NBA, NCAAB, and NHL. Tennis main-line: moneyline from ranking Bradley-Terry (bet_type ML_P1/ML_P2), game handicap (SPREAD_P1/SPREAD_P2), and total games (OVER/UNDER) from a Normal-approx games model. Ranked by conviction. Always 200; an empty list means nothing is on today's slate. 1 credit. The same objects also appear per-event on [GET /intelligence](#event-intelligence) as forecasts[]. How the model works, field catalog, and the forecastable-vs-settleable subset: [/docs/forecasts](/docs/forecasts).

### Query parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| sport | string | required | Player props: mlb, ncaaf, nfl, nba, ncaab, nhl. Main-line: tennis (moneyline, spreads, and totals). |
| date | string | | UTC slate date YYYY-MM-DD. Defaults to today UTC. |
| market | string | | h2h, spreads, or totals — filters a sport's main-line forecast rows. Ignored on prop-only sports. |
| limit | integer | | Max wagers (1–100). Default 25. |

**Response**

```json
{
  "sport": "mlb",
  "date": "2026-08-27",
  "model_version": "forecast-v0",
  "reliability": "emerging",
  "wagers": [{
    "event_id": 18258,
    "sport": "mlb",
    "league": "mlb",
    "player": "Ben Rortvedt",
    "player_id": 5128,
    "bet_type": null,
    "player_role": null,
    "market": "runs",
    "line": 0.5,
    "side": "under",
    "p_hit": 0.7617,
    "interval": [0.6982, 0.8252],
    "sufficiency": 0.4545,
    "reliability": "emerging",
    "conviction": 0.2379,
    "model_version": "forecast-v0",
    "selected": true,
    "books": { "draftkings": -453 },
    "drivers": [{
      "id": "player.l10_rate",
      "input": 0.27,
      "effect": 0.082,
      "direction": "up"
    }],
    "research": null
  }],
  "total": 1
}
```

> **Tip:** How + fields live off this page. Model (shrink L10 → Poisson → side), drop rules, conviction formula, selected vs the full event catalog, and every wager field: [/docs/forecasts](/docs/forecasts). Worked numeric read of one wager: [/docs/understanding-odds#forecasts](/docs/understanding-odds#forecasts). Settleable inventory (including combos the model does not pick): [/docs/player-props](/docs/player-props).

<!-- #intelligence-forecasts -->

## Get betting splits for an event

`GET /v1/events/{id}/splits`

Returns public betting split data for an event — the percentage of bets and handle wagered on each side across moneyline, spread, and total markets. Includes a consensus (average across books) and a per-bookmaker breakdown. Updated every ~10 minutes. Always returns 200 when the event exists — check available to determine whether splits have been ingested yet. Returns 404 only if the event ID does not exist.

> **Note:** Sports coverage: Available for MLB, NBA, NHL, NFL, NCAAF, and NCAAB (during their respective seasons; NCAAB is often empty off-season). Tennis and soccer splits are not available (upstream 400). Soccer odds are available via [/v1/events/{id}/odds](#event-odds). Splits are only ingested for pre-game events; data is not updated once a game starts.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

**Request**

```bash
curl https://lumify.ai/v1/events/479/splits \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id":    479,
  "available":   true,
  "captured_at": "2026-05-17T14:15:12Z",
  "consensus": {
    "moneyline": {
      "home":  { "bets_pct": 92, "handle_pct": 96, "price": -149 },
      "away":  { "bets_pct": 8,  "handle_pct": 4,  "price": 123  }
    },
    "spread": {
      "home":  { "bets_pct": 87, "handle_pct": 98, "line": -1.5 },
      "away":  { "bets_pct": 13, "handle_pct": 2,  "line": 1.5  }
    },
    "total": {
      "over":  { "bets_pct": 78, "handle_pct": 81, "line": 7.0 },
      "under": { "bets_pct": 22, "handle_pct": 19, "line": 7.0 }
    }
  },
  "bookmakers": [
    {
      "bookmaker": "draftkings",
      "name": "DraftKings",
      "moneyline": {
        "home":  { "bets_pct": 83, "handle_pct": 93, "price": -149 },
        "away":  { "bets_pct": 17, "handle_pct": 7,  "price": 123  }
      },
      "spread": {
        "home":  { "bets_pct": 74, "handle_pct": 95, "line": -1.5 },
        "away":  { "bets_pct": 26, "handle_pct": 5,  "line": 1.5  }
      },
      "total": {
        "over":  { "bets_pct": 56, "handle_pct": 62, "line": 7.0 },
        "under": { "bets_pct": 44, "handle_pct": 38, "line": 7.0 }
      }
    }
  ]
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | false when no splits have been ingested yet. consensus will be an empty object and bookmakers an empty array. |
| captured_at | string \| null | UTC timestamp of the most recent ingest cycle for this event's splits data. null when available is false. |
| consensus | object | Market averages across all available bookmakers. Contains moneyline, spread, and total objects. |
| consensus[market][side].bets_pct | integer | Percentage of total bets placed on this side (0–100). Opposite sides sum to ~100. |
| consensus[market][side].handle_pct | integer | Percentage of total money wagered on this side (0–100). A large gap between handle_pct and bets_pct indicates sharp (large-bet) money diverging from public action. |
| consensus[market][side].price | integer \| null | American odds for this side. Present on moneyline; null on spread/total sides. |
| consensus[market][side].line | number \| null | Spread or total line. Present on spread/total; null on moneyline. |
| bookmakers | array | Per-bookmaker breakdown. Same market nesting as consensus. bookmaker is the odds slug (e.g. draftkings) — same namespace as /odds; name is the display name. |

> **Tip:** Sharp-money signal: When handle_pct significantly exceeds bets_pct on a side (typically ≥20pp gap), it indicates that a small number of large bets — characteristic of sharp bettors — are backing that side against the public. Use this in combination with /v1/events/{id}/intelligence for context on line movement.

<!-- #event-splits -->

### Teams
 Team profiles with league, conference, division, and home venue — first-class so agents do not need to derive teams from event participants.

 [MCP: list_teams, get_team →](/docs/guides#mcp)

## List teams

`GET /v1/teams`

Returns a paginated list of teams. Filter by sport, league, conference, division, country, name search, and active status. Results are sorted by ascending team ID.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| sport | string | optional | — | Sport slug, e.g. nba, nhl, nfl. |
| league | string | optional | — | League slug, e.g. nba. |
| conference | string | optional | — | Conference filter, e.g. Eastern. |
| division | string | optional | — | Division filter, e.g. Atlantic. |
| country | string | optional | — | ISO country code, e.g. USA. |
| q | string | optional | — | Partial team-name search. |
| active | boolean | optional | — | Filter by active status. Omit to return both active and inactive teams. |
| after_id | integer | optional | — | Pagination cursor from next_after_id. |
| limit | integer | optional | 25 | Page size, range 1–100. |

**Request**

```bash
# Eastern Conference NBA teams
curl "https://lumify.ai/v1/teams?sport=nba&conference=Eastern" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "data": [
    {
      "id":            1,
      "slug":          "boston-celtics",
      "name":          "Boston Celtics",
      "abbreviation":  "BOS",
      "image_url":     "https://lumify.ai/media/teams/nba/1.png",
      "sport":         "nba",
      "league":        "nba",
      "conference":    "Eastern",
      "division":      "Atlantic",
      "venue":         { "id": 1, "name": "TD Garden", "city": "Boston" },
      "is_active":     true
    }
  ],
  "has_more":       false,
  "next_after_id":  null
}
```

<!-- #teams -->

## Get a team

`GET /v1/teams/{id}`

Returns a single team's profile, including home venue when linked. Returns 404 if the team does not exist.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify team ID. |

**Request**

```bash
curl "https://lumify.ai/v1/teams/1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "id":            1,
  "slug":          "boston-celtics",
  "name":          "Boston Celtics",
  "short_name":    "Celtics",
  "abbreviation":  "BOS",
  "image_url":     "https://lumify.ai/media/teams/nba/1.png",
  "sport":         "nba",
  "league":        "nba",
  "city":          "Boston",
  "state":         "MA",
  "country_code":  "USA",
  "conference":    "Eastern",
  "division":      "Atlantic",
  "venue":         { "id": 1, "name": "TD Garden", "city": "Boston" },
  "is_active":     true
}
```

<!-- #team-detail -->

### Players
 Shared player identity across every sport. Null means unknown, not wrong sport. Tennis standings nest under rankings.

 [MCP: search_players, get_player, get_player_events →](/docs/guides#mcp)

## List players

`GET /v1/players`

Returns a paginated list of players. Same identity object on every sport — null means unknown, not wrong sport. Tennis standings nest under rankings.{singles, points}; rankings is null on every other sport. Supports filtering by sport, country, name search, active status, and ranking. Results are sorted by ascending player ID.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| sport | string | optional | — | Filter by sport slug: tennis, mlb, nfl, etc. |
| q | string | optional | — | Partial name search. Case-insensitive match against full_name (e.g. ?q=sinner). |
| country | string | optional | — | ISO 3166-1 alpha-3 country code (e.g. USA, ITA, GBR). Case-insensitive. |
| active | boolean | optional | — | Pass true for active players only, false for retired. |
| ranked | boolean | optional | — | If true, returns only tennis players with an ATP/WTA singles ranking (rankings.singles). |
| after_id | integer | optional | — | Pagination cursor. Pass next_after_id from the previous response. |
| limit | integer | optional | 25 | Page size. Range: 1–100. |

**Request**

```bash
# Top-ranked tennis players
curl "https://lumify.ai/v1/players?sport=tennis&ranked=true&limit=10" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Search by name
curl "https://lumify.ai/v1/players?q=sinner" \
  -H "Authorization: Bearer YOUR_API_KEY"

# All active MLB players
curl "https://lumify.ai/v1/players?sport=mlb&active=true&limit=100" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "data": [
    {
      "id":                    1,
      "slug":                  "jannik-sinner",
      "full_name":             "Jannik Sinner",
      "first_name":            "Jannik",
      "last_name":             "Sinner",
      "sport":                 "tennis",
      "country_code":          "ITA",
      "birthdate":             null,
      "position":              null,           // e.g. "P", "SS", "CF" for MLB
      "handedness":            null,           // left | right | switch (tennis)
      "height_cm":             null,
      "weight_kg":             null,
      "rankings":              { "singles": 1, "points": 14350 },
      "current_team_id":       null,
      "current_team_name":     null,
      "is_active":             true,
      "retired_at":            null,
      "image_url":             null           // lumify.ai/media/players/tennis/{hash}.png when available
    }
  ],
  "has_more":       true,
  "next_after_id":  25            // null on the last page
}
```

<!-- #players -->

## Get a player

`GET /v1/players/{id}`

Returns a single player's full profile. Returns 404 if the player does not exist.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify player ID. |

**Request**

```bash
curl "https://lumify.ai/v1/players/1" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "id":                    1,
  "slug":                  "jannik-sinner",
  "full_name":             "Jannik Sinner",
  "first_name":            "Jannik",
  "last_name":             "Sinner",
  "sport":                 "tennis",
  "country_code":          "ITA",
  "birthdate":             null,
  "position":              null,
  "handedness":            null,
  "height_cm":             null,
  "weight_kg":             null,
  "rankings":              { "singles": 1, "points": 14350 },
  "current_team_id":       null,
  "current_team_name":     null,
  "is_active":             true,
  "retired_at":            null,
  "image_url":             null           // lumify.ai/media/players/tennis/{hash}.png when available
}
```

<!-- #player-detail -->

## List a player's events

`GET /v1/players/{id}/events`

Returns events a player has participated in or is scheduled to play. Defaults to a ±30-day window around today. Results are sorted by starts_at DESC (most recent first).

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify player ID. |

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| status | string | optional | — | Filter by event status: scheduled, inprogress, final, etc. |
| from | string | optional | today −30d | Start date (UTC, inclusive). Format: YYYY-MM-DD. |
| to | string | optional | today +30d | End date (UTC, inclusive). Max range: 90 days. |
| after_id | integer | optional | — | Pagination cursor. |
| limit | integer | optional | 25 | Page size. Range: 1–100. |

**Request**

```bash
# Sinner's upcoming matches
curl "https://lumify.ai/v1/players/1/events?status=scheduled" \
  -H "Authorization: Bearer YOUR_API_KEY"

# Recent results (last 30 days)
curl "https://lumify.ai/v1/players/1/events?status=final" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "player_id": 1,
  "data": [
    {
      "event_id":    1100,
      "starts_at":   "2026-05-17T15:00:00Z",
      "status":      "scheduled",
      "sport":       "tennis",
      "competition": "ATP Rome",
      "venue":       null,
      "venue_city":  null,
      "role":        "player_1",    // player_1 | player_2 | home | away | single
      "result":      null,           // "win" | "loss" | null (pre-game)
      "score":       null,
      "opponent": {
        "player_id": 1012,
        "name":      "Casper Ruud"
      }
    }
  ],
  "has_more":      false,
  "next_after_id": null
}
```

<!-- #player-events -->

### Odds & Lines
 Current moneyline, spread, and total lines per bookmaker, plus line movement history.

 [MCP: get_odds, get_odds_history →](/docs/guides#mcp)
 [Guide: Track live odds movement →](/docs/guides#recipe-odds-movement)

## Get current odds for an event

`GET /v1/events/{id}/odds`

Returns the current moneyline, spread, and total lines for an event — pregame and in-play. Defaults to **Pinnacle**. Use bookmaker=all or a comma-separated list to fetch multiple books — still **1 credit**. Data is updated every ~10 minutes and cached for 2 minutes. While the event is in progress, books that have not quoted since kickoff are omitted. Final events grade result / close from the pre-kickoff snapshot, not the last in-play line. Always returns 200 when the event exists — check available to determine whether odds have been ingested yet. Returns 404 only if the event ID does not exist.

> **Note:** Soccer: Moneyline (h2h) is a 3-way market — outcomes include both team names plus Draw. Asian handicap spreads use goal lines (e.g. -0.5, +0.5).

> **Note:** Default-book fallback: Pinnacle usually posts preseason/early-week lines within ~24-72h of kickoff, so the first and last games of a slate can go final (or still be too far out) before Pinnacle ever prices them, even though other books already have full odds. When bookmaker is omitted and Pinnacle has no line yet, this endpoint falls back to the best-covered other book instead of returning available: false, adding requested_bookmaker: "pinnacle" and fallback_bookmaker to the response. Passing bookmaker=pinnacle explicitly never falls back.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

### Query parameters

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| bookmaker | string | pinnacle | Bookmaker filter. Accepted values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, westgate, wynn, south_point, stations, hardrock, betonline, betr, betrivers, lowvig, all, or a comma-separated combination (e.g. fanduel,betmgm). 1 credit for one bookmaker or all. |
| include_alts | boolean | false | Include alternate spread/total rungs (is_main=false). Default is mains only. |

**Request — Pinnacle only (default, 1 credit)**

```bash
curl https://lumify.ai/v1/events/4821/odds \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Request — all bookmakers (1 credit)**

```bash
curl "https://lumify.ai/v1/events/4821/odds?bookmaker=all" \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Response**

```json
{
  "event_id": 4821,
  "bookmakers": [
    {
      "bookmaker": "pinnacle",
      "markets": [
        {
          "key": "h2h",
          "label": "moneyline",
          "outcomes": [
            { "outcome": "Jannik Sinner",  "price": -280, "point": null },
            { "outcome": "Carlos Alcaraz", "price": 230,  "point": null }
          ]
        },
        {
          "key": "spreads",
          "label": "spread",
          "outcomes": [
            { "outcome": "Jannik Sinner",  "price": -110, "point": -2.5 },
            { "outcome": "Carlos Alcaraz", "price": -110, "point": 2.5  }
          ]
        },
        {
          "key": "totals",
          "label": "totals",
          "outcomes": [
            { "outcome": "Over",  "price": -110, "point": 22.5 },
            { "outcome": "Under", "price": -110, "point": 22.5 }
          ]
        }
      ],
      "captured_at": "2026-05-13T18:32:00Z"
    }
  ],
  "last_updated": "2026-05-13T18:32:00Z"
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | false when no odds have been ingested yet. bookmakers will be an empty array. |
| bookmakers | array | One entry per bookmaker with odds data. |
| bookmaker | string | Bookmaker key, e.g. pinnacle, draftkings, betmgm. Supported odds books: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, westgate, wynn, south_point, stations, hardrock, betonline, betr, betrivers, lowvig. Availability per event depends on what has been ingested. |
| markets | array | Markets for this bookmaker, ordered: moneyline → spread → totals. |
| key | string | Market key: h2h, spreads, or totals. |
| label | string | Human-readable label: moneyline, spread, or totals. |
| outcomes[].outcome | string | Side name — team/player, Over, Under, or soccer Draw. Soccer h2h is 3-way (home, away, Draw). |
| outcomes[].price | integer | American-odds integer. |
| outcomes[].point | number or null | Spread or total number. null on moneyline. |
| outcomes[].is_main | boolean | true on the book's main line. Alternates ship only when include_alts=true. |
| outcomes[].result | string | Final events only: won / lost / push / void, graded from the stored score against the pre-kickoff close — not the last in-play price. Omitted while the event is not final. |
| outcomes[].close | number or null | Final events only, on spread/total: the pre-kickoff closing point. Omitted on moneyline and while the event is live. |
| outcomes[].fair_price / consensus | integer or object or null | MLB, tennis, and soccer (MLS + big-five) mains only — mirrored from published assessments. Absent on other sports. |
| requested_bookmaker / fallback_bookmaker | string | Present only when the default-book fallback fired (Pinnacle requested, another book returned). Passing bookmaker=pinnacle explicitly never falls back. |
| captured_at | string | ISO-8601 UTC timestamp when this bookmaker's odds were last ingested. |
| last_updated | string | Most recent captured_at across all bookmakers. |

<!-- #event-odds -->

## Get odds movement history

`GET /v1/events/{id}/odds/history`

Returns all recorded line movements for an event — any time a price or point changed between ingest cycles. Defaults to **Pinnacle**. Use bookmaker=all or a comma-separated list for multiple books — still **1 credit**. Ordered newest-first. Useful for detecting sharp line movement. Not cached. Returns 404 if no movement has been recorded.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

### Query parameters

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| bookmaker | string | pinnacle | Bookmaker filter. Accepted values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, westgate, wynn, south_point, stations, hardrock, betonline, betr, betrivers, lowvig, all, or a comma-separated combination. 1 credit for one bookmaker or all. |
| limit | integer | 50 | Max movements to return (1–200). |

**Response**

```json
{
  "event_id": 4821,
  "movements": [
    {
      "bookmaker":  "pinnacle",
      "market":     "moneyline",
      "market_key": "h2h",
      "outcome":    "Jannik Sinner",
      "price_from": -250,
      "price_to":   -280,
      "point_from": null,
      "point_to":   null,
      "moved_at":   "2026-05-13T15:02:00Z"
    }
  ],
  "total": 1
}
```

### Response fields

| Field | Type | Description |
| --- | --- | --- |
| event_id | integer | Lumify event ID. |
| movements[].bookmaker | string | Book slug this tick belongs to. Same namespace as /odds. |
| movements[].market | string | Human label: moneyline, spread, or totals. |
| movements[].market_key | string | Persisted key: h2h, spreads, or totals. Use this for joins; market is the display label. |
| movements[].outcome | string | Side that moved — team/player name, Over, Under, or soccer Draw. |
| movements[].price_from / price_to | integer | American-odds integers before and after this tick. |
| movements[].point_from / point_to | number or null | Spread or total number before and after this tick. Both null on moneyline. |
| movements[].moved_at | string | ISO-8601 UTC timestamp of this ingest cycle. Newest first. |
| total | integer | Count of movements on this page. HTTP 404 if no movement has been recorded for the requested books — not an empty list. |

<!-- #event-odds-history -->

### Push & Streaming
 Server-Sent Events and webhook subscriptions — remove the need to poll for live score changes.

 [Guide: Track live odds movement →](/docs/guides#recipe-odds-movement)

## Stream live score updates (SSE)

`GET /v1/events/{id}/stream`

Opens a text/event-stream connection that emits an event: score message only when the score, status, or clock changes — plus a keep-alive comment every 15 seconds. The stream closes when the event finishes (event: done) or after 5 minutes, whichever comes first. Use this instead of polling [/v1/events/{id}/score](#event-score) when you want push-based updates.

> **Note:** Auth for EventSource clients. Browser EventSource cannot set custom headers, so this endpoint also accepts the key as ?api_key=lmfy-... in addition to the standard Authorization: Bearer header.

> **Tip:** Reconnecting across the 5-minute cap. If the connection closes because the max duration elapsed (not because the game finished), the server sends event: reconnect first so you can tell the two apart — open a fresh connection to the same URL to keep watching. Both SDKs' stream helpers (streamScores() in TypeScript, client.events.stream() in Python) already do this automatically, so a long game looks like one continuous stream — no reconnect logic to write yourself.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Returns an event: error message if the event does not exist. |

**Request**

```bash
curl -N "https://lumify.ai/v1/events/4812/stream" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```text
event: score
data: {"event_id": 4812, "status": "inprogress", "period": "3", "clock": "8:42", "scores": [...] , "updated_at": "2026-05-10T01:18:44Z"}

: keep-alive

event: done
data: {"event_id": 4812}

// or, if the 5-minute cap is hit before the game finishes:
event: reconnect
data: {"event_id": 4812, "reason": "max_stream_duration", "max_seconds": 300}
```

> **Warning:** Concurrency limit. Each API key may hold a limited number of concurrent streams. Exceeding it returns 429 with error.code: "stream_limit_exceeded" — close an existing stream and retry.

<!-- #event-stream -->

## Manage webhook subscriptions

Webhooks push score changes, status transitions, and line moves to your own endpoint — no polling or open connections required. Delivery is performed by the ingest pipeline; each payload is signed with the subscription's signing_secret (HMAC-SHA256) so you can verify authenticity. Deliveries that fail transiently (5xx, 429, or a timeout) are automatically retried with exponential backoff (30s / 5m / 30m / 2h / 6h) — see [delivery history](#webhook-deliveries) below.

**Billing.** Creating, listing, and deleting subscriptions is 1 credit per call, same as any other request. Deliveries fire at a small fraction of a credit each (varies by event type — high-frequency types like score cost less per delivery than low-frequency, high-signal types), drawn from your balance as they accrue, so a quiet subscription can run for a long time on a small balance.

**line_move deliveries.** One signed POST per event per ingest cycle (~10 min), not one per book/market/outcome. The body is data.moves (the material main-line changes that cycle). A move is pushed only for main lines on live or imminent games (starting within ~48 hours), and only when the point changed or the American price moved by at least 5¢. Alternate rungs and 1–4¢ juice ticks are not delivered.

### Create a subscription

`POST /v1/webhooks`

| Field | Type | | Description |
| --- | --- | --- | --- |
| url | string | required | HTTPS endpoint to receive deliveries. Rejected if it resolves to a private/internal address. |
| event_types | string[] | optional | One or more of score, status, line_move, intelligence. Defaults to ["score", "status"]. Including line_move requires sport or event_id (platform-wide line_move is rejected). |
| sport | string | optional | Restrict to one sport slug. Required (or event_id) when event_types includes line_move. |
| event_id | integer | optional | Restrict to a single event. Required (or sport) when event_types includes line_move. |

```bash
curl -X POST https://lumify.ai/v1/webhooks \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/hooks/lumify", "event_types": ["score", "line_move"], "sport": "mlb"}'
```

```json
{
  "id": 42,
  "url": "https://example.com/hooks/lumify",
  "event_types": ["score", "line_move"],
  "sport": "mlb",
  "event_id": null,
  "signing_secret": "whsec_...",  // shown once — store it to verify delivery signatures
  "is_active": true
}
```

### List & delete subscriptions

| Method & path | Description |
| --- | --- |
| GET /v1/webhooks | List the caller's webhook subscriptions. |
| DELETE /v1/webhooks/{id} | Delete a subscription. Returns 404 if it does not belong to the caller. |

```bash
# List
curl https://lumify.ai/v1/webhooks -H "Authorization: Bearer YOUR_API_KEY"

# Delete
curl -X DELETE https://lumify.ai/v1/webhooks/42 -H "Authorization: Bearer YOUR_API_KEY"
```

### Delivery history & retries

Every delivery attempt — including retries — is recorded and queryable per subscription, newest first. A failed attempt whose failure looks transient (5xx, 429, or a connection timeout) gets automatically retried with exponential backoff (30s → 5m → 30m → 2h → 6h, 5 retries max); other 4xx failures are not retried since the receiver is rejecting the request itself. Retries appear as their own rows linked to the attempt they retried via `parent_delivery_id`, so you can reconstruct the full chain for any event.

`GET /v1/webhooks/{id}/deliveries`

| Param | Type | | Description |
| --- | --- | --- | --- |
| after_id | integer | optional | Cursor: return deliveries with id < after_id (list is newest-first). |
| limit | integer | optional | Page size, default 25, max 100. |
| success | boolean | optional | Filter to successful (true, 2xx) or failed (false) deliveries. |
| given_up | boolean | optional | Filter to deliveries that exhausted retries (true) or still have / had a retry path (false). |
| event_type | string | optional | Filter by event type: score, status, line_move, or intelligence. |

```bash
curl https://lumify.ai/v1/webhooks/42/deliveries -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "data": [
    {
      "id": 1002,
      "event_type": "score",
      "event_id": 555,
      "attempt": 2,
      "parent_delivery_id": 1001,  // the attempt this one retried
      "status_code": 200,
      "success": true,
      "error": null,
      "given_up": false,
      "next_retry_at": null,
      "delivered_at": "2026-07-23T18:05:30Z"
    },
    {
      "id": 1001,
      "event_type": "score",
      "event_id": 555,
      "attempt": 1,
      "parent_delivery_id": null,
      "status_code": 503,
      "success": false,
      "error": null,
      "given_up": false,
      "next_retry_at": null,  // cleared once the retry above ran
      "delivered_at": "2026-07-23T18:05:00Z"
    }
  ],
  "next_after_id": null
}
```

<!-- #webhooks -->

### Agent Onboarding
 Programmatic key and credit management under /api/agent — provision access without the browser dashboard.

 [Guide: Provision API access programmatically →](/docs/guides#recipe-agent-onboarding)
 [agent.json →](/.well-known/agent.json)

## Manage API keys

Lets a builder or agent provision and manage keys without the dashboard. Authenticate with a browser session **or** an existing Lumify API key — so an agent that already has one key can mint, list, and revoke others on its own.

| Method & path | Description |
| --- | --- |
| POST /api/agent/keys | Create a new API key. The secret value is returned only once. |
| GET /api/agent/keys | List the caller's API keys (metadata only — secrets are never re-shown). |
| DELETE /api/agent/keys/{id} | Revoke an API key. Returns 404 if it doesn't belong to the caller. |

**Request — create a key**

```bash
curl -X POST https://lumify.ai/api/agent/keys \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "prod-worker-1", "scopes": ["all"]}'
```

```json
{
  "id": 17,
  "name": "prod-worker-1",
  "key": "lmfy-abc123.def456...",  // shown once — store it now
  "scopes": ["all"],
  "created_at": "2026-06-01T12:00:00Z"
}
```

> **Warning:** Key limits are tier-based. Creating past your plan's max_api_keys returns 403 with error.code: "key_limit_reached" and an upgrade_url.

<!-- #agent-keys -->

## Credits & credit packs

Check balance and buy additional credits programmatically — the same prepaid rails as the dashboard, over the existing Stripe integration, with no crypto or new payment flow required.

| Method & path | Description |
| --- | --- |
| GET /api/agent/credits | Current tier, credits used, credit limit, bonus credits, and billing period. |
| GET /api/agent/credit-packs | List purchasable one-time credit packs. |
| POST /api/agent/credits/topup | Purchase a credit pack by pack_id — charged off-session to the account's Stripe payment method on file. |

**Request — check balance**

```bash
curl https://lumify.ai/api/agent/credits \
  -H "Authorization: Bearer YOUR_API_KEY"
```

```json
{
  "tier": "growth",
  "credits_used": 4210,
  "credit_limit": 10000,
  "bonus_credits": 0,
  "total_remaining": 5790,
  "is_trial": false,
  "is_trial_expired": false
}
```

### Purchase a credit pack

```bash
curl -X POST https://lumify.ai/api/agent/credits/topup \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": 3}'
```

> **Warning:** Payment failures return 402 for card/payment issues (card_declined, payment_method_required) or 400 for an invalid pack_id.

<!-- #agent-credits -->

### Planning
 Pre-call credit-cost estimates — plan spend before you spend it.

 [MCP: estimate_cost →](/docs/guides#mcp)

## Estimate call cost

`POST /v1/estimate`

Returns a credit-cost range for one or more planned calls **without making them** — for agents that want to budget before spending. Costs are data-dependent (e.g. odds/intelligence/splits not yet ingested are free), so each result is a min_credits/max_credits range, not a single number, computed by the exact same pricing rules the real endpoints use. This call itself is always free.

See GET /v1/estimate/tools for the full list of supported tool names, grouped by how their cost varies.

### Request body

| Field | Type | | Description |
| --- | --- | --- | --- |
| calls | object[] | required | 1 or more {"tool": "...", "arguments": {...}} entries — the same tool name and arguments you'd pass to the matching MCP tool or SDK method. |

**Request**

```bash
curl -X POST https://lumify.ai/v1/estimate \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"calls":[{"tool":"get_event","arguments":{"event_id":12345,"include_odds":true}}]}'
```

**Response**

```json
{
  "estimates": [
    { "tool": "get_event", "min_credits": 1, "max_credits": 2, "note": "Base lookup is always 1 credit; each include_* add-on only bills (+1) if that data is actually available for the event." }
  ],
  "total_min_credits": 1,
  "total_max_credits": 2
}
```

> **Tip:** Always free. /v1/estimate (and GET /v1/estimate/tools) report X-Credits-Used: 0 — estimating never costs a credit, even in a loop while an agent explores options.

<!-- #estimate -->

## Error Codes

All machine-facing errors (/v1/*, /mcp, /api/agent/*) use one JSON envelope. Switch on error.code. The top-level detail field mirrors error.message for backward compatibility.

| Status | error.code | When it occurs |
| --- | --- | --- |
| 400 | bad_request | Invalid parameter — unknown status value, bad date format, date+from conflict, or date range > 90 days. |
| 401 | unauthorized | Missing, malformed, invalid, inactive, or expired API key. Credit exhaustion is not a 401 — see 402. |
| 402 | insufficient_credits / daily_credit_cap_exceeded | Valid key, but credits block access. Envelope includes upgrade_url and often topup_url. The free-tier daily cap is a rolling 24-hour window; daily_credit_cap_exceeded includes resets_at and window_hours. |
| 403 | forbidden / sport_scope_denied | Valid key denied for this resource (e.g. sport not in key scopes). Structured extras may include sport, granted_scopes, and upgrade_url. |
| 404 | not_found | The requested resource does not exist (e.g. unknown event ID). Sub-resources such as /odds, /splits, and /intelligence return 200 with available: false when data hasn't been ingested yet — 404 on those paths means the parent event ID is invalid. |
| 422 | validation_error | Type validation failed — non-integer id, or limit outside 1–100. Field errors are listed under error.errors. |
| 429 | rate_limit_exceeded | Rate limit exceeded. See error.retry_after and the Retry-After header. |
| 500 | internal_error | Unexpected error. Retry with exponential backoff. |

### Error response shape

```json
{
  "error": {
    "code":     "bad_request",
    "message":  "Invalid status 'live'. Valid values: ['cancelled', 'delayed', 'final', ...]",
    "status":   400,
    "doc_url":  "https://lumify.ai/docs/reference#error-codes"
  },
  "detail": "Invalid status 'live'. Valid values: ['cancelled', 'delayed', 'final', ...]"
}
```

<!-- #error-codes -->

## Event Status Values

The status field describes the lifecycle state of an event. Passing an unrecognised value to the ?status filter returns 400.

| Value | Phase | Description |
| --- | --- | --- |
| scheduled | Pre-game | Confirmed and scheduled; not yet started |
| inprogress | Live | Currently being played |
| delayed | Pre-game hold | Start pushed back but game has not begun (e.g. weather delay before first pitch) |
| suspended | Mid-game halt | Play stopped after the game began (e.g. rain delay mid-inning) |
| postponed | Pre-game | Moved to a different date entirely |
| cancelled | Terminal | Will not be played |
| final | Terminal | Concluded. Check result_type for how it ended. |
| walkover | Terminal | Tennis — opponent withdrew before the match. Winner is set; no score recorded. |

### Result type values

Present on final events. Describes how the outcome was reached.

| Value | Sports | Description |
| --- | --- | --- |
| regulation | All | Decided in normal time |
| overtime | NHL, NBA, NFL, Soccer (AET) | Decided in extra time or OT period |
| shootout | NHL, Soccer (PEN) | Decided by penalty shootout |
| retired | Tennis | Opponent retired mid-match due to injury |
| walkover | Tennis | Opponent withdrew before the match |

<!-- #status-values -->

## Sports Coverage

Yes means the public route accepts the sport — an empty off-season board is still Yes (available: false, not HTTP 400). Some means live with a league gate. No means the sport is not on that surface.

 Yes Shipped (slate may be empty off-season)
 Some League-gated (soccer MLS + big-five)
 No Not offered for this sport

| Surface | MLB | NFL | NCAAF | NBA | NCAAB | NHL | Soccer | Tennis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Event [Events](/docs/reference#events) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Stats [Stats](/docs/reference#event-stats) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Odds [Game odds](/docs/reference#event-odds) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Odds [Player props](/docs/player-props) | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| Odds [Period odds](/docs/reference#event-period-odds) | Yes | Yes | Yes | Yes | Yes | No | Yes | Yes |
| Odds [Team totals](/docs/reference#event-team-props) | Yes | Yes | Yes | No | No | No | Yes | No |
| Odds [Prediction markets](/docs/reference#event-prediction-markets) | Yes | Yes | Yes | Yes | No | Yes | Yes | Yes |
| Splits [Public splits](/docs/reference#event-splits) | Yes | Yes | Yes | Yes | Yes | Yes | No | No |
| Intelligence [Probability & Price](/docs/understanding-odds) | Yes | Yes | Yes | No | No | No | Some | Yes |
| Intelligence [Main-line EV](/docs/reference#intelligence-ev) | Yes | Yes | Yes | No | No | No | Some | Yes |
| Intelligence [Match context](/docs/understanding-odds#context-overlay) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Intelligence [Forecasts](/docs/forecasts) | Yes | Yes | Yes | Yes | Yes | Yes | No | Yes |

Notes and league slugs (NFL, NBA, MLB, NHL, NCAAF, NCAAB, ATP/WTA, soccer mls + big-five + ucl): [/docs/sports-coverage](/docs/sports-coverage). Tennis doubles and qualifying return available: false on /stats.

> **Note:** All timestamps are stored and returned in UTC. Use the venue timezone field to convert to local time for display.

<!-- #sports-coverage -->
