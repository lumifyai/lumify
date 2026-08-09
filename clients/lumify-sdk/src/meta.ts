// Parses the response headers documented in docs.html's "Response headers"
// table (X-RateLimit-*, X-Credits-*) into a typed object attached to every
// successful SDK response as `response.meta`.

export interface ResponseMeta {
  /** Max requests allowed in the current rate-limit window. */
  rateLimitLimit?: number;
  /** Requests remaining in the current window. */
  rateLimitRemaining?: number;
  /** Unix timestamp (seconds) when the window resets. */
  rateLimitReset?: number;
  /** Credits charged for this call (0 for unavailable-data reads — billing fairness). */
  creditsUsed?: number;
  /** Best-effort remaining balance; omitted for unmetered/unlimited plans. */
  creditsRemaining?: number;
  /** Raw Headers object, for anything not surfaced above. */
  headers: Headers;
}

function num(headers: Headers, name: string): number | undefined {
  const v = headers.get(name);
  if (v == null) return undefined;
  const n = Number(v);
  return Number.isNaN(n) ? undefined : n;
}

export function parseMeta(headers: Headers): ResponseMeta {
  return {
    rateLimitLimit: num(headers, "x-ratelimit-limit"),
    rateLimitRemaining: num(headers, "x-ratelimit-remaining"),
    rateLimitReset: num(headers, "x-ratelimit-reset"),
    creditsUsed: num(headers, "x-credits-used"),
    creditsRemaining: num(headers, "x-credits-remaining"),
    headers,
  };
}

/**
 * Every resource method returns the parsed body directly (e.g. `SportsListResponse`)
 * for ergonomics — not a `{data, meta}` wrapper — so response metadata (credits,
 * rate-limit) is instead attached as a hidden, non-enumerable property keyed by
 * this symbol. It's invisible to `JSON.stringify`/`for...in`/object spreads, so it
 * never leaks into logs or persisted data; use {@link getMeta} to read it back.
 */
export const RESPONSE_META = Symbol.for("lumify.sdk.responseMeta");

/** Read the {@link ResponseMeta} attached to a value returned by an SDK call. */
export function getMeta(value: unknown): ResponseMeta | undefined {
  if (value && typeof value === "object") {
    return (value as Record<symbol, ResponseMeta | undefined>)[RESPONSE_META];
  }
  return undefined;
}

export function attachMeta<T>(value: T, meta: ResponseMeta): T {
  if (value && typeof value === "object") {
    Object.defineProperty(value, RESPONSE_META, {
      value: meta,
      enumerable: false,
      configurable: true,
    });
  }
  return value;
}
