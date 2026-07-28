// Verifies the `Lumify-Signature` header webhook deliveries carry (see
// core/webhooks/delivery.py's `_sign`):
//
//   Lumify-Signature: t=<unix_ts>,v1=<hex hmac_sha256(signing_secret, `${ts}.${body}`)>
//
// Uses Web Crypto (`crypto.subtle`), available unflagged in Node 18+ and every
// modern browser/edge runtime — no `node:crypto` import, so this stays portable
// and dependency-free.

export interface VerifyWebhookOptions {
  /** Max age (seconds) a signature is accepted, to reject replayed deliveries. Default 300 (5 min). */
  toleranceSeconds?: number;
  /** Injectable clock for tests. */
  now?: () => number;
}

export class WebhookSignatureError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WebhookSignatureError";
  }
}

function parseSignatureHeader(header: string): { timestamp: number; signature: string } {
  const parts = new Map<string, string>();
  for (const segment of header.split(",")) {
    const [key, value] = segment.split("=", 2);
    if (key && value !== undefined) parts.set(key.trim(), value.trim());
  }
  const t = parts.get("t");
  const v1 = parts.get("v1");
  if (!t || !v1) {
    throw new WebhookSignatureError(
      "Malformed Lumify-Signature header — expected 't=<unix_ts>,v1=<hex_hmac>'."
    );
  }
  const timestamp = Number(t);
  if (!Number.isFinite(timestamp)) {
    throw new WebhookSignatureError("Malformed Lumify-Signature header — 't' is not a number.");
  }
  return { timestamp, signature: v1 };
}

async function hmacSha256Hex(secret: string, payload: string): Promise<string> {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(payload));
  return Array.from(new Uint8Array(sig))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

/** Constant-time string comparison (no early exit on the first mismatched byte). */
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return diff === 0;
}

/**
 * Verify a webhook delivery's `Lumify-Signature` header against the raw
 * request body and your subscription's `signing_secret`. Throws
 * {@link WebhookSignatureError} on any failure (bad format, mismatch, stale
 * timestamp) — treat that as "reject the delivery with a 4xx", not a crash.
 *
 * `body` must be the *raw, unparsed* request bytes/string — re-serializing
 * parsed JSON can reorder keys or change whitespace and break the signature.
 *
 * @example
 * app.post("/webhooks/lumify", express.raw({ type: "*\/*" }), async (req, res) => {
 *   try {
 *     await verifyWebhook(process.env.LUMIFY_WEBHOOK_SECRET!, req.header("Lumify-Signature")!, req.body.toString("utf8"));
 *   } catch {
 *     return res.status(400).end();
 *   }
 *   res.status(200).end();
 * });
 */
export async function verifyWebhook(
  signingSecret: string,
  signatureHeader: string,
  rawBody: string,
  options: VerifyWebhookOptions = {}
): Promise<void> {
  const { timestamp, signature } = parseSignatureHeader(signatureHeader);

  const tolerance = options.toleranceSeconds ?? 300;
  const now = (options.now ?? (() => Date.now() / 1000))();
  if (Math.abs(now - timestamp) > tolerance) {
    throw new WebhookSignatureError(
      `Signature timestamp is ${Math.round(Math.abs(now - timestamp))}s old, outside the ${tolerance}s tolerance (possible replay).`
    );
  }

  const expected = await hmacSha256Hex(signingSecret, `${timestamp}.${rawBody}`);
  if (!timingSafeEqual(expected, signature)) {
    throw new WebhookSignatureError("Signature mismatch — payload may have been tampered with, or the signing secret is wrong.");
  }
}
