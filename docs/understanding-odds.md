# Understanding Odds & Probability

> Canonical URL: https://lumify.ai/docs/understanding-odds.md
> HTML twin: https://lumify.ai/docs/understanding-odds

How to read a Lumify intelligence response — using a real Twins vs. Orioles moneyline, then a player-prop forecast. Terms → fields: https://lumify.ai/docs/glossary.md. Field catalog and model detail: https://lumify.ai/docs/forecasts.md. Inspector: https://lumify.ai/docs/reference.md#event-intelligence.

**The book's cut.** Sportsbooks don't post even prices. They pad each side so the two (or three) outcomes add up to more than 100% — that extra slice is the vig, or juice. Two `-110` sides look like about 52% each, or 105% together; the extra 5% is the book's cut. Lumify already takes that cut out of every `probability` on this page, so those numbers sum to 100%.

The rest of this page walks the highlighted wager below — the Minnesota Twins moneyline on Twins vs. Orioles, from `GET /v1/events/17386/intelligence`.

**Example wager** `GET /v1/events/17386/intelligence`

- Aug 12, 2026 · 1:40 p.m. ET · MLB · Moneyline
- **Minnesota Twins** −105 (Pinnacle) — this wager
- Baltimore Orioles −103 (Pinnacle)
- Fair price −101. Closest shop: FanDuel −104.

API payload:

```json
{
  "bet_type": "ML_P1",
  "player_name": "Minnesota Twins",
  "probability": 0.50236,
  "fair_price": -101,
  "market": { "price": -105, "book": "pinnacle" },
  "edge": null,
  "tier": null,
  "fair": {
    "probability": 0.50699,
    "books": ["circa", "pinnacle"],
    "n_books": 2,
    "is_consensus": true
  },
  "edges_by_book": {
    "fanduel": -0.00551,
    "hardrock": -0.01016,
    "draftkings": -0.01471,
    "caesars": -0.03626
  },
  "best": { "book": "fanduel", "price": -104, "edge": -0.00551 }
}
```

## What "fair" means

Every bet carries **two different "fair" numbers**. They look similar and are easy to mix up:

- **This book's no-cut price.** `market` is the posted line from one book — `market.book` is who posted it (here, Pinnacle) and `market.price` is the number they posted (`-105`). `probability` is that same line with the book's cut removed. `fair_price` is that chance written as American odds, so you can put it next to `-105`.
- **The sharp consensus.** `fair` is a second estimate from the sharpest book or books available (Pinnacle alone, or Pinnacle plus Circa on MLB). This is the yardstick retail books are compared against in the next section.

The two are usually close, but they can come from different books. On this Twins moneyline:

| | Value | In plain terms |
|---|---|---|
| `probability` | `0.50236` | About 50.2% after removing Pinnacle's cut from their `-105` |
| `fair.probability` | `0.50699` | About 50.7% from Circa and Pinnacle together |

Use `probability` / `fair_price` when you care about the book you're looking at. Use `fair` when you want to shop across books.

## Fair price as odds

A 50.2% chance is almost a coin flip. In American odds that's about `-101` — that's `fair_price` on this Twins moneyline. Pinnacle posted `-105`. The four-cent difference is this book's cut on this side: you have to risk a little more than the no-cut number.

Favorites (more than 50%) show as a negative number like `-101`. Underdogs (less than 50%) show as a plus number like `+110`. Same chance, two ways of writing it — percent vs. the odds board.

That `-101` vs. `-105` gap is only about this one book. To see how FanDuel or DraftKings sit against the sharp consensus, use the next section.

## Comparing books

Once you have the sharp consensus, you can ask a simple shopping question: *how does each retail book's current price sit against that number?* That's `edges_by_book`.

A **positive** number means that book is offering a better price than the consensus. A **negative** number means you'd be paying more than the consensus says the side is worth. On this Twins moneyline every retail book is slightly negative — the sharp books were tight that day, so nobody actually beat them. `best` is the closest shop (the smallest gap):

| Book | Vs. the consensus |
|---|---|
| FanDuel | `-0.00551` ← closest (`best`), posted `-104` |
| Hard Rock | `-0.01016` |
| DraftKings | `-0.01471` |
| Caesars | `-0.03626` |

`best.quote_age_seconds` is how old that book's price was when we published. A gap on a seconds-old quote is more useful than the same gap on a quote from several minutes ago.

## When a line looks better than fair

The comparison above is a price gap vs. the sharp books. When that gap is *positive* on a main line (moneyline, spread, or total), Lumify also writes it as a percent (`ev_pct`) and a suggested bankroll fraction (`kelly_fraction`) so it's easy to display. That's `ev` — a Beta field. Tennis totals stay unpublished.

On this Twins moneyline every retail book is worse than the consensus, so `ev` is `null`. If FanDuel were 3.1% better than fair at `+155`, that same ticket would look like this:

**Hypothetical** If FanDuel beat the consensus

- Minnesota Twins · Moneyline · FanDuel **+155**
- `ev_pct` 3.1 · `kelly_fraction` 0.02 of bankroll. Quote was 4 minutes old.

API payload:

```json
{
  "beta": true,
  "book": "fanduel",
  "price": 155,
  "ev_pct": 3.1,
  "kelly_fraction": 0.02,
  "quote_age_seconds": 240.0,
  "n_books": 1
}
```

This only appears when we have a fair number (Pinnacle alone is enough), and only when the gap is positive and not huge (over 25% is dropped). Some MLB moneyline books are skipped and we walk to the next one. Scan a sport with [GET /v1/intelligence/ev](/docs/reference#intelligence-ev) (`market=h2h|spreads|totals`; MCP `list_ev`). Tennis totals return 400.

## Reading a forecasted wager

The moneyline / spread / total bets above live in `bets` — a gated beat-the-market claim. `forecasts[]` is a separate list on the same response: an ungated model probability. Player props (MLB, NFL, NCAAF, NBA, NCAAB, NHL) plus tennis main-line (moneyline, spreads, totals). The daily board is [GET /v1/intelligence/forecasts](/docs/reference#intelligence-forecasts) (MCP `list_forecasts`). Same object either way. Can show up even when game-level intelligence isn't ready yet.

Scan main lines by sharp-fair price gap with `list_ev`. Scan high-probability forecasts with `list_forecasts` (ranked by how strongly the model leans). Soccer has no forecast board.

The table below reads this one ticket — Ben Rortvedt, under 0.5 runs:

**Example wager** `forecasts[]` · `list_forecasts`

- Total Runs — Ben Rortvedt · MLB · Under
- Line 0.5 · Over — · **Under −453** (DraftKings)
- Model pick: under 0.5 · about 76% to hit · emerging. The field table is for this ticket.

API payload:

```json
{
  "player": "Ben Rortvedt",
  "market": "runs",
  "line": 0.5,
  "side": "under",
  "p_hit": 0.7617,
  "interval": [0.6982, 0.8252],
  "sufficiency": 0.4545,
  "conviction": 0.2379,
  "reliability": "emerging",
  "books": { "draftkings": -453 },
  "drivers": [{
    "id": "player.l10_rate",
    "input": 0.27,
    "effect": 0.082,
    "direction": "up"
  }],
  "research": null
}
```

| Field | How to read it here |
|-------|---------------------|
| `side` + `line` | The model has him at about 0.27 runs per game. Against a 0.5 line, `under` is the more likely side. When both sides of a main line are posted, the model always picks one. |
| `p_hit` | About a 76% chance that under 0.5 hits, from the player's recent rate — not from a book's posted price. |
| `sufficiency` | About 45% of that rate comes from his own last 10 games; the rest is a league starting point. The wager still ships — this tells you how much is earned from his own box scores. |
| `interval` | A band around 76% (about 70–83%). Wider when we have fewer of his own games. A stated range, not a formal confidence interval. |
| `conviction` | How strongly the model leans, after sample size. A big lean on a short sample ranks in the middle of the board; a milder lean on a long sample can rank higher. The daily slate is sorted by this. |
| `drivers` | 0.27 runs/game is the rate that went into the forecast. `direction` up means that rate helps the under versus a typical player on the same 0.5 line. |
| `books` | DraftKings has this under at `-453` — the posted price on the side the model picked. |
| `research` | `null` here — no extra write-up yet. When present on a high-probability wager (`p_hit` ≥ 0.80), `note` is the why; it can nudge the chance by a little (at most three percentage points) without changing the side. |
| `reliability` | `emerging` on every forecast for now. It will step up as we score more history for that sport and market. |

How + field catalog: [/docs/forecasts](/docs/forecasts). Inspector: [API Reference → List forecasted wagers](/docs/reference#intelligence-forecasts).

## Matchup context

Above the bets sit two event-level fields. `match_overview` is a short preview of the game. `rationale` is a list of factual chips — injuries, recent form, lineup or availability news, what to watch. Either can be missing when we don't have them yet. They describe the matchup; they don't rank or price a side. Queries are sport-shaped (tennis does not invent starting pitchers).

## Full example

The full `GET /v1/events/17386/intelligence` response these examples come from, with notes on the first bet:

```json
{
  "event_id": 17386,
  "available": true,
  "odds_source": "pinnacle",
  "sport": "mlb",
  "league": "mlb",
  "players": {
    "home": { "name": "Minnesota Twins", "player_id": null, "team_id": 72 },
    "away": { "name": "Baltimore Orioles", "player_id": null, "team_id": 63 }
  },
  "has_recommend": false,
  "match_overview": "The Minnesota Twins (59-61) host the Baltimore Orioles (57-62) on August 12, 2026, at Target Field in a series rubber match. Both teams are below .500 and competing in the AL Central and AL East respectively. The game is scheduled for 1:40 p.m. ET with an over/under set at 8.5.", // matchup preview
  "rationale": [                          // form, pitchers, what to watch
    "Twins RHP Zebby Matthews (5-8, 5.23 ERA, 73 SO) opposes Orioles RHP Shane Baz (4-11, 3.76 ERA, 120 SO); Matthews' team is 8-7 ATS in his starts while Baz's starts yield 10-12 ATS for Baltimore.",
    "Minnesota is 32-12 in games when not allowing a home run; Orioles are 4-6 in their last 10 games with a .219 batting average.",
    "Twins are 31-28 at home; Orioles are 26-32 as moneyline underdogs this season.",
    "Series context shows Baltimore leads the season head-to-head 7-3 in wins, 4-6 in over/under outcomes."
  ],
  "intelligence_updated_at": "2026-08-12T14:42:19Z",
  "bets": [
    {
      "bet_type": "ML_P1",
      "player_role": "home",
      "player_id": null,
      "team_id": 72,
      "player_name": "Minnesota Twins",
      "probability": 0.50236,              // ~50.2% after removing Pinnacle's cut
      "interval": [0.42902, 0.57569],
      "fair_price": -101,                  // that same 50.2% as American odds
      "market": { "price": -105, "line": null, "book": "pinnacle" },
      "edge": null,
      "tier": null,
      "fair": {
        "probability": 0.50699,            // sharp consensus (Circa + Pinnacle) — a different source
        "books": ["circa", "pinnacle"],
        "n_books": 2,
        "is_consensus": true
      },
      "edges_by_book": {                   // each retail book vs the sharp consensus
        "caesars": -0.03625661385006673,
        "fanduel": -0.005513797120894615,
        "hardrock": -0.01015658985142276,
        "draftkings": -0.014711782719110666
      },
      "best": {                            // closest shop
        "book": "fanduel",
        "price": -104,
        "edge": -0.00551,
        "quote_age_seconds": 717.102774
      },
      "ev": null,                          // null here — no retail book beat the consensus
      "computed_at": "2026-08-12T14:42:19Z"
    },
    {
      "bet_type": "ML_P2",
      "player_role": "away",
      "player_id": null,
      "team_id": 63,
      "player_name": "Baltimore Orioles",
      "probability": 0.49764,
      "interval": [0.42431, 0.57098],
      "fair_price": 101,
      "market": { "price": -103, "line": null, "book": "pinnacle" },
      "edge": null,
      "tier": null,
      "fair": {
        "probability": 0.49301,
        "books": ["circa", "pinnacle"],
        "n_books": 2,
        "is_consensus": true
      },
      "edges_by_book": {
        "caesars": -0.009055862009059834,
        "fanduel": -0.03294774134064382,
        "hardrock": -0.037462457767625024,
        "draftkings": -0.018867190107979992
      },
      "best": { "book": "caesars", "price": 101, "edge": -0.00906, "quote_age_seconds": 717.106364 },
      "computed_at": "2026-08-12T14:42:19Z"
    },
    {
      "bet_type": "OVER",
      "player_role": null,
      "player_id": null,
      "team_id": null,
      "player_name": null,
      "probability": 0.52598,
      "interval": [0.44609, 0.60588],
      "fair_price": -111,
      "market": { "price": -118, "line": 8.5, "book": "pinnacle" },
      "edge": null,
      "tier": null,
      "fair": {
        "probability": 0.513,
        "books": ["circa", "pinnacle"],
        "n_books": 2,
        "is_consensus": true
      },
      "edges_by_book": {
        "betmgm": 0.02600147666367647,
        "caesars": 0.02600147666367647,
        "draftkings": 0.03113148404699473
      },
      "best": { "book": "draftkings", "price": 101, "edge": 0.03113, "quote_age_seconds": 717.111229 },
      "computed_at": "2026-08-12T14:42:19Z"
    },
    {
      "bet_type": "UNDER",
      "player_role": null,
      "player_id": null,
      "team_id": null,
      "player_name": null,
      "probability": 0.47402,
      "interval": [0.39412, 0.55391],
      "fair_price": 111,
      "market": { "price": 105, "line": 8.5, "book": "pinnacle" },
      "edge": null,
      "tier": null,
      "fair": {
        "probability": 0.487,
        "books": ["circa", "pinnacle"],
        "n_books": 2,
        "is_consensus": true
      },
      "edges_by_book": {
        "betmgm": -0.1071680202750368,
        "caesars": -0.1071680202750368,
        "draftkings": -0.11382101565301717
      },
      "best": { "book": "caesars", "price": -120, "edge": -0.10717, "quote_age_seconds": 717.106364 },
      "computed_at": "2026-08-12T14:42:19Z"
    }
  ]
}
```

For the complete field reference (types, nullability, every bet token per sport), see https://lumify.ai/docs/reference.md#event-intelligence.
