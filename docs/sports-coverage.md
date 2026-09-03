# Lumify Sports Coverage

> Canonical URL: https://lumify.ai/docs/sports-coverage.md
> HTML twin: https://lumify.ai/docs/sports-coverage

What is live on each sport today — events, stats, odds, splits, and intelligence — with links to the docs for each surface.

<!-- Auto-generated from api/templates/public/docs_sports_coverage.html by scripts/html_docs_to_md.py — edit the HTML template, then re-run. -->

# Sports Coverage

What is live on each sport today. Surface names in the left column link to the docs for that endpoint.

> **Tip:** For agents: the machine-readable twin of this page is [/docs/sports-coverage.md](/docs/sports-coverage.md).

## Sport × surface

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

<!-- #matrix -->

## Notes

| Note | What it means |
| --- | --- |
| Soccer Some | Probability, Price, and main-line EV (h2h / spreads / totals) are MLS + EPL + La Liga + Serie A + Bundesliga + Ligue 1. Team totals and first-half odds ingest the same Pinnacle v2 leagues. Other club soccer is Events / Stats / Game odds only. |
| Tennis intelligence | ATP/WTA singles. Stage 1 is moneyline + spreads; no totals on the predictive payload or the EV scan (market=totals returns 400). Doubles and qualifying stay commodity (no bets[]). |
| Main-line EV | GET /v1/intelligence/ev / MCP list_ev ranks a sharp-fair price gap on moneyline (default), spreads, and totals. Forecasts are a separate ungated model: player props on team sports, tennis main-line (moneyline, spreads, and totals). Soccer has no forecast board. |
| Match context | Search-backed match_overview + top-level rationale[] written before kickoff on every event sport. The request path only reads the stored row. Context, not a pick. |
| Period odds | NFL / NCAAF / NBA / NCAAB / soccer first half; MLB first five; tennis first set. NHL has no period surface. |
| Team totals | NFL, NCAAF, MLB, and soccer on [team totals](/docs/reference#event-team-props). Not the same as player props or game totals. |
| Prediction markets | Fanatics Markets, Kalshi, and Polymarket 0–1 game-line probabilities on [prediction markets](/docs/reference#event-prediction-markets). Not sportsbook odds. NCAAB is not on this surface. |
| Splits | NBA, NHL, MLB, NFL, NCAAF, NCAAB. Soccer and tennis stay 400 upstream. NCAAB is often available: false off-season — empty slate, not a sport gate. |
| Still closed | Soccer / tennis player props. NHL period odds. NBA / NHL / NCAAB team totals. NBA / NCAAB / NHL Probability & Price. |

<!-- #notes -->

## League slugs

Pass these on ?sport= and ?league= when listing events. Tennis uses tour slugs; soccer intelligence is league-gated as in the matrix above.

| Sport | League slug | Type |
| --- | --- | --- |
| NFL | nfl | Team league |
| NBA | nba | Team league |
| MLB | mlb | Team league |
| NHL | nhl | Team league |
| NCAAF | ncaaf | Team league |
| NCAAB | ncaab | Team league |
| Tennis | atp, wta | Individual tour |
| Soccer | mls | Team league — Probability & Price |
| Soccer | epl, la_liga, serie_a, bundesliga, ligue_1 | Team league — Probability & Price |
| Soccer | ucl | Tournament — Events / Stats / Game odds only |

<!-- #leagues -->
