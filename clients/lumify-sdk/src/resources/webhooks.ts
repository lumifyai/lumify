import type { LumifyClient } from "../client.js";
import type {
  WebhookCreateResponse,
  WebhookDeleteResponse,
  WebhookDeliveryListResponse,
  WebhookListResponse,
} from "../generated/models.js";
import { verifyWebhook, type VerifyWebhookOptions } from "../webhook-signature.js";

/** Event types a webhook subscription can fire on (see core/webhooks/delivery.py). */
export type WebhookEventType = "score" | "status" | "line_move" | "intelligence";

export interface CreateWebhookParams {
  /** HTTPS delivery URL. Rejected if it resolves to a private/loopback address (SSRF guard). */
  url: string;
  /** Defaults to ["score", "status"] server-side if omitted. */
  eventTypes?: WebhookEventType[];
  /** Scope the subscription to one sport. */
  sport?: string;
  /** Scope the subscription to one event. */
  eventId?: number;
}

export interface ListWebhookDeliveriesParams {
  /** Cursor: return deliveries with id < afterId (list is newest-first). */
  afterId?: number;
  /** Page size, default 25, max 100. */
  limit?: number;
  /** Filter to successful (2xx) or failed deliveries. */
  success?: boolean;
  /** Filter to deliveries that exhausted retries (or not). */
  givenUp?: boolean;
  /** Filter by event type (score, status, line_move, intelligence). */
  eventType?: WebhookEventType | string;
}

export class WebhooksResource {
  constructor(private readonly client: LumifyClient) {}

  /**
   * POST /v1/webhooks. The response's `signing_secret` (`whsec_...`) is
   * returned once — store it to verify deliveries with {@link WebhooksResource.verify}.
   */
  create(params: CreateWebhookParams): Promise<WebhookCreateResponse> {
    return this.client.post<WebhookCreateResponse>("/v1/webhooks", {
      body: {
        url: params.url,
        event_types: params.eventTypes,
        sport: params.sport,
        event_id: params.eventId,
      },
    });
  }

  /** GET /v1/webhooks — the caller's subscriptions (signing secrets are not re-returned). */
  list(): Promise<WebhookListResponse> {
    return this.client.get<WebhookListResponse>("/v1/webhooks");
  }

  /** DELETE /v1/webhooks/{id} */
  delete(subscriptionId: number): Promise<WebhookDeleteResponse> {
    return this.client.delete<WebhookDeleteResponse>(`/v1/webhooks/${subscriptionId}`);
  }

  /**
   * GET /v1/webhooks/{id}/deliveries — paginated delivery history for one
   * subscription, newest first. Each retry attempt is its own row, linked
   * back to the attempt it retried via `parent_delivery_id`, so you can
   * reconstruct the full chain for a failed event. Failed deliveries whose
   * failure looked transient (5xx/429/timeout) are automatically retried
   * with exponential backoff (30s/5m/30m/2h/6h) until `given_up` is true.
   */
  deliveries(
    subscriptionId: number,
    params: ListWebhookDeliveriesParams = {}
  ): Promise<WebhookDeliveryListResponse> {
    return this.client.get<WebhookDeliveryListResponse>(`/v1/webhooks/${subscriptionId}/deliveries`, {
      query: {
        after_id: params.afterId,
        limit: params.limit,
        success: params.success,
        given_up: params.givenUp,
        event_type: params.eventType,
      },
    });
  }

  /**
   * Verify a delivery's `Lumify-Signature` header against the raw request
   * body and this subscription's `signing_secret`. Throws
   * `WebhookSignatureError` (imported from `@lumifyai/sdk`) if invalid.
   */
  verify(
    signingSecret: string,
    signatureHeader: string,
    rawBody: string,
    options?: VerifyWebhookOptions
  ): Promise<void> {
    return verifyWebhook(signingSecret, signatureHeader, rawBody, options);
  }
}
