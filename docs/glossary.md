# Glossary

> Canonical URL: https://lumify.ai/docs/glossary.md
> HTML twin: https://lumify.ai/docs/glossary

Betting English mapped to Lumify JSON. For a worked wager, see
[Understanding Odds](https://lumify.ai/docs/understanding-odds).

## Terms → fields

| Term | In English | Lumify field |
|------|------------|--------------|
| Juice / vig | The book's cut. Two `−110` sides add up to more than 100%. | Already stripped from `probability` (sides sum to 100%). Compare posted `market.price` to `fair_price`. |
| American odds | `−150` favorite / `+130` underdog. Negative means you risk more than you win. | `fair_price`, `market.price`, and book `price` on odds / splits. |
| Moneyline | Which side wins the game (no point handicap). | `bets[].bet_type` `ML_*` on intelligence; `moneyline` on `GET /odds`. |
| Spread | Point handicap. Favorite must win by more than the number. | `bets[].bet_type` `SPREAD_*`; odds `spread` + `line`. |
| Total (over/under) | Combined score over or under a number. | `bets[].bet_type` `OVER` / `UNDER`; odds `total`. |
| Line | The number on a spread or total (e.g. `−1.5`, `7.0`). | `market.line` on intelligence; `line` on odds and splits. |
| Tickets / bets % | Share of bets by *count* — what the public is on. | `consensus[market][side].bets_pct` on `GET /splits`. |
| Handle | Share of bets by *money*. A gap vs tickets often means larger (sharp) bets. | `consensus[market][side].handle_pct` on `GET /splits`. |
| Fair / no-vig | The price with the book's cut removed — or the consensus across books. | `probability` + `fair_price` (this book). `fair` is the cross-book consensus. |
| Price gap / edge | How a book's posted price compares to consensus. Positive = better than consensus. | `edges_by_book`, `best`. Main-line only (moneyline, spreads, totals): `ev` (Beta). |
| Available | Whether we have computed data for this event yet. | `available: false` → empty payload, **0 credits**. Poll again or pick another event. |

## Go deeper

- [Understanding Odds](https://lumify.ai/docs/understanding-odds) — walk a Twins moneyline and a player-prop ticket
- [Cheat sheet](https://lumify.ai/docs/cheat-sheet) — auth, envelope, hero query
- [Odds reference](https://lumify.ai/docs/reference#event-odds) · [Splits](https://lumify.ai/docs/reference#event-splits) · [Intelligence](https://lumify.ai/docs/reference#event-intelligence)
