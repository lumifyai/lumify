import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { LumifyClient, DEFAULT_BASE_URL } from "../dist/client.js";
import { AuthenticationError, NotFoundError, RateLimitError, ValidationError, ConnectionError, PaymentError, APIError } from "../dist/errors.js";
import { getMeta } from "../dist/meta.js";
import { fakeFetch } from "./_helpers.js";

describe("LumifyClient — request construction", () => {
  test("requires an apiKey", () => {
    assert.throws(() => new LumifyClient({ apiKey: "" }), /apiKey.*required/i);
  });

  test("defaults to https://lumify.ai and strips trailing slash overrides", () => {
    const c1 = new LumifyClient({ apiKey: "k" });
    assert.equal(c1.baseUrl, DEFAULT_BASE_URL);
    const c2 = new LumifyClient({ apiKey: "k", baseUrl: "https://example.test/" });
    assert.equal(c2.baseUrl, "https://example.test");
  });

  test("sends Bearer auth, Accept, and User-Agent headers", async () => {
    const fetch = fakeFetch([{ status: 200, body: { ok: true } }]);
    const client = new LumifyClient({ apiKey: "lmfy-abc", fetch });
    await client.get("/v1/sports");
    const { init } = fetch.calls[0];
    assert.equal(init.headers.Authorization, "Bearer lmfy-abc");
    assert.equal(init.headers.Accept, "application/json");
    assert.match(init.headers["User-Agent"], /^lumify-sdk-js\//);
  });

  test("serializes query params, skipping null/undefined", async () => {
    const fetch = fakeFetch([{ status: 200, body: {} }]);
    const client = new LumifyClient({ apiKey: "k", fetch });
    await client.get("/v1/events", { query: { sport: "nfl", season_id: undefined, limit: 10, active: false } });
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.searchParams.get("sport"), "nfl");
    assert.equal(url.searchParams.has("season_id"), false);
    assert.equal(url.searchParams.get("limit"), "10");
    assert.equal(url.searchParams.get("active"), "false");
  });

  test("POST sends a JSON body with Content-Type", async () => {
    const fetch = fakeFetch([{ status: 200, body: { id: 1 } }]);
    const client = new LumifyClient({ apiKey: "k", fetch });
    await client.post("/v1/webhooks", { body: { url: "https://x.test/hook" } });
    const { init } = fetch.calls[0];
    assert.equal(init.headers["Content-Type"], "application/json");
    assert.deepEqual(JSON.parse(init.body), { url: "https://x.test/hook" });
  });
});

describe("LumifyClient — response meta", () => {
  test("attaches X-Credits/X-RateLimit headers to the parsed body via getMeta()", async () => {
    const fetch = fakeFetch([
      {
        status: 200,
        body: { data: [] },
        headers: {
          "X-Credits-Used": "1",
          "X-Credits-Remaining": "499",
          "X-RateLimit-Limit": "60",
          "X-RateLimit-Remaining": "59",
          "X-RateLimit-Reset": "1234567890",
        },
      },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch });
    const result = await client.get("/v1/sports");
    const meta = getMeta(result);
    assert.equal(meta.creditsUsed, 1);
    assert.equal(meta.creditsRemaining, 499);
    assert.equal(meta.rateLimitLimit, 60);
    assert.equal(meta.rateLimitRemaining, 59);
    assert.equal(meta.rateLimitReset, 1234567890);
  });

  test("getMeta() on a value with no attached meta returns undefined", () => {
    assert.equal(getMeta({}), undefined);
    assert.equal(getMeta(42), undefined);
    assert.equal(getMeta(null), undefined);
  });

  test("billing fairness: unavailable-data reads carry X-Credits-Used: 0", async () => {
    const fetch = fakeFetch([{ status: 200, body: { available: false }, headers: { "X-Credits-Used": "0" } }]);
    const client = new LumifyClient({ apiKey: "k", fetch });
    const odds = await client.get("/v1/events/1/odds");
    assert.equal(getMeta(odds).creditsUsed, 0);
  });
});

describe("LumifyClient — error envelope mapping", () => {
  const cases = [
    [401, "unauthorized", AuthenticationError],
    [404, "not_found", NotFoundError],
    [422, "validation_error", ValidationError],
    [429, "rate_limit_exceeded", RateLimitError],
  ];

  for (const [status, code, ErrorClass] of cases) {
    test(`${status} -> ${ErrorClass.name}`, async () => {
      const fetch = fakeFetch([
        {
          status,
          body: { error: { code, message: "boom", status, doc_url: "https://lumify.ai/docs/reference#error-codes" }, detail: "boom" },
        },
      ]);
      const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
      await assert.rejects(client.get("/v1/x"), (err) => {
        assert.ok(err instanceof ErrorClass);
        assert.equal(err.code, code);
        assert.equal(err.status, status);
        return true;
      });
    });
  }

  test("429 exposes retryAfter from error.retry_after", async () => {
    const fetch = fakeFetch([
      { status: 429, body: { error: { code: "rate_limit_exceeded", message: "slow down", status: 429, retry_after: 3 } } },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), (err) => {
      assert.equal(err.retryAfter, 3);
      return true;
    });
  });

  test("429 prefers Retry-After header when the envelope omits retry_after", async () => {
    const fetch = fakeFetch([
      {
        status: 429,
        headers: { "Retry-After": "7" },
        body: { error: { code: "rate_limit_exceeded", message: "slow down", status: 429 } },
      },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), (err) => {
      assert.ok(err instanceof RateLimitError);
      assert.equal(err.retryAfter, 7);
      return true;
    });
  });

  test("402 maps to PaymentError", async () => {
    const fetch = fakeFetch([
      { status: 402, body: { error: { code: "payment_required", message: "top up", status: 402 } } },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), PaymentError);
  });

  test("non-JSON 200 body throws APIError (does not return undefined)", async () => {
    const fetch = fakeFetch([{ status: 200, rawText: "<html>oops</html>" }]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), (err) => {
      assert.ok(err instanceof APIError);
      assert.equal(err.code, "invalid_response");
      return true;
    });
  });

  test("403 sport-scope denial exposes upgradeUrl", async () => {
    const fetch = fakeFetch([
      {
        status: 403,
        body: { error: { code: "sport_scope_denied", message: "nope", status: 403, upgrade_url: "https://lumify.ai/pricing" } },
      },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), (err) => {
      assert.equal(err.upgradeUrl, "https://lumify.ai/pricing");
      return true;
    });
  });

  test("network failure surfaces as ConnectionError, not a crash", async () => {
    const fetch = fakeFetch([{ throw: new Error("ECONNRESET") }]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 0 });
    await assert.rejects(client.get("/v1/x"), ConnectionError);
  });
});

describe("LumifyClient — retries", () => {
  test("retries a GET on 429 up to maxRetries, then succeeds", async () => {
    const fetch = fakeFetch([
      { status: 429, body: { error: { code: "rate_limit_exceeded", message: "slow down", status: 429, retry_after: 0 } } },
      { status: 200, body: { data: [] } },
    ]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 2 });
    const result = await client.get("/v1/sports");
    assert.deepEqual(result, { data: [] });
    assert.equal(fetch.calls.length, 2);
  });

  test("retries a GET on 500, then exhausts retries and throws", async () => {
    const fetch = fakeFetch(() => ({ status: 500, body: { error: { code: "internal_error", message: "oops", status: 500 } } }));
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 2 });
    await assert.rejects(client.get("/v1/sports"));
    assert.equal(fetch.calls.length, 3); // initial + 2 retries
  });

  test("does not retry a non-idempotent POST on 500", async () => {
    const fetch = fakeFetch([{ status: 500, body: { error: { code: "internal_error", message: "oops", status: 500 } } }]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 2 });
    await assert.rejects(client.post("/v1/webhooks", { body: {} }));
    assert.equal(fetch.calls.length, 1);
  });

  test("does not retry on 404 (not a transient error)", async () => {
    const fetch = fakeFetch([{ status: 404, body: { error: { code: "not_found", message: "nope", status: 404 } } }]);
    const client = new LumifyClient({ apiKey: "k", fetch, maxRetries: 2 });
    await assert.rejects(client.get("/v1/x"));
    assert.equal(fetch.calls.length, 1);
  });
});
