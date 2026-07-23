"""Resource classes — one per REST resource group. Each method maps 1:1 to a
Lumify REST endpoint and returns the same JSON shape (a ``dict`` typed as the
matching model in :mod:`lumify.models`)."""

from .agent import AgentCreditsResource, AgentKeysResource, AgentResource
from .estimate import EstimateResource
from .events import EventsResource
from .players import PlayersResource
from .sports import SeasonsResource, SportsResource
from .teams import TeamsResource
from .webhooks import WebhooksResource

__all__ = [
    "SportsResource",
    "SeasonsResource",
    "EventsResource",
    "TeamsResource",
    "PlayersResource",
    "WebhooksResource",
    "AgentResource",
    "AgentKeysResource",
    "AgentCreditsResource",
    "EstimateResource",
]
