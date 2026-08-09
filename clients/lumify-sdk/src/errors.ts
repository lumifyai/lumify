// Error taxonomy mirroring api/errors.py's unified envelope:
//
//   { "error": { "code", "message", "status", "doc_url", ...extra }, "detail" }
//
// Agents should switch on `err.code`, not parse `err.message`.

/** Shape of the `error` object inside every Lumify error envelope. */
export interface LumifyErrorPayload {
  code: string;
  message: string;
  status: number;
  doc_url?: string;
  /** Present on 429 responses; seconds until the rate-limit window resets. */
  retry_after?: number;
  /** Present on some 403 responses (sport-scope denials). */
  upgrade_url?: string;
  /** Present on 422 validation errors. */
  errors?: Array<{ field: string; message: string; type: string }>;
  [key: string]: unknown;
}

export interface LumifyErrorOptions {
  status: number;
  code: string;
  docUrl?: string;
  requestId?: string | null;
  payload?: LumifyErrorPayload;
  cause?: unknown;
}

/** Base class for every error the SDK throws for a non-2xx API response. */
export class LumifyError extends Error {
  /** Stable machine-readable slug, e.g. "not_found" — switch on this. */
  readonly code: string;
  /** HTTP status code. */
  readonly status: number;
  /** Link to the error-code reference docs. */
  readonly docUrl?: string;
  /** Value of the `X-Request-Id` request header, if the caller sent one. */
  readonly requestId?: string | null;
  /** The full parsed `error` object from the response envelope. */
  readonly payload?: LumifyErrorPayload;

  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts.cause !== undefined ? { cause: opts.cause } : undefined);
    this.name = "LumifyError";
    this.code = opts.code;
    this.status = opts.status;
    this.docUrl = opts.docUrl;
    this.requestId = opts.requestId ?? null;
    this.payload = opts.payload;
  }
}

export class AuthenticationError extends LumifyError {
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "AuthenticationError";
  }
}

export class PermissionError extends LumifyError {
  /** Present on sport-scope denials — where to upgrade the API key's plan/scope. */
  readonly upgradeUrl?: string;
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "PermissionError";
    this.upgradeUrl = opts.payload?.upgrade_url as string | undefined;
  }
}

export class NotFoundError extends LumifyError {
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "NotFoundError";
  }
}

export class RateLimitError extends LumifyError {
  /** Seconds to wait before retrying (mirrors the `Retry-After` header / `error.retry_after`). */
  readonly retryAfter?: number;
  constructor(message: string, opts: LumifyErrorOptions & { retryAfter?: number }) {
    super(message, opts);
    this.name = "RateLimitError";
    // Prefer the envelope field (canonical for Lumify), fall back to the header.
    const fromPayload = opts.payload?.retry_after;
    const resolved =
      typeof fromPayload === "number"
        ? fromPayload
        : typeof opts.retryAfter === "number"
          ? opts.retryAfter
          : undefined;
    this.retryAfter = resolved;
  }
}

export interface FieldError {
  field: string;
  message: string;
  type: string;
}

export class ValidationError extends LumifyError {
  readonly fieldErrors: FieldError[];
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "ValidationError";
    this.fieldErrors = (opts.payload?.errors as FieldError[] | undefined) ?? [];
  }
}

/** 402 — credit top-up or payment method required. */
export class PaymentError extends LumifyError {
  /** Present on credit/trial denials — where to upgrade the plan. */
  readonly upgradeUrl?: string;
  /** Present on credit denials — dashboard top-up entry point. */
  readonly topupUrl?: string;
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "PaymentError";
    this.upgradeUrl = opts.payload?.upgrade_url as string | undefined;
    this.topupUrl = opts.payload?.topup_url as string | undefined;
  }
}

/** 5xx or any status this SDK doesn't have a dedicated class for. */
export class APIError extends LumifyError {
  constructor(message: string, opts: LumifyErrorOptions) {
    super(message, opts);
    this.name = "APIError";
  }
}

/** Network failure, timeout, or abort — the request never got a response. */
export class ConnectionError extends LumifyError {
  constructor(message: string, opts: { cause?: unknown } = {}) {
    super(message, { status: 0, code: "connection_error", cause: opts.cause });
    this.name = "ConnectionError";
  }
}

export interface ErrorFromResponseOptions {
  /** Seconds parsed from the `Retry-After` response header, when present. */
  retryAfterHeader?: number;
}

/**
 * Build the right LumifyError subclass from a parsed error envelope.
 * Falls back to APIError for unrecognized status codes.
 */
export function errorFromResponse(
  status: number,
  payload: LumifyErrorPayload | undefined,
  requestId: string | null,
  options: ErrorFromResponseOptions = {}
): LumifyError {
  const code = payload?.code ?? `http_${status}`;
  const message = payload?.message ?? `Request failed with status ${status}.`;
  const opts: LumifyErrorOptions = { status, code, docUrl: payload?.doc_url, requestId, payload };

  switch (status) {
    case 401:
      return new AuthenticationError(message, opts);
    case 402:
      return new PaymentError(message, opts);
    case 403:
      return new PermissionError(message, opts);
    case 404:
      return new NotFoundError(message, opts);
    case 422:
      return new ValidationError(message, opts);
    case 429:
      return new RateLimitError(message, { ...opts, retryAfter: options.retryAfterHeader });
    default:
      return new APIError(message, opts);
  }
}
