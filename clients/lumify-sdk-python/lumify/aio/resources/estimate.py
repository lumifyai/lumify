from __future__ import annotations

from typing import List

from ..._async_transport import AsyncLumifyClient
from ...models import EstimateCall, EstimateResponse


class AsyncEstimateResource:
    def __init__(self, client: AsyncLumifyClient) -> None:
        self._client = client

    async def cost(self, calls: List[EstimateCall]) -> EstimateResponse:
        """POST /v1/estimate — pre-call credit-cost estimate for one or more
        planned tool calls, without making them or spending credits. Costs are
        data-dependent (e.g. odds/intelligence not yet ingested are free), so
        each result is a ``[min_credits, max_credits]`` range, not a single
        number. Always free (0 credits) to call.

        Each entry in ``calls`` is ``{"tool": "get_event", "arguments": {...}}``
        — the same tool name and arguments you'd pass to the matching MCP tool
        or SDK method. See :meth:`list_tools` for the supported tool names.
        """
        return await self._client.post("/v1/estimate", body={"calls": calls})

    async def list_tools(self) -> dict:
        """GET /v1/estimate/tools — the tool names :meth:`cost` understands,
        grouped by how their cost varies."""
        return await self._client.get("/v1/estimate/tools")
