# How Lumify Forecasts Wagers

> Canonical URL: https://lumify.ai/docs/forecasts.md
> HTML twin: https://lumify.ai/docs/forecasts

How the forecast model works — a probability-based prediction, not a beat-the-market claim. Player-prop rate model plus tennis main-line (moneyline from ranking; spreads/totals from a Normal-approx games model). Field catalog and the forecastable-vs-settleable subset.

<!-- Auto-generated from api/templates/public/docs_forecasts.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

# How Lumify forecasts wagers

A model prediction, not a beat-the-market claim — no OOS/independence gate, unlike main-line ev. Player-prop rate model on MLB / NFL / NCAAF / NBA / NCAAB / NHL; tennis main-line — moneyline from ranking Bradley-Terry, game handicap and total games from a Normal-approx games model. A sibling of predictive bets[], not a replacement. Inspector endpoints stay on the [API reference](/docs/reference#intelligence-forecasts). This page is the how and the field catalog.

## Three intelligence surfaces

- **Predictive bets[]** — vig-stripped probability / fair_price plus Price overlay on MLB, tennis, soccer (MLS + big-five), NFL, and NCAAF. Walkthrough: [/docs/understanding-odds](/docs/understanding-odds).

- **Main-line ev (Beta)** — the same sharp-fair gap packaged as ev_pct + Kelly on moneyline, spreads, and totals. Scan: [GET /intelligence/ev](/docs/reference#intelligence-ev).

- **forecasts[]** — this page. A probability-based prediction, not a beat-the-market claim. Player props: MLB, NFL, NCAAF, NBA, NCAAB, NHL. Tennis main-line — moneyline (ML_P1/ML_P2) from ranking gap, game handicap (SPREAD_P1/SPREAD_P2) and total games (OVER/UNDER) from a Normal-approx games model — not tennis bets[]. Can populate when available is still false. Do not treat available: false as “no intelligence JSON.”

<!-- #surfaces -->

## How the model works

- Start from the player's recent counting-stat rate (typically last 10 games), shrunk toward a prior so a 3-game heater does not dominate. Prior weight is 12 — sufficiency is n / (n + 12).

- Treat that rate as λ in a Poisson and score it against the posted Over/Under main. The model always picks the more likely side when a strictly-matched two-way main is in range.

- One-sided longshots (|price| ≥ 1000) and rate-certain low-count lines (p_hit ≥ 0.95 on counting markets) are dropped so ladder rows do not fill the board. Yardage markets skip that Poisson cut.

- Rank the slate by conviction — distance from a coin flip, times how much of the rate is this player's own boxes, times an optional research multiplier. Cap: 3 wagers per event / 25 on the sport slate.

- Optional Deep Research overlay may nudge p_hit by at most ±0.03. The chosen side never flips.

GET /intelligence/forecasts returns only the selected: true rows (the daily board). GET /events/{id}/intelligence forecasts[] includes the rest of that event's catalog with selected: false.

<!-- #model -->

## Forecastable markets vs settleable inventory

Forecasts score a **1:1 counting subset** of the player-props catalog. Combos, anytime TD, double-double / triple-double, and hockey points are settleable on [/docs/player-props](/docs/player-props) but are not selected onto the daily board.

| Sport | Forecastable markets (1:1) | On player-props, not forecasted |
| --- | --- | --- |
| MLB | strikeouts_pitcher, hits, rbis, runs, strikeouts_batter, hits_allowed, earned_runs, outs_recorded | home_runs, stolen_bases, total_bases, hits_runs_rbis |
| NFL / NCAAF | passing_yards, rushing_yards, receiving_yards, receptions | passing_tds, rushing_tds, touchdowns |
| NBA / NCAAB | points, rebounds, assists, steals, blocks, threes_made | pts_rebs, pts_asts, rebs_asts, pts_rebs_asts, double_double, triple_double |
| NHL | goals, hockey_assists, shots_on_goal | hockey_points |
| Tennis | Moneyline (ML_P1 / ML_P2) from ranking Bradley-Terry; game handicap (SPREAD_P1 / SPREAD_P2) and total games (OVER / UNDER) from a Normal-approx games model fit on historical set/game scores — soft-book game-unit lines only, never Pinnacle's set-unit total | — |

<!-- #markets -->

## Field catalog

Player-prop rows: bet_type is null, and player / player_id / side are populated. Tennis moneyline rows set bet_type to ML_P1 or ML_P2, player_role to p1/p2, and leave side / line null. Tennis spread rows set bet_type to SPREAD_P1/SPREAD_P2 with player / player_role / line populated. Tennis total-games rows set bet_type to OVER/UNDER with line populated and player / player_id / player_role null — the total is match-level, not about either player.

### Top-level (daily board)

| Field | Type | Description |
| --- | --- | --- |
| sport | string | Sport slug this slate was scored for. |
| date | string | UTC slate date (YYYY-MM-DD). |
| model_version | string | Scorer version used for every wager on this page (e.g. forecast-v0). |
| reliability | string | Default badge on this slate. v0 ships emerging; each wager repeats the same field. Cells promote as a scored history accumulates — there is no numeric threshold published yet. |
| wagers | array | Selected forecasted wagers, highest conviction first. |
| total | integer | Count of wagers on this page. |

### Wager fields

| Field | Type | Description |
| --- | --- | --- |
| event_id | integer | Lumify event ID. Present on the daily board; omitted on GET /intelligence forecasts[] (the event is the path). |
| player / player_id | string or null / integer or null | Display name and Lumify ID. Bound by exact / Jr-stripped name match to the priced line. Join player_id to GET /v1/players/{id}. Null on a main-line row with no player attribution (match-level bet_type like OVER/UNDER/ML_DRAW). |
| bet_type | string or null | Main-line token. Tennis sets ML_P1/ML_P2 (moneyline), SPREAD_P1/SPREAD_P2 (game handicap), or OVER/UNDER (total games). Null on player-prop rows — that is the discriminator. ML_HOME/ML_AWAY/ML_DRAW (team sports) are reserved. |
| player_role | string or null | home/away for team sports or p1/p2 for head-to-head sports, set only alongside a non-null bet_type. Null on player-prop rows and on match-level main-line tokens. |
| market | string | Player-prop rows: 1:1 counting category from the table above (not the combo / yes-no keys on the settleable catalog). Main-line rows (bet_type set): the main-line family — h2h, spreads, or totals. |
| line | number or null | Posted line the model was scored against. Player-prop and totals main-line rows: Over/Under number. spreads main-line rows: the spread number. Null on h2h/moneyline rows. |
| side | string or null | Player-prop rows: over or under — the more likely side given the player's shrunken rate versus line. Null on main-line rows — read the picked outcome from bet_type instead. |
| p_hit | number | Model probability (0–1) that the picked outcome (side on prop rows, bet_type on main-line rows) hits. Prop rows: built from the player's shrunken counting-stat rate (Poisson vs the posted Over/Under). Optional research may nudge a prop's p_hit by at most ±0.03; the chosen side stays the same. |
| interval | [number, number] | [lo, hi] stated band around p_hit. Wider when sufficiency is low. A stated evidence band, not a statistical confidence interval. |
| sufficiency | number | Evidence weight on 0–1: n / (n + 12), where n is the recent-form game count (typically L10). A player with 10 recent games has sufficiency ≈ 0.45 — about half the rate is player-observed, half prior. The wager still ships at any sufficiency. |
| conviction | number | Board rank key on 0–1: \|p_hit − 0.5\| × 2 × sufficiency × research. A 0.76 call on a thin sample ranks below a 0.62 call on a long one. Highest conviction first. This is not the same scale as research.conviction. |
| reliability | string | Badge on this sport×market cell: emerging, moderate, high, or informational. v0 ships emerging for every wager. Promotion is “as a scored history accumulates,” not a published numeric threshold. |
| selected | boolean | true on the daily board (these are the top-conviction rows). On GET /intelligence the array also includes the rest of the event catalog with selected: false. |
| books | object | American price for the picked outcome, keyed by bookmaker slug. Posted market price for the side/bet_type the model picked. |
| drivers | array | Signed contributions that moved p_hit. Typical prop-row id is player.l10_rate (shrunken L10 counting rate); tennis moneyline uses player.tennis_ranking, tennis spreads use player.tennis_game_margin, tennis totals use match.tennis_total_games. Treat unknown ids as opaque. input is the measured rate/rating behind the driver; effect is the probability-unit shift versus a baseline case on the same line (0.0 on yardage); direction is up / down / neutral. |
| research | object or null | Optional Deep Research overlay on high-probability wagers (p_hit ≥ 0.80): {stance, conviction, note}. stance is validate / neutral / invalidate. note is the wager-level why (the fact the model cannot see); validate / invalidate rows always carry one. research.conviction is a qualitative research strength (high / medium / low), not the 0–1 wager conviction rank. Validate nudges p_hit up by at most 0.03 and lifts the rank; invalidate does the reverse. The chosen side stays. null means read p_hit from the rate model alone. |

<!-- #fields -->

## Worked wager

 Example wager · forecasts[] · list_forecasts

 Total Runs — Ben Rortvedt

 MLB
 Under

 0.5

 —

 −453
 DraftKings

The write-up below is this ticket: under 0.5 runs at DraftKings −453.

Ben Rortvedt is priced at runs 0.5. His last-10 rate is 0.27 runs/game (drivers[0].input), so Poisson vs 0.5 makes under the more likely side at p_hit 0.76. Sufficiency 0.45 means that rate is about half player-observed (10 games vs k=12) — the interval is wide because of that. Conviction 0.24 is |0.76 − 0.5| × 2 × 0.45: a strong lean on a modest sample, so it ranks in the middle of the board rather than the top. DraftKings posts −453 on that under — the market price for the side the model picked. research is null, so no news overlay has been applied.

How to read this same object: [/docs/understanding-odds#forecasts](/docs/understanding-odds#forecasts).

<!-- #worked -->

## REST + MCP

| Surface | REST | MCP | Credits |
| --- | --- | --- | --- |
| Daily board | [GET /v1/intelligence/forecasts](/docs/reference#intelligence-forecasts) | list_forecasts | 1 |
| Per-event catalog | [GET /v1/events/{id}/intelligence](/docs/reference#event-intelligence) → forecasts[] | get_intelligence | 1 |
| Live progress | [GET /v1/events/{id}/player-props](/docs/reference#event-player-props) | get_player_props | 1 when lines exist |

Playground: [#list_forecasts](/playground#list_forecasts). Recipe: [Read a forecasted prop wager](/docs/guides#recipe-forecasted-prop). list_forecasts accepts sport=tennis and an optional market filter (h2h, spreads, or totals).

<!-- #endpoints -->
