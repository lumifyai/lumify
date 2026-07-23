from __future__ import annotations

from typing import Optional

from ..._async_transport import AsyncLumifyClient
from ...models import SeasonsListResponse, SportsListResponse


class AsyncSportsResource:
    def __init__(self, client: AsyncLumifyClient) -> None:
        self._client = client

    async def list(self, *, active_only: Optional[bool] = None) -> SportsListResponse:
        """GET /v1/sports — every sport Lumify covers (mlb, nfl, nba, nhl,
        tennis, soccer, ncaaf, ncaab, ...)."""
        return await self._client.get("/v1/sports", query={"active_only": active_only})


class AsyncSeasonsResource:
    def __init__(self, client: AsyncLumifyClient) -> None:
        self._client = client

    async def list(
        self,
        *,
        sport: Optional[str] = None,
        current_only: Optional[bool] = None,
    ) -> SeasonsListResponse:
        """GET /v1/seasons — seasons across sports/leagues."""
        return await self._client.get(
            "/v1/seasons", query={"sport": sport, "current_only": current_only}
        )
