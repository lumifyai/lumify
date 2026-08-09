import { ConnectionError, APIError, errorFromResponse, type LumifyErrorPayload } from "./errors.js";
import { attachMeta, parseMeta } from "./meta.js";

export const DEFAULT_BASE_URL = "https://lumify.ai";
const DEFAULT_TIMEOUT_MS = 30_000;
const DEFAULT_MAX_RETRIES = 2;
const SDK_VERSION = "0.2.0";

export interface LumifyClientOptions {
  /** Lumify API key (`lmfy-...`). Create one at https://lumify.ai/api-keys. */
  apiKey: string;
  /** Override the API origin — mainly for testing against a local server. */
  baseUrl?: string;
  /** Per-request timeout in milliseconds. Default 30000. */
  timeoutMs?: number;
  /** Retries for idempotent (GET) requests on 429/5xx/network errors. Default 2. */
  maxRetries?: number;
  /** Injectable fetch implementation (tests, non-standard runtimes). */
  fetch?: typeof fetch;
  /** Extra string appended to the User-Agent header. */
  userAgent?: string;
}

export type QueryParams = Record<string, string | number | boolean | null | undefined>;

export interface RequestOptions {
  query?: QueryParams;
  body?: unknown;
  /** Override retry behavior for this call (defaults to the method's idempotency). */
  idempotent?: boolean;
  signal?: AbortSignal;
}

function buildQuery(params?: QueryParams): string {
  if (!params) return "";
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    usp.set(key, String(value));
  }
  const qs = usp.toString();
  return qs ? `?${qs}` : "";
}

async function sleep(ms: number): Promise<void> {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

/** Low-level HTTP transport shared by every resource. Not usually constructed directly — use {@link Lumify}. */
export class LumifyClient {
  readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;
  private readonly fetchImpl: typeof fetch;
  private readonly userAgent: string;

  constructor(opts: LumifyClientOptions) {
    if (!opts.apiKey) {
      throw new Error("Lumify SDK: `apiKey` is required (create one at https://lumify.ai/api-keys).");
    }
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/$/, "");
    this.timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.maxRetries = opts.maxRetries ?? DEFAULT_MAX_RETRIES;
    this.fetchImpl = opts.fetch ?? globalThis.fetch;
    if (!this.fetchImpl) {
      throw new Error(
        "Lumify SDK: no `fetch` available in this runtime. Use Node 18+, a browser, " +
          "or pass a `fetch` implementation in the client options."
      );
    }
    this.userAgent = `lumify-sdk-js/${SDK_VERSION}${opts.userAgent ? ` ${opts.userAgent}` : ""}`;
  }

  /** Build an absolute URL for a path, without performing the request. */
  url(path: string, query?: QueryParams): string {
    return `${this.baseUrl}${path}${buildQuery(query)}`;
  }

  /**
   * Base headers for a request that needs raw `fetch` (SSE streaming), where
   * `request()`'s buffered JSON handling doesn't apply. Not part of the
   * supported public API surface for arbitrary callers — resources within
   * this package use it to avoid duplicating auth/UA construction.
   */
  authHeaders(accept = "application/json"): Record<string, string> {
    return {
      Authorization: `Bearer ${this.apiKey}`,
      Accept: accept,
      "User-Agent": this.userAgent,
    };
  }

  /** The injected/global `fetch` this client uses — for raw streaming calls (SSE). */
  get fetchFn(): typeof fetch {
    return this.fetchImpl;
  }

  /** Per-request timeout (ms) configured on this client — used as the SSE connect timeout default. */
  get requestTimeoutMs(): number {
    return this.timeoutMs;
  }

  /** GET a resource and parse its JSON body. */
  get<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return this.request<T>("GET", path, { ...options, idempotent: options.idempotent ?? true });
  }

  /** POST a resource and parse its JSON body. Not retried by default (not idempotent). */
  post<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return this.request<T>("POST", path, { ...options, idempotent: options.idempotent ?? false });
  }

  /** DELETE a resource and parse its JSON body. */
  delete<T>(path: string, options: RequestOptions = {}): Promise<T> {
    return this.request<T>("DELETE", path, { ...options, idempotent: options.idempotent ?? true });
  }

  /**
   * Perform the raw fetch, with:
   *  - Bearer auth + JSON headers
   *  - a hard per-request timeout
   *  - retries with exponential backoff for idempotent requests on 429/5xx/network
   *    failures, honoring `Retry-After` / `error.retry_after` on 429
   *  - the unified error envelope mapped to a typed {@link LumifyError} subclass
   *  - X-Credits and X-RateLimit response headers attached to the parsed body
   *    via {@link attachMeta} (read with {@link getMeta})
   */
  async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    const idempotent = options.idempotent ?? method === "GET";
    const attempts = idempotent ? Math.max(1, this.maxRetries + 1) : 1;
    let lastError: unknown;

    for (let attempt = 0; attempt < attempts; attempt++) {
      if (attempt > 0) {
        await sleep(this.backoffMs(attempt, lastError));
      }
      try {
        return await this.attempt<T>(method, path, options);
      } catch (err) {
        lastError = err;
        if (!this.shouldRetry(err) || attempt === attempts - 1) {
          throw err;
        }
      }
    }
    // Unreachable — the loop always returns or throws — but keeps TS satisfied.
    throw lastError;
  }

  private shouldRetry(err: unknown): boolean {
    if (err instanceof ConnectionError) return true;
    const status = (err as { status?: number }).status;
    return status === 429 || (typeof status === "number" && status >= 500);
  }

  private backoffMs(attempt: number, lastError: unknown): number {
    const retryAfter = (lastError as { retryAfter?: number } | undefined)?.retryAfter;
    if (typeof retryAfter === "number" && retryAfter >= 0) {
      return retryAfter * 1000;
    }
    const base = 250 * 2 ** (attempt - 1);
    const jitter = Math.random() * 100;
    return base + jitter;
  }

  private async attempt<T>(method: string, path: string, options: RequestOptions): Promise<T> {
    const url = this.url(path, options.query);
    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.apiKey}`,
      Accept: "application/json",
      "User-Agent": this.userAgent,
    };
    let body: string | undefined;
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(options.body);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(new Error("timeout")), this.timeoutMs);
    const signal = options.signal ? anySignal([options.signal, controller.signal]) : controller.signal;

    let res: Response;
    try {
      res = await this.fetchImpl(url, { method, headers, body, signal });
    } catch (err) {
      throw new ConnectionError(
        `Request to ${method} ${path} failed: ${err instanceof Error ? err.message : String(err)}`,
        { cause: err }
      );
    } finally {
      clearTimeout(timeout);
    }

    const requestId = res.headers.get("x-request-id");
    const text = await res.text();
    const json = text ? safeJsonParse(text) : undefined;
    const parseFailed = Boolean(text) && json === undefined;

    if (!res.ok) {
      const payload = (json as { error?: LumifyErrorPayload } | undefined)?.error;
      const retryAfterHeader = parseRetryAfter(res.headers.get("retry-after"));
      throw errorFromResponse(res.status, payload, requestId, { retryAfterHeader });
    }

    if (parseFailed) {
      throw new APIError(`Response from ${method} ${path} was not valid JSON.`, {
        status: res.status,
        code: "invalid_response",
        requestId,
      });
    }

    const meta = parseMeta(res.headers);
    return attachMeta(json as T, meta);
  }
}

function safeJsonParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

/** Parse `Retry-After` as seconds. Supports integer seconds; ignores HTTP-date forms. */
function parseRetryAfter(header: string | null): number | undefined {
  if (header == null || header === "") return undefined;
  const seconds = Number(header);
  if (!Number.isFinite(seconds) || seconds < 0) return undefined;
  return seconds;
}

/** Minimal AbortSignal.any polyfill-free combinator (works without lib.dom's AbortSignal.any). */
function anySignal(signals: AbortSignal[]): AbortSignal {
  if (typeof AbortSignal !== "undefined" && "any" in AbortSignal) {
    return (AbortSignal as unknown as { any(signals: AbortSignal[]): AbortSignal }).any(signals);
  }
  const controller = new AbortController();
  for (const s of signals) {
    if (s.aborted) {
      controller.abort(s.reason);
      break;
    }
    s.addEventListener("abort", () => controller.abort(s.reason), { once: true });
  }
  return controller.signal;
}
