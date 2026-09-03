from __future__ import annotations

from typing import Any, Iterator, Optional

from .._transport import LumifyClient
from ..models import Player, PlayerEventsResponse, PlayersListResponse
from ..pagination import iterate_items, paginate


class PlayersResource:
    def __init__(self, client: LumifyClient) -> None:
        self._client = client

    def list(
        self,
        *,
        sport: Optional[str] = None,
        q: Optional[str] = None,
        country: Optional[str] = None,
        active: Optional[bool] = None,
        ranked: Optional[bool] = None,
        after_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PlayersListResponse:
        """GET /v1/players — cursor-paginated."""
        return self._client.get(
            "/v1/players",
            query={
                "sport": sport,
                "q": q,
                "country": country,
                "active": active,
                "ranked": ranked,
                "after_id": after_id,
                "limit": limit,
            },
        )

    def paginate(
        self, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[PlayersListResponse]:
        return paginate(
            lambda after_id, lim: self.list(after_id=after_id, limit=lim, **filters),
            limit=limit,
            max_pages=max_pages,
        )

    def iterate(
        self, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[Any]:
        return iterate_items(
            lambda after_id, lim: self.list(after_id=after_id, limit=lim, **filters),
            items_key="data",
            limit=limit,
            max_pages=max_pages,
        )

    def get(self, player_id: int) -> Player:
        """GET /v1/players/{id}."""
        return self._client.get("/v1/players/%d" % player_id)

    def events(
        self,
        player_id: int,
        *,
        status: Optional[str] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        after_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> PlayerEventsResponse:
        """GET /v1/players/{id}/events — cursor-paginated schedule/results.
        ``from_`` maps to the ``from`` query param (a Python keyword)."""
        return self._client.get(
            "/v1/players/%d/events" % player_id,
            query={
                "status": status,
                "from": from_,
                "to": to,
                "after_id": after_id,
                "limit": limit,
            },
        )

    def paginate_events(
        self, player_id: int, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[PlayerEventsResponse]:
        return paginate(
            lambda after_id, lim: self.events(
                player_id, after_id=after_id, limit=lim, **filters
            ),
            limit=limit,
            max_pages=max_pages,
        )
