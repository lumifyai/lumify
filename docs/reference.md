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
| league | string | optional | — | Narrow to a specific league slug (e.g. atp, fifa_world_cup). More specific than sport. |
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

Use ?include_odds=true and/or ?include_intelligence=true to embed the current odds and bet intelligence directly in this response, saving extra round trips. Odds are scoped by bookmaker (default Pinnacle: +1 credit; all or a list: +2). Intelligence adds +1 when available. Use [/v1/events/{id}/score](#event-score) when you only need live score data.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Non-integer values return 422. Unknown IDs return 404. |

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| include_odds | boolean | optional | false | When true, embeds the current odds payload under an odds key — same shape as [GET /v1/events/{id}/odds](#event-odds), scoped by bookmaker (default: pinnacle). Adds +1 credit for a single book or +2 credits for all / a comma-separated list. |
| include_intelligence | boolean | optional | false | When true, embeds the bet intelligence payload under an intelligence key — same shape as [GET /v1/events/{id}/intelligence](#event-intelligence). Adds +1 credit (total 2 credits). |
| bookmaker | string | optional | system default | Bookmaker for inlined odds (when include_odds=true) and for intelligence.bets[].market prices (when include_intelligence=true). Valid values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, hardrock, betonline, all. Defaults to pinnacle. Single book = +1 credit for odds; all or a comma-separated list = +2. |

> **Note:** Credit costs: A plain call costs 1 credit. Adding include_odds=true costs 2 credits for a single book (default Pinnacle) or 3 credits for bookmaker=all / a list. Adding include_intelligence=true costs 2 credits total. Using both with default bookmaker costs 3 credits — cheaper than fetching event + odds + intelligence as three separate calls.

**Request**

```bash
# Basic — 1 credit
curl https://lumify.ai/v1/events/4812 \
  -H "Authorization: Bearer YOUR_API_KEY"

# Compound — event + odds + intelligence in one call (3 credits)
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
        "id": 1, "name": "Boston Bruins", "abbreviation": "BOS", "country_code": "USA"
      },
      "player":        null,               // null for team sports; see tennis example below
      "period_scores": []                 // per-period breakdown; empty [] if unavailable
    },
    {
      "role": "away", "score": "2", "game_score": null, "is_winner": false,
      "team": { "id": 2, "name": "Toronto Maple Leafs", "abbreviation": "TOR", "country_code": "CAN" },
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
    "analyst_take": "...",
    "match_overview": null,
    "intelligence_updated_at": "2026-05-10T01:45:00Z",
    "bets": [/* same bet objects as GET /v1/events/{id}/intelligence */ ]
  }
}
```

> **Warning:** Caching note: When include_odds=true, the compound response is cached for 2 minutes (pre-game/live) rather than the standard 5-minute event TTL, to reflect the faster-moving odds data. Final events remain cached for 1 hour.

> **Note:** Tennis scheduling: For tennis, starts_at is a floor (not a fixed time). scheduled_start_at preserves the original announced time. starts_at_qualifier will be not_before for order-of-play matches. Use court and order_of_play to understand draw position.

<!-- #event-detail -->

## Batch get events

`POST /v1/events/batch`

Fetch multiple events by id in a single round-trip — for agents that already have a list of ids (e.g. from GET /v1/events) and want full detail for each without one GET per event. Max **25** ids per call. Each returned event has the same shape as [GET /v1/events/{id}](#event-detail).

Credits are the sum of each event's normal compound cost. Duplicate ids are billed once. Ids that don't exist are returned under not_found and cost nothing. Unavailable odds/intelligence add-ons remain free (billing fairness).

### Request body

| Field | Type | | Description |
| --- | --- | --- | --- |
| event_ids | integer[] | required | 1–25 event ids. Order is preserved in the response. |
| include_odds | boolean | optional | Inline current odds scoped by bookmaker (default: pinnacle). +1 credit per event for a single book when available; +2 for all or a comma-separated list. |
| include_intelligence | boolean | optional | Inline bet intelligence on each event (+1 credit per event when available). |
| bookmaker | string | optional | Bookmaker for inlined odds and intelligence market prices. Defaults to pinnacle. Valid: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, hardrock, betonline, all. |

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
 Raw team/match statistics (Data), confidence scores and signal breakdowns (Intelligence), validator output, LLM-generated narratives, and public betting splits per event.

 [MCP: get_stats, get_intelligence, get_splits →](/docs/guides#mcp)
 [Guide: Build an MCP betting-splits agent →](/docs/guides#recipe-mcp-splits)
 [Guide: Pull a full intelligence report →](/docs/guides#recipe-intelligence-report)

## Get raw match statistics for an event

`GET /v1/events/{id}/stats`

Returns the deterministic, reproducible team and match statistics behind an event — computed directly from completed results and box scores already in the public record. This is the **Data** layer: no market/odds data (see /v1/events/{id}/odds for that) and no scoring, weighting, confidence, or narrative is attached. /v1/events/{id}/intelligence is the **Intelligence** layer built on top of these same inputs — use this endpoint when you want to run your own analysis on Lumify's underlying aggregates instead of (or alongside) Lumify's judgment. Always returns 200 when the event exists — check available to determine whether both teams have resolved. Returns 404 only if the event ID does not exist, and 400 if the event's sport is not yet supported.

> **Note:** Sports coverage: Soccer and MLB today. Other sports will get their own raw-stat endpoint as their equivalent data-fetch layer is factored out the same way.

The payload shape is sport-specific and never reuses field names across sports — branch on league_slug / the event's sport, not on the presence of a given key. Soccer: team strength (league-table rank/GD/W-D-L, or FIFA rank at the World Cup), recent form, head-to-head history, rest days, home/away splits, per-game boxscore rates (shots/SoT for & against, possession, corners, cards, save rate) over explicit windows (rates_l5 / rates_season), strength-of-schedule (sos), and lineups/formation — see the club-league example below. MLB: season-to-date W/L record + run differential, recent form (runs scored/allowed), head-to-head history, rest days, team batting/pitching rates (rates_l5 / rates_season — AVG/ERA/WHIP/K9/BB9 and component counts), the game's starting pitcher's own season ERA/WHIP/K9/BB9, and lineup (batting order + starting pitcher + subs) — see the MLB example further down. MLB Path A is post-final only: this event's lineup and starting-pitcher identity come from completed-game box scores (no pregame probable pitchers).

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
| teams.{home,away}.team_strength | object | Club leagues (source: "league_table_ppg"): season table row — ppg, games, points, w/d/l, gf/ga/gd, and ordinal rank (points → GD → GF). World Cup (source: "fifa_rank"): the team's current FIFA World Ranking. |
| teams.{home,away}.sos | object \| null | Club only: strength-of-schedule lite — average opponent PPG/rank across the last 5 completed league games (source: "opp_ppg_avg"). null for World Cup (no league table). |
| teams.{home,away}.lineup | object | Formation + starters/bench from ESPN summary rosters when ingested (available: false until then). Each player has name, position, jersey, formation_place, espn_athlete_id. |
| teams.{home,away}.venue | object | Club leagues (source: "home_away_ppg_split"): this team's own points-per-game when playing at home vs. away this season (each null until a minimum sample of completed games exists). World Cup (source: "confederation"): the team's confederation, used as a travel-distance proxy for neutral-site tournament venues. |
| teams.{home,away}.rates_l5 | object | Per-game averages from the last 5 completed matches with ESPN team box scores in this league (source: "event_stats_avg"). Includes shots_for/shots_against, shots_on_target_*, possession_pct, corners_*, cards, saves, and save_rate (total saves ÷ total SoT faced). Always includes games (0 when no box scores yet; rate fields are then null) and field_games — the number of those games that actually had a value for each individual field, since a source's summary can omit one stat on an otherwise-complete game. |
| teams.{home,away}.rates_season | object | Same shape as rates_l5 but averaged over the current season (club) or the full tournament (World Cup). window is "season" (no window_size). |
| head_to_head | object | Up to the last window (10) meetings between these two teams in this league, most-recent-first from the current home team's perspective. |
| league_context.avg_goals_per_team | number \| null | Season-to-date league-wide average goals scored per team per game. null for the World Cup (uses a fixed baseline instead) or before enough club-season games exist. |

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
        "era": 4.72,
        "whip": 1.38,
        /* + at_bats, hits, runs, home_runs, walks, strikeouts, doubles, stolen_bases, innings_pitched, earned_runs, hits_allowed, walks_allowed, strikeouts_pitched, home_runs_allowed, k9, bb9 */
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
| teams.{home,away}.record | object | Season-to-date source: "season_to_date" record: wins, losses, games, win_pct, runs_for, runs_against, run_differential. |
| teams.{home,away}.rates_l5 / rates_season | object | Team batting/pitching rate aggregates (source: "player_game_stats_sum") — every player's per-game box-score line summed to the team-game level, then averaged/derived across the window. batting_avg/era/whip/k9/bb9 are derived from the sum of their component totals, not an average of per-game ratios. Includes field_games per field, same convention as soccer. |
| teams.{home,away}.starting_pitcher | object | The game's own starting pitcher's season-to-date era/whip/k9/bb9, derived via outs-based ratio-of-sums from his own box-score rows. available: false until a post-final box score with lineup lands (Path A does not expose pregame probable pitchers). |
| teams.{home,away}.lineup | object | batting_order (9 batters, ordered) + starting_pitcher + bench (pinch hitters/relievers/subs) from the ingested final box score. No formation field — not a baseball concept. available: false until post-game ingest. |
| head_to_head | object | Up to the last window (10) meetings between these two teams, most-recent-first. meetings use home_runs/away_runs — not home_goals/away_goals. |

> **Tip:** Pairs with /intelligence: For soccer, these raw fields are exactly what feed the Core Signals in [GET /v1/events/{id}/intelligence](#event-intelligence) (Team Strength, Recent Form, Attack/Defense, Head-to-Head, Schedule/Rest, Venue) — that endpoint applies Lumify's scoring/weighting on top of these same numbers. For MLB, /stats and /intelligence are related but not identical: /stats reads our ingested box-score aggregates, while MLB intelligence still largely live-fetches overlapping signals (starting pitching, bullpen, lineup/OPS, etc.). Fetch both when you want the Data layer alongside Lumify's judgment.

<!-- #event-stats -->

## Get bet intelligence for an event

`GET /v1/events/{id}/intelligence`

Returns the full bet intelligence payload for an event. This endpoint is not cached — it always returns the latest computed data. Always returns 200 when the event exists — check available to determine whether intelligence has been computed yet. Returns 404 only if the event ID does not exist.

> **Warning:** Two response shapes. bets[] comes in one of two shapes depending on the sport and league. Branch on the presence of probability versus confidence_score — never assume one shape.

1. Probability model — currently soccer / MLS only. Each bet carries a calibrated probability, a vig-free fair_price, and the components behind them (p_market, p_model, blend_w, edge, sufficiency, drivers). It carries no confidence_score, coverage, signals, or validator. See [Probability-model bet fields](#intelligence-probability-fields).

2. Points model — every other sport and league: MLB, ATP/WTA tennis, NFL, NCAAF, FIFA World Cup soccer, and club soccer leagues other than MLS. Each bet carries confidence_score, coverage, signals, validator, narrative, rationale, and attribution. See [Points-model bet fields](#intelligence-points-fields).

Both shapes share bet_type, player_role, player_id, team_id, player_name, market, tier, and computed_at, plus every event-level field.

> **Note:** Sports coverage: Available for MLB, ATP/WTA tennis, FIFA World Cup 2026 soccer, MLS, NFL, and NCAAF. Intelligence is computed by the Lumify analysis pipeline and updated after each run. has_recommend: null means the pipeline has not yet run for that event. NFL and NCAAF analysis is seasonal — the pipelines self-skip in the offseason, so intelligence is only present during the football season.

MLB: Uses a 6-bet model. Bet tokens are ML_P1 (home), ML_P2 (away), SPREAD_P1, SPREAD_P2, OVER, UNDER. The model scores 9 core signals plus up to 4 optional supplementary signals (umpire factor, batting trend, travel fatigue, injury impact) returned in signals.signal_meta. OVER/UNDER confidence is capped at 0.80 — very_high tier is only reachable on moneyline and spread bets. Bets at extreme moneyline prices (≤ −400) are filtered out and will not appear in the response.

Soccer — MLS (probability model): MLS returns the probability shape. Bet tokens are ML_HOME, ML_AWAY, ML_DRAW, SPREAD_HOME, SPREAD_AWAY, OVER, UNDER. Unlike the points model, the outcomes of a market are solved together, so ML_HOME + ML_DRAW + ML_AWAY sum to 1, as do SPREAD_HOME + SPREAD_AWAY and OVER + UNDER — they cannot contradict each other. There are no signals or confidence_score on MLS bets.

Soccer — World Cup and other club leagues (points model): FIFA World Cup and club leagues other than MLS use the 3-way points model, with each token scored independently with its own confidence score, narrative, and tier. Signal keys are the same as tennis but map to soccer-specific concepts and different max points (see signal table below). Three signals are competition-aware: for the FIFA World Cup they measure FIFA Ranking Edge, Tournament Context (group vs. knockout), and Travel / Neutral site; for club leagues the same columns measure Team Strength (league table), Schedule & Rest, and Home Advantage. Human-readable labels for each signal — matching whichever competition type the fixture is — are included in the signals._labels object, so you never have to hardcode which column means what for soccer. Filter events with sport=soccer (optionally add &league=fifa_world_cup or a club-league slug such as mls).

Draws are match-level. For any 3-way soccer market, ML_DRAW carries player_role, player_id, team_id, and player_name as null, exactly like OVER/UNDER — a draw is not a bet on either team. You can sum exposure by team_id across bets[] without double-counting the draw against the home side.

NFL & NCAAF: Both use the same P1/P2 bet tokens as MLB — ML_P1 (home), ML_P2 (away), SPREAD_P1, SPREAD_P2, OVER, UNDER. Signals map to football-specific concepts. NFL: QB Edge, Offensive Efficiency, Defensive Strength, Situational/Weather, Recent Form, Market Odds, Research Alignment, Head-to-Head, Betting Splits. NCAAF: SP+ Power Rankings, Offensive/Defensive Efficiency, Market Odds, Research Alignment, Recent Form, Home Field/Weather, Head-to-Head, Betting Splits. Human-readable labels for each signal are included in the signals._labels object.

### Path parameters

| Parameter | Type | | Description |
| --- | --- | --- | --- |
| id | integer | required | Lumify event ID. Returns 404 if the event doesn't exist. If the event exists but intelligence has not been computed yet, returns 200 with available: false and empty bets array. |

**Request**

```bash
curl https://lumify.ai/v1/events/4821/intelligence \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Response**

```json
{
  "event_id":                4821,
  "available":               true,        // false when the pipeline hasn't run yet
  "players": {                                         // maps bet-token roles to players/teams
    "player_1": { "name": "Jacob Fearnley",            "player_id": 44, "team_id": null },
    "player_2": { "name": "Giovanni Mpetshi Perricard", "player_id": 51, "team_id": null }
  },
  "has_recommend":           true,       // false = all bets avoided; null = pipeline hasn't run
  "analyst_take":            "Expert consensus leans toward Fearnley given his dominant clay-court form and 3-1 H2H advantage. The market has installed him as a moderate favorite at -185, though prevailing sharp money has shown some interest on the underdog at +155. The narrow spread pricing suggests bookmakers expect a competitive match.",
  "match_overview":          null,         // populated instead of analyst_take when no bets are recommended
  "intelligence_updated_at": "2026-05-13T05:09:50Z",
  "bets": [
    {
      "bet_type":                       "ML_P1",          // MLB: ML_P1 (home) | ML_P2 (away) | SPREAD_P1 | SPREAD_P2 | OVER | UNDER
                                                             // tennis: ML_P1 | ML_P2 | SPREAD_P1 | SPREAD_P2 | OVER | UNDER
                                                             // soccer: ML_HOME | ML_AWAY | ML_DRAW | SPREAD_HOME | SPREAD_AWAY | OVER | UNDER
      "player_role":                    "player_1",       // matches participants[].role in GET /v1/events/{id}; null for OVER/UNDER
      "player_id":                      44,               // permanent player ID — matches participants[].player.id; null for OVER/UNDER
      "team_id":                        null,             // set for team sports (MLB etc.); null for player sports (tennis)
      "player_name":                    "Jacob Fearnley",
      "tier":                           "moderate",  // very_high | strong | moderate | avoid
      "confidence_score":               0.646,       // 0.0–1.0, after validator adjustment
      "confidence_score_pre_validator": 0.652,       // pre-validator score; null if validator hasn't run
      "coverage":                       1.0,         // fraction of 100-pt model that could be scored
      "market": {
        "price": -185,                              // American odds; null if no market data
        "line":  null                                // spread or total line; null for moneyline bets
      },
      "signals": {
        "signal_research":   20,   // Research Alignment         — max 22 pts (all sports)
        "signal_surface":    12,   // Surface Performance (tennis, max 15) | Tournament Context (soccer WC, max 8) | Schedule Context (soccer club, max 8)
        "signal_serve_rtn":  8,    // Serve / Return Edge (tennis, max 12) | Attack / Defense Edge (soccer, max 12)
        "signal_form":       10,   // Recent Form L10 (tennis, max 12)     | Recent Form (soccer, max 15)
        "signal_surface_frm":6,    // Surface Form L10 (tennis, max 8)     | Travel / Neutral (soccer WC, max 5) | Home Advantage (soccer club, max 5)
        "signal_market_odds":4,    // Market Odds Value          — max  8 pts (all sports)
        "signal_fatigue":    6,    // Fatigue / Context (tennis, max 8)    | Goal Environment (soccer O/U only, max 8; null on ML/spread/draw)
        "signal_h2h":        5,    // Head-to-Head (tennis, max 5)         | Head-to-Head (soccer, max 10)
        "signal_ranking":    8,    // Ranking Differential (tennis, max 10) — omitted for MLB; FIFA Ranking Edge (soccer WC, max 15) | Team Strength/Table (soccer club, max 15)
                                                          // signal_splits omitted for tennis (Owls doesn't support tennis splits)
        "_earned_pts":       84,   // sum of all non-null signal values
        "_max_pts":          108   // max possible given available data (differs by sport)
      },
      "validator": {
        "stance":       "neutral",   // validate | neutral | invalidate
        "confidence":   "medium",    // conviction in the stance: high | medium | low
        "delta":        -0.006,      // adjustment applied to pre-validator score
        "validated_at": "2026-05-13T05:09:43Z"
      },                                               // null if validator hasn't run for this bet
      "narrative":    "Fearnley enters this match having won 7 of his last 10 clay-court matches and holds a commanding H2H edge. The moneyline at -185 reflects his status as a significant favorite, and his superior surface form justifies the price.",
      "rationale": [// structured bullets derived from signal scores — agent-parseable
        "Strong Research Alignment (20/22)",
        "Strong Surface Performance (12/15)",
        "Moderate Serve / Return Edge (8/12)",
        "Strong Recent Form (10/12)",
        "Strong Head-to-Head (5/5)",
        "Deep Research returns no strong signal"
      ],
      "attribution": [// data sources that contributed meaningful signal
        "research_alignment",
        "surface_stats",
        "serve_return",
        "recent_form",
        "head_to_head",
        "deep_research"
      ],
      "computed_at":  "2026-05-13T03:41:17Z"
    }
    // … ML_P2, SPREAD_P1, SPREAD_P2, OVER, UNDER entries follow (MLB / tennis) …
    // … ML_AWAY, ML_DRAW, SPREAD_HOME, SPREAD_AWAY, OVER, UNDER entries follow (soccer) …
  ]
}
```

### Top-level fields

| Field | Type | Description |
| --- | --- | --- |
| available | boolean | false when the analysis pipeline has not yet run for this event. All other fields will be empty/null — check this first before reading bets. Not charged when false. |
| sport | string \| null | Sport slug for this event. Together with league, tells you which of the two bets[] shapes to expect. |
| league | string \| null | League slug for this event, if any — e.g. mls, fifa_world_cup. |
| odds_source | string \| null | Bookmaker the bets[].market prices came from. For the probability model this is the book the assessment was actually priced against, not a live overlay — per-bet market.book is authoritative if the two ever differ. |
| players | object | Participant identification keyed by role — {role: {name, player_id, team_id}}, where role is player_1/player_2 or home/away. Cross-reference with participants[] in GET /v1/events/{id}. |
| has_recommend | boolean \| null | true if at least one bet meets the recommendation threshold; false if none do; null if the pipeline hasn't run yet. A recommendation requires an edge, so this is false for any probability-model event whose bets are all market-anchored (blend_w of 0). |
| intelligence_updated_at | string \| null | ISO-8601 UTC timestamp of the most recent change anywhere in this payload — the maximum of the per-bet computed_at values. Individual markets are only rewritten when they move, so use the per-bet computed_at when reasoning about one specific bet. |
| analyst_take | string \| null | Event-level narrative summarising expert consensus and market sentiment. Present when at least one bet is recommended. |
| match_overview | string \| null | Short overview used when no bets are recommended. Explains why no clear edge exists. Mutually exclusive with analyst_take. |
| bets | array | One entry per scored bet token. MLB / tennis order: ML_P1 → ML_P2 → SPREAD_P1 → SPREAD_P2 → OVER → UNDER. Soccer order: ML_HOME → ML_AWAY → ML_DRAW → SPREAD_HOME → SPREAD_AWAY → OVER → UNDER. |
| matchup | object \| null | MLB only. Starting pitcher matchup derived from the research pipeline. Contains home_starter and away_starter objects, each with name (string), hand (pitching hand, if known), era (ERA, if available), and confirmed (boolean — whether the starter is confirmed vs. projected). null when research data is unavailable or for non-MLB events. |

### Probability-model bet fields

Returned for **soccer / MLS**. These bets carry a calibrated probability and a vig-free fair price instead of a points score. The components are exposed deliberately, so you can rebuild the published number yourself, apply your own model weight, or ignore our model entirely and consume the de-vigged market alone.

**Response (MLS, one bet shown)**

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
  "has_recommend": false,   // no edge yet on this league → nothing to recommend
  "bets": [
    {
      "bet_type":      "ML_HOME",
      "player_role":   "home",
      "team_id":       858,
      "player_name":   "D.C. United",
      "probability":   0.31903,   // calibrated; ML_HOME + ML_DRAW + ML_AWAY sum to 1
      "interval":     [0.2631, 0.37496],
      "p_market":     0.31903,   // de-vigged market price
      "p_model":      null,      // no fitted model cleared for this league yet
      "blend_w":      0,         // 0 → probability is purely the de-vigged market
      "fair_price":   213,       // vig-free line implied by probability
      "market": { "price": 199, "line": null, "book": "pinnacle" },
      "edge":         null,      // null while blend_w is 0 — see note below
      "sufficiency":  0.6,
      "tier":         null,      // null whenever edge is null
      "phase":        "quant",
      "model_version": "market_anchor",
      "drivers":      [],
      "alignment":    null,
      "computed_at":  "2026-07-27T10:07:20Z"
    }
    // … ML_AWAY, ML_DRAW, SPREAD_HOME, SPREAD_AWAY, OVER, UNDER follow …
  ]
}
```

| Field | Type | Description |
| --- | --- | --- |
| probability | number \| null | Published probability for this outcome, 0–1. Equals p_market when blend_w is 0; otherwise the blend of p_model and p_market at that weight. The outcomes of a market are solved together and sum to 1. |
| p_market | number \| null | De-vigged market probability. The bookmaker's price with the margin removed across the whole market, so outcomes sum to 1. This is not the same as implied probability from a single price and cannot be recomputed from market.price alone. null when the fixture is unpriced. |
| p_model | number \| null | Our fitted model's own probability, before blending. null for any league with no model yet cleared for publication — currently every soccer league. |
| blend_w | number \| null | Weight applied to p_model when blending with p_market, 0–1. 0 means the published probability is purely the de-vigged market. Weight is enabled per league and per bet token, and only where the model beat the market out-of-sample — so tokens on the same event can carry different weights. |
| fair_price | integer \| null | American-odds fair price implied by probability — the vig-free line. Comparing it to market.price gives the book's margin on this side (above: +213 fair vs +199 offered). |
| edge | number \| null | Expected profit per 1 unit staked at market.price, i.e. probability × decimal_odds − 1. Positive means the price pays more than the probability justifies. null whenever blend_w is 0: a probability taken from the market has no honest edge against the price it came from, so reporting one would just restate the vig. |
| interval | number[] \| null | [lo, hi] band around probability. Read it as how much evidence backs this number, not as a statistical confidence interval — its width is driven by sufficiency and its constants are calibrated against realised outcomes rather than derived analytically. While blend_w is 0 the band reflects how mature and well-traded the quoted line is, so a freshly-opened line gets a wider band than a heavily-traded one. |
| sufficiency | number \| null | How much evidence backs this assessment, 0–1. Sets interval width and caps tier. Its inputs depend on what is being measured: while blend_w is 0 it measures the quoted line's maturity (how many times it has moved on the priced book, and hours since that book's first quote), because there is no model sample to be thin about. Once a model carries weight it reflects the model's own sample depth. Thin evidence widens the interval rather than removing the response. |
| drivers | object[] | Named, signed contributions to probability: {id, input, effect, direction}, where effect is the probability shift attributed to that factor and direction is up/down/neutral. This is the probability-model equivalent of signals. Empty whenever no model contributed to the bet. |
| phase | string \| null | quant when the assessment is purely deterministic (ratings, market, and model math). full once a qualitative overlay — lineups, injuries, research alignment — is attached, which is the only case where alignment is populated. |
| alignment | object \| null | Qualitative-overlay agreement detail. Populated only when phase is full; null for every quant assessment. |
| model_version | string \| null | Identifier of the parameter set that produced this assessment, so a published number can be traced to the version that made it. market_anchor means no fitted model contributed. Reported per bet, since model weight is enabled per token. |
| tier | string \| null | very_high, strong, moderate, or avoid. null whenever edge is null — a tier ranks a bet against its price, so there is nothing to rank without an edge. |
| market.book | string \| null | Bookmaker this bet's price/line came from, and the book probability, fair_price, and edge were computed against. Always set for the probability model. The ?bookmaker= parameter does not apply to this shape. |
| computed_at | string \| null | ISO-8601 UTC time this bet's numbers last materially changed — not when they were last checked. The publisher runs on a schedule but only rewrites a bet when its price, line, or probability moves beyond a tolerance, so an older timestamp means "unchanged since", not "stale". Bets on the same event legitimately differ here because each market moves independently. |

> **Tip:** Reading a market-anchored event. When blend_w is 0 across the payload, treat it as a fair-price reference, not a set of picks: probability and fair_price tell you what the market thinks with the vig stripped out, which is the input most agents want for their own expected-value math. edge, tier, and drivers populate per league and per token as models clear out-of-sample validation, so code against them now and they will fill in without a response-shape change.

### Points-model bet fields

Returned for MLB, tennis, NFL, NCAAF, FIFA World Cup soccer, and club soccer leagues other than MLS. The response example above this table shows this shape.

| Field | Type | Description |
| --- | --- | --- |
| bet_type | string | MLB: ML_P1 (home), ML_P2 (away), SPREAD_P1, SPREAD_P2, OVER, UNDER. Tennis: ML_P1, ML_P2, SPREAD_P1, SPREAD_P2, OVER, UNDER. Soccer: ML_HOME, ML_AWAY, ML_DRAW, SPREAD_HOME, SPREAD_AWAY, OVER, UNDER. Soccer moneyline is a 3-way market — ML_HOME, ML_AWAY, and ML_DRAW are all scored independently. |
| player_role | string \| null | player_1/player_2 or home/away — matches participants[].role in GET /v1/events/{id}. null for match-level tokens: OVER, UNDER, and ML_DRAW. |
| player_id | integer \| null | Permanent player identity — matches participants[].player.id in GET /v1/events/{id}. Stable across all events. null for team sports and for match-level tokens (OVER, UNDER, ML_DRAW). |
| team_id | integer \| null | Permanent team identity for team-sport bets (MLB, soccer, NFL etc). null for player-sport bets (tennis) and for match-level tokens (OVER, UNDER, ML_DRAW) — a draw is not a bet on either team, so summing exposure by team_id never double-counts it. |
| tier | string \| null | Recommendation tier: very_high, strong, moderate, avoid |
| confidence_score | number | Final confidence (0.0–1.0) after validator adjustment |
| confidence_score_pre_validator | number \| null | Confidence score before the deep-research validator ran. null if the validator has not yet processed this bet. Useful for measuring validator impact. |
| coverage | number | Signal coverage ratio (0.0–1.0). 1.0 = all applicable signals had sufficient data. |
| market.price | integer \| null | American odds, e.g. -185, +155 |
| market.line | number \| null | Spread or total line, e.g. -3.5, 22.5. null for moneyline bets. |
| signals.signal_* | integer \| null | Individual signal scores. null when data was unavailable for that signal. Signal keys are shared across sports but map to different concepts and max points depending on the sport. MLB max pts: signal_surface 25 (Starting Pitching), signal_serve_rtn 15 (Bullpen), signal_form 15 (Lineup/OPS), signal_market_odds 10 (Market Odds), signal_research 20 (Research Alignment), signal_splits 8 (Sharp Money), signal_fatigue 8 (Recent Form), signal_surface_frm 7 (Park & Weather), signal_h2h 5 (H2H). Tennis max pts: signal_research 22, signal_surface 15, signal_serve_rtn 12, signal_form 12, signal_surface_frm 8, signal_market_odds 8, signal_fatigue 8, signal_h2h 5, signal_ranking 10. (signal_splits is omitted from tennis responses — Owls Insight does not support tennis splits.) Soccer max pts: signal_research 22 (Research Alignment), signal_ranking 15 (World Cup: FIFA Ranking Edge; club leagues: Team Strength / league table), signal_form 15 (Recent Form), signal_serve_rtn 12 (Attack/Defense Edge), signal_h2h 10 (Head-to-Head), signal_surface 8 (World Cup: Tournament Context; club leagues: Schedule & Rest), signal_market_odds 8, signal_fatigue 8 (Goal Environment — OVER/UNDER only; null on ML/spread/draw), signal_surface_frm 5 (World Cup: Travel/Neutral; club leagues: Home Advantage), signal_splits 8. |
| signals.signal_meta | object \| null | MLB only. JSON object containing optional supplementary signal scores that did not fit the shared signal columns. Keys: umpire (0–5, home plate umpire run-environment factor), batting_trend (0–3, L15 OPS vs season delta), travel (0–3, time-zone fatigue), injury (0–3, IL key-position player differential). Each key is omitted when data was unavailable. null for all non-MLB sports. |
| signals._labels | object | Present for NFL, NCAAF, and soccer only — omitted entirely for tennis and MLB. Maps every signal_* key present on this bet to its human-readable, sport-specific label (e.g. signal_serve_rtn → "Attack / Defense Edge" for soccer). For soccer this already reflects the fixture's competition type (World Cup vs. club-league labels), so you can render or reason about signals without hardcoding the column-name → concept mapping yourself. |
| signals._earned_pts | integer | Sum of all non-null signal values for this bet |
| signals._max_pts | integer | Maximum possible points given available signal data. |
| validator.stance | string \| null | validate, neutral, or invalidate |
| validator.confidence | string \| null | Conviction level of the validator stance: high, medium, or low |
| validator.delta | number \| null | Confidence adjustment applied by the validator. Positive = boost, negative = reduction. |
| narrative | string \| null | LLM-generated bet rationale written for human consumption. Typically present for recommended bets; null for avoid tier. |
| rationale | string[] | Structured list of signal-derived bullets, designed for agent consumption. Each entry describes a signal's contribution, e.g. "Strong Research Alignment (20/22)". Always present — contains at least one entry. |
| attribution | string[] | List of data-source keys that contributed meaningful signal to this bet, e.g. ["research_alignment", "surface_stats", "deep_research"]. Useful for agents reasoning about signal provenance. |

> **Tip:** Workflow tip: Call /v1/events to list events — use sport=mlb&status=scheduled for MLB, sport=tennis&status=scheduled for tennis, sport=soccer&league=fifa_world_cup&status=scheduled for World Cup matches, sport=soccer&league=mls for MLS, or sport=nfl / sport=ncaaf during football season. Then fetch /v1/events/{id}/intelligence for any game you want analysis on.

Points-model events: check has_recommend first — if false, read match_overview; if true, look for bets where tier is not "avoid" and read narrative + analyst_take. For MLB, ML_P1 is always the home team.

Probability-model events (MLS): ignore has_recommend until edge is populated. Compare fair_price to market.price to see the book's margin, use p_market as the de-vigged probability input to your own expected-value math, and use sufficiency to decide how much to trust a thin, freshly-opened line. All three moneyline outcomes sum to 1, so you can renormalise or compare across markets safely.

<!-- #event-intelligence -->

## Get betting splits for an event

`GET /v1/events/{id}/splits`

Returns public betting split data for an event — the percentage of bets and handle wagered on each side across moneyline, spread, and total markets. Includes a consensus (average across books) and a per-bookmaker breakdown. Updated every ~30 minutes. Always returns 200 when the event exists — check available to determine whether splits have been ingested yet. Returns 404 only if the event ID does not exist.

> **Note:** Sports coverage: Available for MLB, NBA, NHL, and NFL (during their respective seasons). Tennis, soccer, and NCAAF splits are not available on the Owls Insight v1 API. Soccer odds are available via [/v1/events/{id}/odds](#event-odds). Splits are only ingested for pre-game events; data is not updated once a game starts.

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
  "books": [
    {
      "book": "dk",
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
| available | boolean | false when no splits have been ingested yet. consensus will be an empty object and books an empty array. |
| captured_at | string \| null | UTC timestamp of the most recent ingest cycle for this event's splits data. null when available is false. |
| consensus | object | Market averages across all available books. Contains moneyline, spread, and total objects. |
| consensus[market][side].bets_pct | integer | Percentage of total bets placed on this side (0–100). Opposite sides sum to ~100. |
| consensus[market][side].handle_pct | integer | Percentage of total money wagered on this side (0–100). A large gap between handle_pct and bets_pct indicates sharp (large-bet) money diverging from public action. |
| consensus[market][side].price | integer \| null | American odds for this side. Present on moneyline; null on spread/total sides. |
| consensus[market][side].line | number \| null | Spread or total line. Present on spread/total; null on moneyline. |
| books | array | Per-bookmaker breakdown. Same structure as consensus but for a single book. book is the bookmaker key (e.g. dk); name is the display name. |

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
 Player profiles, rankings, and event history across all supported sports.

 [MCP: search_players, get_player, get_player_events →](/docs/guides#mcp)

## List players

`GET /v1/players`

Returns a paginated list of players. Supports filtering by sport, country, name search, active status, and ranking. Results are sorted by ascending player ID.

### Query parameters

| Parameter | Type | | Default | Description |
| --- | --- | --- | --- | --- |
| sport | string | optional | — | Filter by sport slug: tennis, mlb, nfl, etc. |
| q | string | optional | — | Partial name search. Case-insensitive match against full_name (e.g. ?q=sinner). |
| country | string | optional | — | ISO 3166-1 alpha-3 country code (e.g. USA, ITA, GBR). Case-insensitive. |
| active | boolean | optional | — | Pass true for active players only, false for retired. |
| ranked | boolean | optional | — | If true, returns only players with a current ATP/WTA ranking. Useful for tennis leaderboard use cases. |
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
      "tennis_ranking":        1,
      "tennis_ranking_points": 14350,
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
  "tennis_ranking":        1,
  "tennis_ranking_points": 14350,
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

Returns the current moneyline, spread, and total lines for an event. Defaults to **Pinnacle only (1 credit)**. Use bookmaker=all or a comma-separated list to fetch multiple books at **2 credits**. Data is updated every ~30 minutes and cached for 2 minutes. Always returns 200 when the event exists — check available to determine whether odds have been ingested yet. Returns 404 only if the event ID does not exist.

> **Note:** Soccer (FIFA World Cup): Filter events with league=fifa_world_cup. Soccer moneyline (h2h) is a 3-way market — outcomes include both team names plus Draw. Asian handicap spreads use goal lines (e.g. -0.5, +0.5). Odds are ingested for all known-team fixtures during the tournament window; TBD knockout placeholders (e.g. "Round of 32 Winner") will return available: false until teams are determined.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

### Query parameters

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| bookmaker | string | pinnacle | Bookmaker filter. Accepted values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, hardrock, betonline, all, or a comma-separated combination (e.g. fanduel,betmgm). 1 credit for a single bookmaker · 2 credits for multiple or all. |

**Request — Pinnacle only (default, 1 credit)**

```bash
curl https://lumify.ai/v1/events/4821/odds \
  -H "Authorization: Bearer $LUMIFY_API_KEY"
```

**Request — all bookmakers (2 credits)**

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
| bookmaker | string | Bookmaker key, e.g. pinnacle, draftkings, betmgm. Supported odds books: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, hardrock, betonline. Availability per event depends on what has been ingested. |
| markets | array | Markets for this bookmaker, ordered: moneyline → spread → totals. |
| key | string | Market key: h2h, spreads, or totals. |
| label | string | Human-readable label: moneyline, spread, or totals. |
| outcomes | array | Each outcome has outcome (name), price (American odds integer), and point (spread/total line; null for moneyline). Soccer h2h includes three outcomes: home team, away team, and Draw. |
| captured_at | string | UTC timestamp when this bookmaker's odds were last ingested. |
| last_updated | string | Most recent captured_at across all bookmakers. |

<!-- #event-odds -->

## Get odds movement history

`GET /v1/events/{id}/odds/history`

Returns all recorded line movements for an event — any time a price or point changed between ingest cycles. Defaults to **Pinnacle only (1 credit)**. Use bookmaker=all or a comma-separated list for multiple books at **2 credits**. Ordered newest-first. Useful for detecting sharp line movement. Not cached. Returns 404 if no movement has been recorded.

### Path parameters

| Name | Type | Description |
| --- | --- | --- |
| id | integer | Lumify event ID. |

### Query parameters

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| bookmaker | string | pinnacle | Bookmaker filter. Accepted values: pinnacle, fanduel, draftkings, betmgm, caesars, bet365, circa, hardrock, betonline, all, or a comma-separated combination. 1 credit for a single bookmaker · 2 credits for multiple or all. |
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

### Create a subscription

`POST /v1/webhooks`

| Field | Type | | Description |
| --- | --- | --- | --- |
| url | string | required | HTTPS endpoint to receive deliveries. Rejected if it resolves to a private/internal address. |
| event_types | string[] | optional | One or more of score, status, line_move, intelligence. Defaults to ["score", "status"]. |
| sport | string | optional | Restrict to one sport slug. Omit to subscribe across sports. |
| event_id | integer | optional | Restrict to a single event. Omit to subscribe to all matching events. |

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

| Sport | League slug | Type | Live scores |
| --- | --- | --- | --- |
| NFL | nfl | Team league | Yes |
| NBA | nba | Team league | Yes |
| MLB | mlb | Team league | Yes |
| NHL | nhl | Team league | Yes |
| NCAAF | ncaaf | Team league | Yes (in season) |
| NCAAB | ncaab | Team league | Yes (in season) |
| Tennis | atp, wta | Individual tour | Yes |
| Soccer | fifa_world_cup | Tournament | Yes (tournament dates only) |
| Soccer | mls | Team league | Yes (in season) |
| Soccer | epl, la_liga, serie_a, bundesliga, ligue_1 | Team league | Yes (in season) |
| Soccer | ucl | Tournament | Yes (in season) |

> **Note:** All timestamps are stored and returned in UTC. Use the venue timezone field to convert to local time for display.

<!-- #sports-coverage -->
