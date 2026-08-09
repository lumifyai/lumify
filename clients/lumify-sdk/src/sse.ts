// Server-Sent Events reader for GET /v1/events/{id}/stream (see api/routes/v1/stream.py).
// The endpoint emits named events — `score` on change, `done` when the event
// finishes, `error` if the event id doesn't exist — plus unnamed `: keep-alive`
// comment pings every ~15s. This module has no dependency on the DOM
// `EventSource` API (which can't set an Authorization header); it parses the
// wire format directly off the fetch `Response` body stream, which works
// identically in Node 18+ and browsers.

import type { LumifyClient } from "./client.js";
import { ConnectionError, errorFromResponse } from "./errors.js";
import type { LumifyErrorPayload } from "./errors.js";
import type { ScoreResponse } from "./generated/models.js";

export interface SSEEvent {
  /** SSE `event:` field. Defaults to "message" per the SSE spec if the server omits it. */
  event: string;
  /** Raw (still-a-string) `data:` field, joined across multiline data. */
  data: string;
  id?: string;
}

/**
 * Parse a `text/event-stream` response body into individual SSE frames.
 * Exposed for advanced use; most callers want {@link streamScores}.
 *
 * Frames are separated by a blank line (`\n\n` or `\r\n\r\n`). The reader is
 * cancelled when the consumer breaks out of the async iterator so the upstream
 * fetch connection is released promptly.
 */
export async function* parseSSEStream(body: ReadableStream<Uint8Array>): AsyncGenerator<SSEEvent, void, void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Normalize CRLF → LF so a single splitter handles both wire forms.
      buffer = buffer.replace(/\r\n/g, "\n").replace(/\r/g, "\n");

      let sepIndex: number;
      while ((sepIndex = buffer.indexOf("\n\n")) !== -1) {
        const rawFrame = buffer.slice(0, sepIndex);
        buffer = buffer.slice(sepIndex + 2);
        const frame = parseFrame(rawFrame);
        if (frame) yield frame;
      }
    }
  } finally {
    // Cancel the underlying stream so breaking out of `for await` tears down
    // the HTTP connection instead of waiting for the server's 5-minute cap.
    try {
      await reader.cancel();
    } catch {
      // already closed / cancelled
    }
    try {
      reader.releaseLock();
    } catch {
      // already released
    }
  }
}

function parseFrame(raw: string): SSEEvent | null {
  const dataLines: string[] = [];
  let event = "message";
  let id: string | undefined;
  let isCommentOnly = true;

  for (const line of raw.split("\n")) {
    if (line.startsWith(":")) continue; // comment / keep-alive
    isCommentOnly = false;
    if (line.startsWith("event:")) event = line.slice("event:".length).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice("data:".length).trimStart());
    else if (line.startsWith("id:")) id = line.slice("id:".length).trim();
  }

  if (isCommentOnly && dataLines.length === 0) return null; // pure keep-alive frame
  return { event, data: dataLines.join("\n"), id };
}

export interface StreamScoresOptions {
  /** Abort the stream from the caller's side (e.g. on a UI unmount). */
  signal?: AbortSignal;
  /**
   * Timeout for the *initial* HTTP connect/headers only (ms). The stream itself
   * is long-lived and is not subject to this timeout. Defaults to the client's
   * `timeoutMs` (30s). Pass `0` to disable.
   */
  connectTimeoutMs?: number;
}

export type ScoreStreamEvent =
  | { event: "score"; data: ScoreResponse }
  | { event: "done"; data: { event_id: number } }
  | { event: "error"; data: { error: { code: string; message: string } } }
  | { event: "reconnect"; data: { event_id: number; reason: string; max_seconds: number } };

async function connectStream(
  client: LumifyClient,
  eventId: number,
  options: StreamScoresOptions
): Promise<Response> {
  const url = client.url(`/v1/events/${eventId}/stream`);

  // Connect-phase timeout only — once headers arrive we clear it so the
  // long-lived SSE body isn't aborted by the client default timeout.
  const connectTimeoutMs =
    options.connectTimeoutMs !== undefined ? options.connectTimeoutMs : client.requestTimeoutMs;
  const connectController = new AbortController();
  let connectTimer: ReturnType<typeof setTimeout> | undefined;
  if (connectTimeoutMs > 0) {
    connectTimer = setTimeout(
      () => connectController.abort(new Error("connect timeout")),
      connectTimeoutMs
    );
  }

  const signals: AbortSignal[] = [connectController.signal];
  if (options.signal) signals.push(options.signal);
  const signal = anySignal(signals);

  let res: Response;
  try {
    res = await client.fetchFn(url, {
      headers: client.authHeaders("text/event-stream"),
      signal,
    });
  } catch (err) {
    throw new ConnectionError(
      `SSE connect to /v1/events/${eventId}/stream failed: ${err instanceof Error ? err.message : String(err)}`,
      { cause: err }
    );
  } finally {
    if (connectTimer) clearTimeout(connectTimer);
  }

  if (!res.ok) {
    let payload: { error?: LumifyErrorPayload } | undefined;
    try {
      payload = await res.json();
    } catch {
      // non-JSON error body — fall through with an undefined payload
    }
    const retryAfterHeader = parseRetryAfter(res.headers.get("retry-after"));
    throw errorFromResponse(res.status, payload?.error, res.headers.get("x-request-id"), {
      retryAfterHeader,
    });
  }

  if (!res.body) {
    throw new ConnectionError(`SSE response for event ${eventId} had no body.`);
  }

  return res;
}

/**
 * Async-iterate live score updates for an event over SSE. Emits only on
 * change (plus a final `done`), so it's far cheaper than polling `get_live_score`.
 *
 * The server caps a single connection at 5 minutes and sends `event: reconnect`
 * just before closing it for that reason (as opposed to `done`, which means the
 * game actually finished). This generator reconnects on that signal
 * automatically and keeps yielding — a long game's stream looks continuous to
 * the caller. The `reconnect` event is still yielded for visibility/telemetry;
 * no action is required in response to it.
 *
 * @example
 * for await (const evt of streamScores(client, eventId)) {
 *   if (evt.event === "score") console.log(evt.data.status, evt.data.clock);
 *   if (evt.event === "done") break;
 * }
 */
export async function* streamScores(
  client: LumifyClient,
  eventId: number,
  options: StreamScoresOptions = {}
): AsyncGenerator<ScoreStreamEvent, void, void> {
  for (;;) {
    const res = await connectStream(client, eventId, options);
    let reconnecting = false;

    for await (const frame of parseSSEStream(res.body!)) {
      if (frame.event === "message" && !frame.data) continue; // keep-alive with no named event
      let parsed: unknown;
      try {
        parsed = frame.data ? JSON.parse(frame.data) : undefined;
      } catch {
        continue; // malformed frame — skip rather than throw mid-stream
      }
      yield { event: frame.event, data: parsed } as ScoreStreamEvent;
      if (frame.event === "reconnect") {
        reconnecting = true;
        break; // tear down this connection below, then loop to reconnect
      }
      if (frame.event === "done" || frame.event === "error") return;
    }

    if (!reconnecting) return; // stream ended without an explicit reconnect signal
  }
}

function parseRetryAfter(header: string | null): number | undefined {
  if (header == null || header === "") return undefined;
  const seconds = Number(header);
  if (!Number.isFinite(seconds) || seconds < 0) return undefined;
  return seconds;
}

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
