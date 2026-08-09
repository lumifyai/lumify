// @lumifyai/sdk — official TypeScript/JavaScript client for the Lumify
// agent-ready sports intelligence API. See https://lumify.ai/docs.

export { Lumify } from "./lumify.js";
export type { LumifyClientOptions } from "./client.js";
export { LumifyClient, DEFAULT_BASE_URL } from "./client.js";

export {
  LumifyError,
  AuthenticationError,
  PermissionError,
  NotFoundError,
  RateLimitError,
  ValidationError,
  APIError,
  ConnectionError,
  PaymentError,
  type LumifyErrorPayload,
  type FieldError,
} from "./errors.js";

export { getMeta, RESPONSE_META, type ResponseMeta } from "./meta.js";
export { paginate, iterateItems, type PaginateOptions, type IterateOptions, type CursorPage } from "./pagination.js";
export { parseSSEStream, streamScores, type SSEEvent, type ScoreStreamEvent, type StreamScoresOptions } from "./sse.js";
export { verifyWebhook, WebhookSignatureError, type VerifyWebhookOptions } from "./webhook-signature.js";

export type {
  ListSportsParams,
  ListSeasonsParams,
} from "./resources/sports.js";
export type {
  ListEventsParams,
  GetEventParams,
  BookmakerParams,
  OddsHistoryParams,
  EventDetailWithIncludes,
} from "./resources/events.js";
export type { ListTeamsParams } from "./resources/teams.js";
export type { ListPlayersParams, PlayerEventsParams } from "./resources/players.js";
export type { CreateWebhookParams, WebhookEventType } from "./resources/webhooks.js";
export type { CreateApiKeyParams } from "./resources/agent.js";

export * from "./generated/models.js";
