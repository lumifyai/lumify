from __future__ import annotations

from typing import Optional

from ._transport import DEFAULT_BASE_URL, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT, LumifyClient, Transport
from .resources import (
    AgentResource,
    EstimateResource,
    EventsResource,
    PlayersResource,
    SeasonsResource,
    SportsResource,
    TeamsResource,
    WebhooksResource,
)


class Lumify:
    """The Lumify SDK entry point.

    Example::

        from lumify import Lumify

        client = Lumify(api_key=os.environ["LUMIFY_API_KEY"])
        sports = client.sports.list()
        event = client.events.get(12345, include_odds=True)
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: Optional[Transport] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self._client = LumifyClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            transport=transport,
            user_agent=user_agent,
        )
        self.sports = SportsResource(self._client)
        self.seasons = SeasonsResource(self._client)
        self.events = EventsResource(self._client)
        self.teams = TeamsResource(self._client)
        self.players = PlayersResource(self._client)
        self.webhooks = WebhooksResource(self._client)
        self.agent = AgentResource(self._client)
        self.estimate = EstimateResource(self._client)

    @property
    def base_url(self) -> str:
        """The configured API origin (default ``https://lumify.ai``)."""
        return self._client.base_url
