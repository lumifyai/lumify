# Player props catalog

> Canonical URL: https://lumify.ai/docs/player-props
> HTML twin: https://lumify.ai/docs/player-props

NFL, NCAAF, NBA, NCAAB, NHL, and MLB only. `GET /v1/events/{id}/player-props` (MCP `get_player_props`)
returns persisted player-prop mains joined to this-event player box counts.
`GET /odds` stays moneyline / spread / totals. Other sports return HTTP 400.
1 credit when lines exist; `available:false` is free.

This page is the coverage inventory plus response-field meanings.
Endpoint inspector: [API reference — player props](https://lumify.ai/docs/reference#event-player-props).
Forecast how + field catalog: [How Lumify forecasts prop wagers](https://lumify.ai/docs/forecasts).

## How to read the table

- **Yes — over / under / push** — the market grades from this-event box
  counts (1:1 slug, combo sum, weighted combo, or yes/no threshold)
  once the event is final and `current` is present.
- **Returned, not graded** — the line is in the payload with
  `settleable:false` and `result:null` until it has its own settlement rule.
- **Yes — 1:1 slate** — `list_forecasts` / `forecasts[]` may pick this market.
  Combos, anytime TD, and double-double stay settleable-only.

## NFL

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `passing_yards` | Passing yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `passing_tds` | Passing touchdowns | Yes — over / under / push | Settleable only | — |
| `rushing_yards` | Rushing yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `rushing_tds` | Rushing touchdowns | Yes — over / under / push | Settleable only | — |
| `receiving_yards` | Receiving yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `receptions` | Receptions | Yes — over / under / push | Yes — 1:1 slate | — |
| `touchdowns` | Anytime touchdown | Yes — over / under / push | Settleable only | Anytime TD scorer: rushing + receiving + defensive TDs. Passing TDs do not count. Kick/punt return TDs are not in the box yet. |

## NCAAF

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `passing_yards` | Passing yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `passing_tds` | Passing touchdowns | Yes — over / under / push | Settleable only | — |
| `rushing_yards` | Rushing yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `rushing_tds` | Rushing touchdowns | Yes — over / under / push | Settleable only | — |
| `receiving_yards` | Receiving yards | Yes — over / under / push | Yes — 1:1 slate | — |
| `receptions` | Receptions | Yes — over / under / push | Yes — 1:1 slate | — |
| `touchdowns` | Anytime touchdown | Yes — over / under / push | Settleable only | Anytime TD scorer: rushing + receiving + defensive TDs. Passing TDs do not count. Kick/punt return TDs are not in the box yet. |

## NBA

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `points` | Points | Yes — over / under / push | Yes — 1:1 slate | — |
| `rebounds` | Rebounds | Yes — over / under / push | Yes — 1:1 slate | — |
| `assists` | Assists | Yes — over / under / push | Yes — 1:1 slate | — |
| `steals` | Steals | Yes — over / under / push | Yes — 1:1 slate | — |
| `blocks` | Blocks | Yes — over / under / push | Yes — 1:1 slate | — |
| `threes_made` | Threes made | Yes — over / under / push | Yes — 1:1 slate | — |
| `pts_rebs` | Points + rebounds | Yes — over / under / push | Settleable only | Sum of points + rebounds. |
| `pts_asts` | Points + assists | Yes — over / under / push | Settleable only | Sum of points + assists. |
| `rebs_asts` | Rebounds + assists | Yes — over / under / push | Settleable only | Sum of rebounds + assists. |
| `pts_rebs_asts` | Points + rebounds + assists | Yes — over / under / push | Settleable only | Sum of points + rebounds + assists. |
| `double_double` | Double-double | Yes — over / under / push | Settleable only | Yes (current=1) if two or more of points, rebounds, assists, steals, blocks are ≥ 10. Graded vs the posted line (typically 0.5). |
| `triple_double` | Triple-double | Yes — over / under / push | Settleable only | Yes (current=1) if three or more of points, rebounds, assists, steals, blocks are ≥ 10. Graded vs the posted line (typically 0.5). |

## NCAAB

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `points` | Points | Yes — over / under / push | Yes — 1:1 slate | — |
| `rebounds` | Rebounds | Yes — over / under / push | Yes — 1:1 slate | — |
| `assists` | Assists | Yes — over / under / push | Yes — 1:1 slate | — |
| `steals` | Steals | Yes — over / under / push | Yes — 1:1 slate | — |
| `blocks` | Blocks | Yes — over / under / push | Yes — 1:1 slate | — |
| `threes_made` | Threes made | Yes — over / under / push | Yes — 1:1 slate | — |
| `pts_rebs` | Points + rebounds | Yes — over / under / push | Settleable only | Sum of points + rebounds. |
| `pts_asts` | Points + assists | Yes — over / under / push | Settleable only | Sum of points + assists. |
| `rebs_asts` | Rebounds + assists | Yes — over / under / push | Settleable only | Sum of rebounds + assists. |
| `pts_rebs_asts` | Points + rebounds + assists | Yes — over / under / push | Settleable only | Sum of points + rebounds + assists. |
| `double_double` | Double-double | Yes — over / under / push | Settleable only | Yes (current=1) if two or more of points, rebounds, assists, steals, blocks are ≥ 10. Graded vs the posted line (typically 0.5). |
| `triple_double` | Triple-double | Yes — over / under / push | Settleable only | Yes (current=1) if three or more of points, rebounds, assists, steals, blocks are ≥ 10. Graded vs the posted line (typically 0.5). |

## NHL

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `goals` | Goals | Yes — over / under / push | Yes — 1:1 slate | — |
| `hockey_assists` | Assists | Yes — over / under / push | Yes — 1:1 slate | Prop category hockey_assists. Box slug is assists_nhl (MLB/NBA own the global assists slug). |
| `shots_on_goal` | Shots on goal | Yes — over / under / push | Yes — 1:1 slate | — |
| `hockey_points` | Points (goals + assists) | Yes — over / under / push | Settleable only | Sum of goals + assists (assists_nhl). |

## MLB

| Market key | Name | Graded? | Forecasted? | Notes |
|---|---|---|---|---|
| `hits` | Hits | Yes — over / under / push | Yes — 1:1 slate | — |
| `runs` | Runs | Yes — over / under / push | Yes — 1:1 slate | — |
| `rbis` | RBIs | Yes — over / under / push | Yes — 1:1 slate | Prop category rbis. Box slug is rbi. |
| `home_runs` | Home runs | Yes — over / under / push | Settleable only | — |
| `stolen_bases` | Stolen bases | Yes — over / under / push | Settleable only | — |
| `strikeouts_batter` | Batter strikeouts | Yes — over / under / push | Yes — 1:1 slate | Prop category strikeouts_batter. Box slug is strikeouts (batter Ks). |
| `total_bases` | Total bases | Yes — over / under / push | Settleable only | TB = hits + doubles + 2·triples + 3·home_runs (standard identity). |
| `hits_runs_rbis` | Hits + runs + RBIs | Yes — over / under / push | Settleable only | Sum of hits + runs + RBI. |
| `strikeouts_pitcher` | Pitcher strikeouts | Yes — over / under / push | Yes — 1:1 slate | Prop category strikeouts_pitcher. Box slug is strikeouts_pitched. |
| `hits_allowed` | Hits allowed | Yes — over / under / push | Yes — 1:1 slate | — |
| `earned_runs` | Earned runs | Yes — over / under / push | Yes — 1:1 slate | — |
| `outs_recorded` | Outs recorded | Yes — over / under / push | Yes — 1:1 slate | Prop category outs_recorded. Box slug is outs. |

## Sports not on this surface

| Sport | Status |
|---|---|
| Soccer (`soccer`) | Not on `GET /player-props` (HTTP 400) |
| Tennis (`tennis`) | Not on `GET /player-props` (HTTP 400) |

## Endpoint

```
GET https://lumify.ai/v1/events/{id}/player-props
Authorization: Bearer lmfy-...
```

MCP: `get_player_props` with `{ "event_id": … }`.

Sample payload:
[/docs/reference#event-player-props](https://lumify.ai/docs/reference#event-player-props).

## Response fields

Shared live-progress envelope on player-props, team-props, and period-odds.

| Field | Type | Description |
|---|---|---|
| `available` | boolean | False when no mains have been ingested. Not charged. |
| `sport` | string | Event sport slug. |
| `status` | string | Event status. Same enum as `/docs/reference#status-values`. |
| `period` / `clock` | string or null | Live clock. Sport-specific formats: `/docs/reference#event-score`. |
| `player` / `player_id` | string / integer or null | Display name and Lumify ID. Join `player_id` to `/v1/players/{id}`. Null when the priced name did not bind. |
| `market` | string | Prop market key (this page). |
| `line` | number | Posted main Over/Under. Half-points are typical. A different number is a separate row. |
| `current` | number or null | This-event box count — 1:1 slug, combo sum, or yes/no (1.0/0.0). Null before the box lands, when unmatched, or when `settleable` is false. |
| `pct_of_line` | number or null | `current / line × 100`, one decimal. Can exceed 100. Null when `current` or `line` is null, when `line` is 0, or on yes/no markets. |
| `settleable` | boolean | True when this market has a settlement rule. When false, `current` and `result` are null. |
| `result` | string or null | `in_progress` while not final. `over` / `under` / `push` once final and `current` is present. Null when `settleable` is false. |
| `books` | object | Per-book Over/Under American-odds integers at this exact `line`. A missing side is null. |
