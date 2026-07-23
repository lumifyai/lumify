// Core of the lumify-mcp local bridge.
//
// The Lumify MCP server is hosted (Streamable HTTP, JSON mode, stateless) at
// https://lumify.ai/mcp. Some MCP clients only speak the local stdio transport,
// so this bridge exposes the same server over stdio: it reads newline-delimited
// JSON-RPC messages, forwards each one VERBATIM to the hosted endpoint with the
// API key injected as a Bearer token, and writes the response back.
//
// Because it forwards raw JSON-RPC, the hosted server remains the single source
// of truth for the tool catalog, input schemas, protocol negotiation, and credit
// metering — nothing is duplicated here, so nothing can drift. The only value
// this layer adds beyond a generic proxy is:
//   1. Translating HTTP-level failures (429 / 4xx / 5xx / network / timeout)
//      into well-formed JSON-RPC error replies.
//   2. Guaranteeing NDJSON-safe stdout (MCP stdio forbids embedded newlines) by
//      re-serializing every successful upstream body.
//   3. Pinning MCP-Protocol-Version after initialize, the way a proper
//      Streamable-HTTP client would.

export const DEFAULT_MCP_URL = "https://lumify.ai/mcp";
const DEFAULT_TIMEOUT_MS = 30_000;

/**
 * Build a bridge bound to an upstream endpoint + credentials.
 *
 * @param {object} [opts]
 * @param {string} [opts.url]        Upstream MCP endpoint (default lumify.ai/mcp).
 * @param {string} [opts.apiKey]     Lumify API key (lmfy-...); omitted → handshake only.
 * @param {Function} [opts.fetchImpl] fetch implementation (injectable for tests).
 * @param {number} [opts.timeoutMs]  Per-request upstream timeout.
 * @param {string} [opts.userAgent]  User-Agent sent upstream.
 * @returns {{ endpoint: string, handleMessage: (raw: string) => Promise<string|null>, getProtocolVersion: () => string|null }}
 */
export function createBridge({ url, apiKey, fetchImpl, timeoutMs, userAgent } = {}) {
  const endpoint = url || DEFAULT_MCP_URL;
  const doFetch = fetchImpl || globalThis.fetch;
  const ua = userAgent || "lumify-mcp";
  const timeout = timeoutMs ?? DEFAULT_TIMEOUT_MS;
  /** @type {string|null} Negotiated protocol version from the last initialize. */
  let protocolVersion = null;

  if (typeof doFetch !== "function") {
    throw new Error("global fetch is unavailable — lumify-mcp requires Node 18+");
  }

  /**
   * Handle one line from stdin. Resolves to the string to write to stdout, or
   * null when there is nothing to answer (notifications, or an empty/202 reply).
   * The returned string is always a single line of valid JSON (or null).
   */
  async function handleMessage(raw) {
    const line = typeof raw === "string" ? raw.trim() : "";
    if (!line) return null;

    let parsed;
    try {
      parsed = JSON.parse(line);
    } catch {
      // Malformed input never reaches the server; answer per JSON-RPC spec.
      return stringify(jsonRpcError(null, -32700, "Parse error"));
    }

    const ids = collectIds(parsed);

    let res;
    try {
      const headers = {
        "Content-Type": "application/json",
        Accept: "application/json",
        "User-Agent": ua,
      };
      if (apiKey) headers.Authorization = `Bearer ${apiKey}`;
      // After a successful initialize, pin the negotiated protocol version on
      // subsequent requests (Streamable-HTTP client behavior).
      if (protocolVersion) headers["MCP-Protocol-Version"] = protocolVersion;
      res = await doFetch(endpoint, {
        method: "POST",
        headers,
        body: line,
        signal: AbortSignal.timeout(timeout),
      });
    } catch (err) {
      const message =
        err && err.name === "TimeoutError"
          ? `Upstream timeout after ${timeout}ms contacting ${endpoint}`
          : `Upstream request failed: ${(err && err.message) || err}`;
      return errorFor(ids, parsed, -32603, message);
    }

    const text = (await res.text()).trim();

    if (res.ok) {
      // 202 (notifications-only) or an empty body → nothing to write back.
      if (res.status === 202 || !text) return null;
      // Re-serialize so stdout is always one NDJSON line of valid JSON-RPC,
      // even if a proxy pretty-prints or somehow returns non-JSON.
      return sanitizeOkBody(text, ids, parsed, (body) => {
        rememberProtocolVersion(body);
      });
    }

    // Non-2xx: the body is a Lumify HTTP error envelope, not JSON-RPC. Convert
    // it into a JSON-RPC error so the client gets a protocol-valid reply.
    let detail = `HTTP ${res.status}`;
    let data;
    try {
      const env = JSON.parse(text);
      const e = (env && env.error) || {};
      if (e.message) detail = `HTTP ${res.status}: ${e.message}`;
      if (e.code) data = { ...(data || {}), upstream_code: e.code };
      if (e.retry_after != null) {
        data = { ...(data || {}), retry_after: e.retry_after };
        detail += ` (retry after ${e.retry_after}s)`;
      }
    } catch {
      // Non-JSON error body (e.g. an edge/HTML page) — keep the status-only detail.
    }
    return errorFor(ids, parsed, -32603, detail, data);
  }

  function rememberProtocolVersion(body) {
    // initialize result (single message) or first matching entry in a batch.
    const msgs = Array.isArray(body) ? body : [body];
    for (const m of msgs) {
      const ver = m && m.result && m.result.protocolVersion;
      if (typeof ver === "string" && ver) {
        protocolVersion = ver;
        break;
      }
    }
  }

  return {
    endpoint,
    handleMessage,
    getProtocolVersion: () => protocolVersion,
  };
}

// ── helpers ────────────────────────────────────────────────────────────────

/**
 * Ensure a successful upstream body is a single line of JSON. Rejects non-JSON
 * with a JSON-RPC error so stdout never carries HTML/plaintext.
 */
function sanitizeOkBody(text, ids, parsed, onParsed) {
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    return errorFor(
      ids,
      parsed,
      -32603,
      "Upstream returned a non-JSON success body (not a valid MCP message).",
    );
  }
  if (onParsed) onParsed(body);
  return stringify(body);
}

/** IDs of every request (not notification) in a single message or a batch. */
function collectIds(parsed) {
  const arr = Array.isArray(parsed) ? parsed : [parsed];
  return arr
    .filter((m) => m && typeof m === "object" && "id" in m && m.id !== undefined)
    .map((m) => m.id);
}

function jsonRpcError(id, code, message, data) {
  const error = { code, message };
  if (data !== undefined) error.data = data;
  return { jsonrpc: "2.0", id: id ?? null, error };
}

/**
 * Build the error reply matching the request shape: a single error for a single
 * request, an array of errors for a batch, or null when there were only
 * notifications (which per JSON-RPC must not be answered).
 */
function errorFor(ids, parsed, code, message, data) {
  if (ids.length === 0) return null;
  if (!Array.isArray(parsed)) return stringify(jsonRpcError(ids[0], code, message, data));
  return stringify(ids.map((id) => jsonRpcError(id, code, message, data)));
}

function stringify(obj) {
  // Compact JSON — MCP stdio forbids embedded newlines in a message.
  return JSON.stringify(obj);
}
