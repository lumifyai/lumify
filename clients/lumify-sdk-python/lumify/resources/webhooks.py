from __future__ import annotations

from typing import Callable, List, Optional

from .._transport import LumifyClient
from ..models import (
    WebhookCreateResponse,
    WebhookDeleteResponse,
    WebhookDeliveryListResponse,
    WebhookListResponse,
)
from ..webhook_signature import verify_webhook


class WebhooksResource:
    def __init__(self, client: LumifyClient) -> None:
        self._client = client

    def create(
        self,
        *,
        url: str,
        event_types: Optional[List[str]] = None,
        sport: Optional[str] = None,
        event_id: Optional[int] = None,
    ) -> WebhookCreateResponse:
        """POST /v1/webhooks. The response's ``signing_secret`` (``whsec_...``)
        is returned once — store it to verify deliveries with :meth:`verify`.

        ``event_types`` defaults to ``["score", "status"]`` server-side.
        """
        return self._client.post(
            "/v1/webhooks",
            body={
                "url": url,
                "event_types": event_types,
                "sport": sport,
                "event_id": event_id,
            },
        )

    def list(self) -> WebhookListResponse:
        """GET /v1/webhooks — the caller's subscriptions (signing secrets are
        not re-returned)."""
        return self._client.get("/v1/webhooks")

    def delete(self, subscription_id: int) -> WebhookDeleteResponse:
        """DELETE /v1/webhooks/{id}."""
        return self._client.delete("/v1/webhooks/%d" % subscription_id)

    def deliveries(
        self,
        subscription_id: int,
        *,
        after_id: Optional[int] = None,
        limit: Optional[int] = None,
        success: Optional[bool] = None,
        given_up: Optional[bool] = None,
        event_type: Optional[str] = None,
    ) -> WebhookDeliveryListResponse:
        """GET /v1/webhooks/{id}/deliveries — paginated delivery history for one
        subscription, newest first. Each retry attempt is its own row, linked
        back to the attempt it retried via ``parent_delivery_id``, so you can
        reconstruct the full chain for a failed event. Failed deliveries whose
        failure looked transient (5xx/429/timeout) are automatically retried
        with exponential backoff (30s/5m/30m/2h/6h) until ``given_up`` is true.

        Optional filters: ``success`` (2xx vs not), ``given_up``, ``event_type``.
        """
        return self._client.get(
            "/v1/webhooks/%d/deliveries" % subscription_id,
            query={
                "after_id": after_id,
                "limit": limit,
                "success": success,
                "given_up": given_up,
                "event_type": event_type,
            },
        )

    def verify(
        self,
        signing_secret: str,
        signature_header: str,
        raw_body: str,
        *,
        tolerance_seconds: int = 300,
        now: Optional[Callable[[], float]] = None,
    ) -> None:
        """Verify a delivery's ``Lumify-Signature`` header against the raw
        request body and this subscription's ``signing_secret``. Raises
        ``WebhookSignatureError`` if invalid."""
        verify_webhook(
            signing_secret,
            signature_header,
            raw_body,
            tolerance_seconds=tolerance_seconds,
            now=now,
        )
