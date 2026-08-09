import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { errorFromResponse, APIError, LumifyError, PaymentError, RateLimitError } from "../dist/errors.js";

describe("errorFromResponse()", () => {
  test("500 maps to APIError, an instance of the LumifyError base", () => {
    const err = errorFromResponse(500, { code: "internal_error", message: "boom", status: 500 }, null);
    assert.ok(err instanceof APIError);
    assert.ok(err instanceof LumifyError);
    assert.equal(err.code, "internal_error");
  });

  test("402 maps to PaymentError", () => {
    const err = errorFromResponse(402, { code: "payment_required", message: "top up", status: 402 }, null);
    assert.ok(err instanceof PaymentError);
    assert.equal(err.code, "payment_required");
  });

  test("402 PaymentError exposes upgradeUrl and topupUrl", () => {
    const err = errorFromResponse(
      402,
      {
        code: "insufficient_credits",
        message: "top up",
        status: 402,
        upgrade_url: "https://lumify.ai/pricing",
        topup_url: "https://lumify.ai/dashboard",
      },
      null,
    );
    assert.ok(err instanceof PaymentError);
    assert.equal(err.upgradeUrl, "https://lumify.ai/pricing");
    assert.equal(err.topupUrl, "https://lumify.ai/dashboard");
  });

  test("429 uses Retry-After header when envelope omits retry_after", () => {
    const err = errorFromResponse(
      429,
      { code: "rate_limit_exceeded", message: "slow", status: 429 },
      null,
      { retryAfterHeader: 9 }
    );
    assert.ok(err instanceof RateLimitError);
    assert.equal(err.retryAfter, 9);
  });

  test("falls back gracefully when the payload is missing (non-JSON error body)", () => {
    const err = errorFromResponse(503, undefined, null);
    assert.equal(err.code, "http_503");
    assert.match(err.message, /503/);
  });

  test("carries the request id through when present", () => {
    const err = errorFromResponse(404, { code: "not_found", message: "gone", status: 404 }, "req-abc");
    assert.equal(err.requestId, "req-abc");
  });

  test("ValidationError exposes structured fieldErrors", () => {
    const err = errorFromResponse(
      422,
      {
        code: "validation_error",
        message: "limit: must be <= 100",
        status: 422,
        errors: [{ field: "limit", message: "must be <= 100", type: "value_error" }],
      },
      null
    );
    assert.equal(err.fieldErrors.length, 1);
    assert.equal(err.fieldErrors[0].field, "limit");
  });
});
