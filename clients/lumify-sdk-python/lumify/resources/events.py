from __future__ import annotations

from typing import Any, Iterator, List, Optional, Union

from .._transport import LumifyClient
from ..models import (
    BatchEventsResponse,
    EventDetail,
    EventListResponse,
    ForecastsResponse,
    IntelligenceEvResponse,
    IntelligenceResponse,
    MlbStatsResponse,
    NflStatsResponse,
    NLQueryResponse,
    OddsHistoryResponse,
    OddsResponse,
    PeriodOddsResponse,
    PlayerPropsResponse,
    PredictionMarketsResponse,
    ScoreResponse,
    SplitsResponse,
    TeamPropsResponse,
    StatsResponse,
    TennisStatsResponse,
)

EventStatsResponse = Union[StatsResponse, MlbStatsResponse, TennisStatsResponse, NflStatsResponse]
from ..pagination import iterate_items, paginate
from ..sse import ScoreStreamEvent, stream_scores


class EventsResource:
    def __init__(self, client: LumifyClient) -> None:
        self._client = client

    def list(
        self,
        *,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        status: Optional[str] = None,
        date: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        season_id: Optional[int] = None,
        team_id: Optional[int] = None,
        after_id: Optional[int] = None,
        limit: Optional[int] = None,
        include_scores: Optional[bool] = None,
        has_recommend: Optional[bool] = None,
        sort: Optional[str] = None,
    ) -> EventListResponse:
        """GET /v1/events — cursor-paginated (``after_id``/``limit``;
        ``next_after_id`` when more remain). ``from_`` maps to the ``from``
        query param (a Python keyword). Pass ``team_id`` to filter to a
        team's schedule (resolve ids via :meth:`TeamsResource.list`)."""
        return self._client.get(
            "/v1/events",
            query={
                "sport": sport,
                "league": league,
                "status": status,
                "date": date,
                "from": from_,
                "to": to,
                "season_id": season_id,
                "team_id": team_id,
                "after_id": after_id,
                "limit": limit,
                "include_scores": include_scores,
                "has_recommend": has_recommend,
                "sort": sort,
            },
        )

    def paginate(
        self, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[EventListResponse]:
        """Iterate every page of :meth:`list` for the given filters."""
        return paginate(
            lambda after_id, lim: self.list(after_id=after_id, limit=lim, **filters),
            limit=limit,
            max_pages=max_pages,
        )

    def iterate(
        self, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[Any]:
        """Iterate every event matching the filters, across all pages. Events
        pages hold items under ``events`` (not ``data``)."""
        return iterate_items(
            lambda after_id, lim: self.list(after_id=after_id, limit=lim, **filters),
            items_key="events",
            limit=limit,
            max_pages=max_pages,
        )

    def get(
        self,
        event_id: int,
        *,
        include_odds: Optional[bool] = None,
        include_intelligence: Optional[bool] = None,
        bookmaker: Optional[str] = None,
        include_alts: Optional[bool] = None,
    ) -> EventDetail:
        """GET /v1/events/{id} — full event. ``include_odds`` inlines current
        odds scoped by ``bookmaker`` (default: pinnacle). ``include_intelligence``
        inlines bet intelligence. Includes do not add credits (1 credit for the
        call). ``include_alts`` includes alternate spread/total rungs on the
        inlined odds (mains only by default)."""
        return self._client.get(
            "/v1/events/%d" % event_id,
            query={
                "include_odds": include_odds,
                "include_intelligence": include_intelligence,
                "bookmaker": bookmaker,
                "include_alts": include_alts,
            },
        )

    def batch_get(
        self,
        event_ids: List[int],
        *,
        include_odds: Optional[bool] = None,
        include_intelligence: Optional[bool] = None,
        bookmaker: Optional[str] = None,
    ) -> BatchEventsResponse:
        """POST /v1/events/batch — fetch multiple events by id in one
        round-trip. Max 25 ids per call; duplicates are billed once. Ids that
        don't exist are returned under ``not_found`` rather than failing the
        call, and cost nothing. ``include_odds`` is scoped by ``bookmaker``
        (default: pinnacle). Includes do not add credits — each found event
        stays 1 credit."""
        return self._client.post(
            "/v1/events/batch",
            body={
                "event_ids": event_ids,
                "include_odds": include_odds,
                "include_intelligence": include_intelligence,
                "bookmaker": bookmaker,
            },
        )

    def query(self, text: str, *, limit: Optional[int] = None) -> NLQueryResponse:
        """POST /v1/query — search events with a natural-language query
        instead of structured filters, e.g. ``"live nfl games today"``. A
        small rule-based mapper (not an LLM call); the response includes the
        parsed filters (``interpreted``), the equivalent ``GET /v1/events``
        call, and any words that didn't map to a filter
        (``unrecognized_terms``). Costs 1 credit, same as :meth:`list` —
        interpreting the query text is free."""
        return self._client.post("/v1/query", body={"query": text, "limit": limit})

    def score(self, event_id: int) -> ScoreResponse:
        """GET /v1/events/{id}/score — live score snapshot."""
        return self._client.get("/v1/events/%d/score" % event_id)

    def odds(
        self,
        event_id: int,
        *,
        bookmaker: Optional[str] = None,
        include_alts: Optional[bool] = None,
    ) -> OddsResponse:
        """GET /v1/events/{id}/odds. Default is main lines. Pass
        ``include_alts=True`` for alternate spread/total rungs.
        ``available: false`` (odds not yet posted) is not charged —
        ``credits_used`` is 0 (read via ``get_meta()``)."""
        return self._client.get(
            "/v1/events/%d/odds" % event_id,
            query={"bookmaker": bookmaker, "include_alts": include_alts},
        )

    def odds_history(
        self, event_id: int, *, bookmaker: Optional[str] = None, limit: Optional[int] = None
    ) -> OddsHistoryResponse:
        """GET /v1/events/{id}/odds/history — line-movement history."""
        return self._client.get(
            "/v1/events/%d/odds/history" % event_id,
            query={"bookmaker": bookmaker, "limit": limit},
        )

    def stats(self, event_id: int) -> EventStatsResponse:
        """GET /v1/events/{id}/stats — raw, deterministic team/player/match
        statistics (Data layer). Sport-specific shapes: soccer/MLB/NFL use
        ``teams.home/away``; tennis uses ``players.player_1/player_2`` +
        ``match``. No market/odds data — use ``odds()`` for that. No
        scoring/confidence — see ``intelligence()``. Soccer, MLB, tennis
        (singles), and NFL Stage-1 today. ``available: false`` is not charged —
        ``credits_used`` is 0 (read via ``get_meta()``).
        """
        return self._client.get("/v1/events/%d/stats" % event_id)

    def player_props(self, event_id: int) -> PlayerPropsResponse:
        """GET /v1/events/{id}/player-props — NFL/NCAAF/NBA/NCAAB/NHL/MLB player-prop
        mains plus live box progress. ``available: false`` is not charged —
        ``credits_used`` is 0 (read via ``get_meta()``).
        """
        return self._client.get("/v1/events/%d/player-props" % event_id)

    def team_props(self, event_id: int) -> TeamPropsResponse:
        """GET /v1/events/{id}/team-props — NFL/NCAAF/MLB/soccer team-total mains
        plus this-event team score. ``available: false`` is not charged.
        """
        return self._client.get("/v1/events/%d/team-props" % event_id)

    def prediction_markets(self, event_id: int) -> PredictionMarketsResponse:
        """GET /v1/events/{id}/prediction-markets — Fanatics Markets / Kalshi /
        Polymarket 0–1 game-line probabilities. Not sportsbook odds.
        ``available: false`` is not charged.
        """
        return self._client.get("/v1/events/%d/prediction-markets" % event_id)

    def period_odds(self, event_id: int) -> PeriodOddsResponse:
        """GET /v1/events/{id}/period-odds — first-half / first-five / first-set
        mains plus this-event period scores. ``available: false`` is not charged.
        """
        return self._client.get("/v1/events/%d/period-odds" % event_id)

    def splits(self, event_id: int) -> SplitsResponse:
        """GET /v1/events/{id}/splits — public betting splits (tickets % vs. money %)."""
        return self._client.get("/v1/events/%d/splits" % event_id)

    def intelligence(
        self, event_id: int, *, bookmaker: Optional[str] = None
    ) -> IntelligenceResponse:
        """GET /v1/events/{id}/intelligence — AI bet intelligence.

        ``bets[].signals`` keys (``signal_research``, ``signal_serve_rtn``, etc.)
        are shared DB columns that mean different things per sport (e.g.
        ``signal_serve_rtn`` is tennis Serve/Return but soccer Attack/Defense
        Edge). For NFL and NCAAF, ``bets[].signals._labels`` maps each
        present ``signal_*`` key to its sport-specific human-readable label;
        omitted on the probability surface (MLB, tennis, MLS). Prefer
        ``rationale``/``attribution`` over raw ``signal_*`` keys when you just
        need prose, not the underlying scores.
        """
        return self._client.get(
            "/v1/events/%d/intelligence" % event_id, query={"bookmaker": bookmaker}
        )

    def list_ev(
        self,
        *,
        sport: str,
        league: Optional[str] = None,
        market: Optional[str] = None,
        min_ev: Optional[float] = None,
        book: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> IntelligenceEvResponse:
        """GET /v1/intelligence/ev — Beta main-line EV scan for a
        predictive-framework sport (soccer, mlb, tennis, nfl, ncaaf).
        ``market`` is ``h2h`` (default), ``spreads``, or ``totals``.
        Tennis totals return 400."""
        return self._client.get(
            "/v1/intelligence/ev",
            query={
                "sport": sport,
                "league": league,
                "market": market,
                "min_ev": min_ev,
                "book": book,
                "limit": limit,
            },
        )

    def list_forecasts(
        self,
        *,
        sport: str,
        date: Optional[str] = None,
        market: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> ForecastsResponse:
        """GET /v1/intelligence/forecasts — daily board of forecasted
        wagers: a model prediction, not a beat-the-market claim. Player
        props (mlb, ncaaf, nfl, nba, ncaab, nhl) plus tennis main-line:
        moneyline (``bet_type`` ``ML_P1``/``ML_P2``), game handicap
        (``SPREAD_P1``/``SPREAD_P2``), and total games (``OVER``/
        ``UNDER``). ``market`` (``h2h``, ``spreads``, or ``totals``)
        filters a sport's main-line rows."""
        return self._client.get(
            "/v1/intelligence/forecasts",
            query={"sport": sport, "date": date, "market": market, "limit": limit},
        )

    def stream(
        self, event_id: int, *, connect_timeout: Optional[float] = None
    ) -> Iterator[ScoreStreamEvent]:
        """GET /v1/events/{id}/stream (SSE) — iterate live score updates,
        emitted only on change, until the event finishes."""
        return stream_scores(self._client, event_id, connect_timeout=connect_timeout)
