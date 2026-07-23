import type { IDataObject } from "n8n-workflow";

// Keep in sync with package.json — used for User-Agent / X-Lumify-Client.
// (Avoid importing package.json so tsc's rootDir stays scoped to source.)
export const PACKAGE_VERSION = "0.2.5";

export const CLIENT_NAME = "n8n-nodes-lumify";
export const CLIENT_UA = `${CLIENT_NAME}/${PACKAGE_VERSION}`;

export const INSTANT_KEY_URL = "https://lumify.ai/docs/ai";
export const REGISTER_URL = "https://lumify.ai/register";
export const BASE_URL_DEFAULT = "https://lumify.ai";

/** Max event IDs accepted by POST /v1/events/batch. */
export const BATCH_MAX_IDS = 25;

/**
 * Strip whitespace / a leading `Bearer ` prefix. Returns `null` when empty.
 * Warns (does not hard-fail) when the key does not start with `lmfy-`.
 */
export function normalizeApiKey(apiKey: unknown): string | null {
  if (typeof apiKey !== "string") {
    return null;
  }
  let key = apiKey.trim();
  if (!key) {
    return null;
  }
  const lower = key.toLowerCase();
  if (lower.startsWith("bearer ")) {
    key = key.slice(7).trim();
  } else if (lower === "bearer") {
    return null;
  }
  if (!key) {
    return null;
  }
  return key;
}

/**
 * Drop undefined/null/empty-string values, and drop non-positive numbers for
 * ID-like filter keys (`season_id`, `team_id`). Keeps `after_id: 0` (valid
 * first-page cursor) and boolean `false`.
 */
export function withDefinedValues(obj: IDataObject): IDataObject {
  const dropZeroKeys = new Set(["season_id", "team_id"]);
  const out: IDataObject = {};
  for (const [key, value] of Object.entries(obj)) {
    if (value === undefined || value === null || value === "") {
      continue;
    }
    if (
      dropZeroKeys.has(key) &&
      typeof value === "number" &&
      !(Number.isFinite(value) && value > 0)
    ) {
      continue;
    }
    out[key] = value;
  }
  return out;
}

/** Parse a comma-separated ID list into positive integers. */
export function parseIdList(raw: string): number[] {
  return raw
    .split(",")
    .map((id) => id.trim())
    .filter((id) => id.length > 0)
    .map((id) => Number(id));
}

export function validatePositiveId(
  id: unknown,
  label: string,
): asserts id is number {
  if (typeof id !== "number" || !Number.isInteger(id) || id <= 0) {
    throw new Error(
      `${label} must be a positive integer (got ${JSON.stringify(id)}). Resolve IDs via List operations first.`,
    );
  }
}

export function validateBatchIds(ids: number[]): number[] {
  if (ids.length === 0) {
    throw new Error(
      "Event IDs is required. Provide a comma-separated list of Lumify event IDs.",
    );
  }
  for (const id of ids) {
    if (!Number.isInteger(id) || id <= 0) {
      throw new Error(
        `Invalid event ID in list: ${JSON.stringify(id)}. Expected positive integers only.`,
      );
    }
  }
  if (ids.length > BATCH_MAX_IDS) {
    throw new Error(
      `Batch accepts at most ${BATCH_MAX_IDS} event IDs (got ${ids.length}).`,
    );
  }
  return ids;
}

/** Best-effort HTTP status extraction from n8n / axios-style errors. */
export function extractHttpStatus(error: unknown): number | null {
  if (!error || typeof error !== "object") {
    return null;
  }
  const e = error as Record<string, unknown>;

  for (const key of ["statusCode", "httpCode", "status"] as const) {
    const v = e[key];
    if (typeof v === "number" && v >= 100 && v < 600) {
      return v;
    }
    if (typeof v === "string" && /^\d{3}$/.test(v)) {
      return Number(v);
    }
  }

  const response = e.response as Record<string, unknown> | undefined;
  if (response) {
    const status = response.status ?? response.statusCode;
    if (typeof status === "number" && status >= 100 && status < 600) {
      return status;
    }
  }

  const message = typeof e.message === "string" ? e.message : "";
  const match = message.match(/\b([45]\d{2})\b/);
  return match ? Number(match[1]) : null;
}

/** Pull a human message from Lumify's JSON error envelope when present. */
export function extractApiMessage(error: unknown): string | null {
  if (!error || typeof error !== "object") {
    return null;
  }
  const e = error as Record<string, unknown>;
  const candidates: unknown[] = [
    e.description,
    e.message,
    (e.response as Record<string, unknown> | undefined)?.body,
    (e.response as Record<string, unknown> | undefined)?.data,
    e.error,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      // Prefer the nested Lumify envelope when the string is raw JSON.
      try {
        const parsed = JSON.parse(candidate) as Record<string, unknown>;
        const nested = extractMessageFromBody(parsed);
        if (nested) {
          return nested;
        }
      } catch {
        // not JSON — fall through
      }
      if (!candidate.startsWith("{") && !candidate.startsWith("[")) {
        return candidate;
      }
    }
    if (candidate && typeof candidate === "object") {
      const nested = extractMessageFromBody(candidate as Record<string, unknown>);
      if (nested) {
        return nested;
      }
    }
  }
  return null;
}

function extractMessageFromBody(body: Record<string, unknown>): string | null {
  const err = body.error;
  if (err && typeof err === "object") {
    const msg = (err as Record<string, unknown>).message;
    if (typeof msg === "string" && msg.trim()) {
      return msg;
    }
  }
  if (typeof body.detail === "string" && body.detail.trim()) {
    return body.detail;
  }
  if (typeof body.message === "string" && body.message.trim()) {
    return body.message;
  }
  return null;
}

/**
 * Map 401/402 into actionable copy. Returns null for other statuses so the
 * caller can rethrow the original error.
 */
export function friendlyAuthError(
  status: number,
  apiMessage: string | null,
): { message: string; description: string } | null {
  if (status === 401) {
    return {
      message: "Invalid or missing Lumify API key",
      description:
        apiMessage ??
        `Check the key in your Lumify credentials. Grab a free instant key (no signup) at ${INSTANT_KEY_URL}.`,
    };
  }
  if (status === 402) {
    return {
      message: "Lumify credit limit reached",
      description:
        apiMessage ??
        `Your key is out of credits. Create a free account at ${REGISTER_URL} for 1,000 additional credits (no card required), or top up an existing account.`,
    };
  }
  return null;
}

/**
 * Unwrap a Lumify list envelope into individual items for n8n looping.
 * Recognizes `events`, `data`, `sports`, and `seasons` array keys.
 */
export function splitEnvelope(
  responseData: unknown,
): IDataObject[] | null {
  if (!responseData || typeof responseData !== "object" || Array.isArray(responseData)) {
    return null;
  }
  const obj = responseData as Record<string, unknown>;
  for (const key of ["events", "data", "sports", "seasons"] as const) {
    const arr = obj[key];
    if (Array.isArray(arr)) {
      return arr.map((entry) =>
        entry && typeof entry === "object"
          ? (entry as IDataObject)
          : ({ value: entry } as IDataObject),
      );
    }
  }
  return null;
}

export function clientHeaders(): Record<string, string> {
  return {
    "User-Agent": CLIENT_UA,
    "X-Lumify-Client": CLIENT_UA,
    "Content-Type": "application/json",
  };
}
