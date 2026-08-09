const test = require("node:test");
const assert = require("node:assert/strict");

const {
  normalizeApiKey,
  withDefinedValues,
  parseIdList,
  validatePositiveId,
  validateBatchIds,
  extractHttpStatus,
  extractApiMessage,
  friendlyAuthError,
  splitEnvelope,
  clientHeaders,
  BATCH_MAX_IDS,
  INSTANT_KEY_URL,
  REGISTER_URL,
} = require("../dist/nodes/Lumify/helpers.js");

test("normalizeApiKey strips whitespace and Bearer prefix", () => {
  assert.equal(normalizeApiKey("  lmfy-abc  "), "lmfy-abc");
  assert.equal(normalizeApiKey("Bearer lmfy-abc"), "lmfy-abc");
  assert.equal(normalizeApiKey("bearer lmfy-abc"), "lmfy-abc");
  assert.equal(normalizeApiKey("Bearer"), null);
  assert.equal(normalizeApiKey("   "), null);
  assert.equal(normalizeApiKey(null), null);
  assert.equal(normalizeApiKey(undefined), null);
});

test("withDefinedValues drops empty strings and non-positive ID filters", () => {
  assert.deepEqual(
    withDefinedValues({
      sport: "nfl",
      league: "",
      season_id: 0,
      team_id: -1,
      after_id: 0,
      include_scores: false,
      has_recommend: true,
    }),
    {
      sport: "nfl",
      after_id: 0,
      include_scores: false,
      has_recommend: true,
    },
  );
});

test("parseIdList and validateBatchIds enforce positive ints and max size", () => {
  assert.deepEqual(parseIdList("1, 2, 3"), [1, 2, 3]);
  assert.deepEqual(validateBatchIds([1, 2]), [1, 2]);
  assert.throws(() => validateBatchIds([]), /required/i);
  assert.throws(() => validateBatchIds([1, NaN]), /Invalid event ID/);
  assert.throws(() => validateBatchIds([0, 1]), /Invalid event ID/);
  assert.throws(
    () => validateBatchIds(Array.from({ length: BATCH_MAX_IDS + 1 }, (_, i) => i + 1)),
    new RegExp(String(BATCH_MAX_IDS)),
  );
});

test("validatePositiveId rejects zero and non-integers", () => {
  assert.doesNotThrow(() => validatePositiveId(42, "Event ID"));
  assert.throws(() => validatePositiveId(0, "Event ID"), /positive integer/);
  assert.throws(() => validatePositiveId(1.5, "Event ID"), /positive integer/);
});

test("extractHttpStatus reads statusCode / response.status / message", () => {
  assert.equal(extractHttpStatus({ statusCode: 401 }), 401);
  assert.equal(extractHttpStatus({ httpCode: "402" }), 402);
  assert.equal(extractHttpStatus({ response: { status: 404 } }), 404);
  assert.equal(extractHttpStatus({ message: "Request failed with status code 402" }), 402);
  assert.equal(extractHttpStatus({ message: "nope" }), null);
});

test("extractApiMessage prefers Lumify error envelope", () => {
  assert.equal(
    extractApiMessage({
      response: {
        body: {
          error: { code: "insufficient_credits", message: "Out of credits." },
        },
      },
    }),
    "Out of credits.",
  );
  assert.equal(
    extractApiMessage({
      message: JSON.stringify({
        error: { message: "Invalid or inactive API key." },
      }),
    }),
    "Invalid or inactive API key.",
  );
});

test("friendlyAuthError maps 401/402 with CTAs", () => {
  const unauthorized = friendlyAuthError(401, null);
  assert.match(unauthorized.message, /API key/i);
  assert.match(unauthorized.description, new RegExp(INSTANT_KEY_URL.replace(/\./g, "\\.")));

  const payment = friendlyAuthError(402, "Your instant trial's 100 credits are used up.");
  assert.match(payment.message, /credit/i);
  assert.equal(
    payment.description,
    "Your instant trial's 100 credits are used up.",
  );
  // Fallback CTA when API message missing
  const paymentFallback = friendlyAuthError(402, null);
  assert.match(paymentFallback.description, new RegExp(REGISTER_URL.replace(/\./g, "\\.")));

  assert.equal(friendlyAuthError(500, null), null);
});

test("splitEnvelope unwraps known list keys", () => {
  assert.deepEqual(splitEnvelope({ events: [{ id: 1 }, { id: 2 }] }), [
    { id: 1 },
    { id: 2 },
  ]);
  assert.deepEqual(splitEnvelope({ data: [{ id: 9 }] }), [{ id: 9 }]);
  assert.deepEqual(splitEnvelope({ sports: [{ slug: "nfl" }] }), [
    { slug: "nfl" },
  ]);
  assert.deepEqual(splitEnvelope({ seasons: [{ id: 3 }] }), [{ id: 3 }]);
  assert.equal(splitEnvelope({ total: 0 }), null);
  assert.equal(splitEnvelope([{ id: 1 }]), null);
});

test("clientHeaders identify the n8n package", () => {
  const headers = clientHeaders();
  assert.match(headers["User-Agent"], /^n8n-nodes-lumify\//);
  assert.equal(headers["User-Agent"], headers["X-Lumify-Client"]);
  assert.equal(headers["Content-Type"], "application/json");
});
