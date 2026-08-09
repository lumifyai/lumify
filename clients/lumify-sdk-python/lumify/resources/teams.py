from __future__ import annotations

from typing import Any, Iterator, Optional

from .._transport import LumifyClient
from ..models import Team, TeamsListResponse
from ..pagination import iterate_items, paginate


class TeamsResource:
    def __init__(self, client: LumifyClient) -> None:
        self._client = client

    def list(
        self,
        *,
        sport: Optional[str] = None,
        league: Optional[str] = None,
        conference: Optional[str] = None,
        division: Optional[str] = None,
        country: Optional[str] = None,
        q: Optional[str] = None,
        active: Optional[bool] = None,
        after_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> TeamsListResponse:
        """GET /v1/teams — cursor-paginated."""
        return self._client.get(
            "/v1/teams",
            query={
                "sport": sport,
                "league": league,
                "conference": conference,
                "division": division,
                "country": country,
                "q": q,
                "active": active,
                "after_id": after_id,
                "limit": limit,
            },
        )

    def paginate(
        self, *, limit: int = 25, max_pages: int = 1000, **filters: Any
    ) -> Iterator[TeamsListResponse]:
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

    def get(self, team_id: int) -> Team:
        """GET /v1/teams/{id}."""
        return self._client.get("/v1/teams/%d" % team_id)
