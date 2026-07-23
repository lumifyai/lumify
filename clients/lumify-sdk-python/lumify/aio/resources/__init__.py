"""Async resource classes — one per REST resource group, mirroring
:mod:`lumify.resources` method-for-method but ``async``/``await``."""

from .agent import AsyncAgentCreditsResource, AsyncAgentKeysResource, AsyncAgentResource
from .estimate import AsyncEstimateResource
from .events import AsyncEventsResource
from .players import AsyncPlayersResource
from .sports import AsyncSeasonsResource, AsyncSportsResource
from .teams import AsyncTeamsResource
from .webhooks import AsyncWebhooksResource

__all__ = [
    "AsyncSportsResource",
    "AsyncSeasonsResource",
    "AsyncEventsResource",
    "AsyncTeamsResource",
    "AsyncPlayersResource",
    "AsyncWebhooksResource",
    "AsyncAgentResource",
    "AsyncAgentKeysResource",
    "AsyncAgentCreditsResource",
    "AsyncEstimateResource",
]
