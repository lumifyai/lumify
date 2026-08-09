from __future__ import annotations

from typing import List, Optional

from ..._async_transport import AsyncLumifyClient
from ...models import (
    AgentApiKey,
    AgentApiKeyListResponse,
    AgentApiKeyRevokeResponse,
    AgentCreditsResponse,
    CreditPackListResponse,
    CreditTopupResponse,
)


class AsyncAgentKeysResource:
    """Programmatic API-key lifecycle — mint/list/revoke keys without the dashboard."""

    def __init__(self, client: AsyncLumifyClient) -> None:
        self._client = client

    async def create(
        self,
        *,
        name: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_in_days: Optional[int] = None,
    ) -> AgentApiKey:
        """POST /api/agent/keys — the full key is only returned once, on creation."""
        return await self._client.post(
            "/api/agent/keys",
            body={"name": name, "scopes": scopes, "expires_in_days": expires_in_days},
        )

    async def list(self) -> AgentApiKeyListResponse:
        """GET /api/agent/keys."""
        return await self._client.get("/api/agent/keys")

    async def revoke(self, key_id: int) -> AgentApiKeyRevokeResponse:
        """DELETE /api/agent/keys/{id}."""
        return await self._client.delete("/api/agent/keys/%d" % key_id)


class AsyncAgentCreditsResource:
    """Credit balance, usage, and top-ups — for agents managing their own spend."""

    def __init__(self, client: AsyncLumifyClient) -> None:
        self._client = client

    async def get(self) -> AgentCreditsResponse:
        """GET /api/agent/credits — current balance, usage, and billing period."""
        return await self._client.get("/api/agent/credits")

    async def list_packs(self) -> CreditPackListResponse:
        """GET /api/agent/credit-packs — purchasable one-off credit packs."""
        return await self._client.get("/api/agent/credit-packs")

    async def topup(self, pack_id: int) -> CreditTopupResponse:
        """POST /api/agent/credits/topup — charges the account's saved payment
        method for ``pack_id`` (see :meth:`list_packs`)."""
        return await self._client.post("/api/agent/credits/topup", body={"pack_id": pack_id})


class AsyncAgentResource:
    """Agent onboarding surface: ``client.agent.keys.*`` and ``client.agent.credits.*``."""

    def __init__(self, client: AsyncLumifyClient) -> None:
        self.keys = AsyncAgentKeysResource(client)
        self.credits = AsyncAgentCreditsResource(client)
