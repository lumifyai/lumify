from __future__ import annotations

from typing import Optional

from .._async_transport import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncLumifyClient,
    AsyncTransport,
)
from .resources import (
    AsyncAgentResource,
    AsyncEstimateResource,
    AsyncEventsResource,
    AsyncPlayersResource,
    AsyncSeasonsResource,
    AsyncSportsResource,
    AsyncTeamsResource,
    AsyncWebhooksResource,
)


class AsyncLumify:
    """The async/await counterpart to :class:`lumify.Lumify` — identical
    resource shape and REST contract, ``await``-able methods. Needs the
    optional ``httpx`` dependency (``pip install "lumify-sdk[asyncio]"``)
    unless you supply your own ``transport=``.

    Example::

        import asyncio
        from lumify.aio import AsyncLumify

        async def main():
            async with AsyncLumify(api_key=os.environ["LUMIFY_API_KEY"]) as client:
                sports, event = await asyncio.gather(
                    client.sports.list(),
                    client.events.get(12345, include_odds=True),
                )

        asyncio.run(main())

    Use ``async with`` (or call ``await client.aclose()`` when done) to
    release the pooled HTTP connection cleanly.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        transport: Optional[AsyncTransport] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        self._client = AsyncLumifyClient(
            api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            transport=transport,
            user_agent=user_agent,
        )
        self.sports = AsyncSportsResource(self._client)
        self.seasons = AsyncSeasonsResource(self._client)
        self.events = AsyncEventsResource(self._client)
        self.teams = AsyncTeamsResource(self._client)
        self.players = AsyncPlayersResource(self._client)
        self.webhooks = AsyncWebhooksResource(self._client)
        self.agent = AsyncAgentResource(self._client)
        self.estimate = AsyncEstimateResource(self._client)

    @property
    def base_url(self) -> str:
        """The configured API origin (default ``https://lumify.ai``)."""
        return self._client.base_url

    async def aclose(self) -> None:
        """Close the pooled HTTP connection. Safe to call multiple times;
        a no-op if you supplied a custom ``transport=``."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncLumify":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
