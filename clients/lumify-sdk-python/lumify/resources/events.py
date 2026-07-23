from __future__ import annotations

from typing import Any, Iterator, List, Optional

from .._transport import LumifyClient
from ..models import (
    BatchEventsResponse,
    EventDetail,
    EventListResponse,
    IntelligenceResponse,
    NLQueryResponse,
    OddsHistoryResponse,
    OddsResponse,
    ScoreResponse,
    SplitsResponse,
)
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
    ) -> EventDetail:
        """GET /v1/events/{id} — full event. ``include_odds`` /
        ``include_intelligence`` inline those payloads (each +1 credit when
        available)."""
        return self._client.get(
            "/v1/events/%d" % event_id,
            query={
                "include_odds": include_odds,
                "include_intelligence": include_intelligence,
                "bookmaker": bookmaker,
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
        call, and cost nothing."""
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

    def odds(self, event_id: int, *, bookmaker: Optional[str] = None) -> OddsResponse:
        """GET /v1/events/{id}/odds. ``available: false`` (odds not yet posted)
        is not charged — ``credits_used`` is 0 (read via ``get_meta()``)."""
        return self._client.get(
            "/v1/events/%d/odds" % event_id, query={"bookmaker": bookmaker}
        )

    def odds_history(
        self, event_id: int, *, bookmaker: Optional[str] = None, limit: Optional[int] = None
    ) -> OddsHistoryResponse:
        """GET /v1/events/{id}/odds/history — line-movement history."""
        return self._client.get(
            "/v1/events/%d/odds/history" % event_id,
            query={"bookmaker": bookmaker, "limit": limit},
        )

    def splits(self, event_id: int) -> SplitsResponse:
        """GET /v1/events/{id}/splits — public betting splits (tickets % vs. money %)."""
        return self._client.get("/v1/events/%d/splits" % event_id)

    def intelligence(
        self, event_id: int, *, bookmaker: Optional[str] = None
    ) -> IntelligenceResponse:
        """GET /v1/events/{id}/intelligence — AI bet intelligence."""
        return self._client.get(
            "/v1/events/%d/intelligence" % event_id, query={"bookmaker": bookmaker}
        )

    def stream(
        self, event_id: int, *, connect_timeout: Optional[float] = None
    ) -> Iterator[ScoreStreamEvent]:
        """GET /v1/events/{id}/stream (SSE) — iterate live score updates,
        emitted only on change, until the event finishes."""
        return stream_scores(self._client, event_id, connect_timeout=connect_timeout)
