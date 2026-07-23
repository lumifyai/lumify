// G6 sync gate (SDK arm) — the SDK must build exactly the REST request declared
// in the shared cross-surface probe matrix. This consumes the SAME fixture the
// Python REST↔MCP parity test uses (tests/fixtures/agent_contract.json), so the
// SDK can't silently drift from the REST contract that REST and MCP agree on.
//
// This asserts request *construction* (method + path + query), not live data:
// the SDK is TypeScript and can't reach the in-process Python SQLite app, so
// data/credit parity is owned by the Python test. Together they close the loop:
// REST ⇄ MCP agree on data+credits+envelopes; SDK ⇄ REST agree on the wire call.

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { Lumify } from "../dist/lumify.js";
import { fakeFetch } from "./_helpers.js";

const fixture = JSON.parse(
  readFileSync(new URL("../../../tests/fixtures/agent_contract.json", import.meta.url))
);

/** Invoke `client[resource][method](...args)` for a probe's sdk recipe. */
function invoke(client, sdk) {
  const resource = client[sdk.resource];
  assert.ok(resource, `SDK has no resource '${sdk.resource}'`);
  const fn = resource[sdk.method];
  assert.equal(typeof fn, "function", `SDK ${sdk.resource}.${sdk.method} is not a method`);
  return fn.apply(resource, sdk.args ?? []);
}

describe("agent-contract — SDK builds the REST request declared in the shared matrix", () => {
  for (const probe of fixture.probes) {
    if (!probe.sdk) continue;

    test(probe.name, async () => {
      const isError = probe.kind === "error";
      const canned = isError
        ? { status: probe.assert.rest_status, body: { error: { code: probe.assert.error_code, status: probe.assert.rest_status } } }
        : { status: 200, body: {} };
      const fetch = fakeFetch([canned]);
      const client = new Lumify({ apiKey: "lmfy-test", fetch, maxRetries: 0 });

      // Error probes reject (NotFoundError etc.) — the request is still recorded
      // by fakeFetch before the throw, which is all we're asserting here.
      try {
        await invoke(client, probe.sdk);
      } catch (err) {
        if (!isError) throw err;
      }

      assert.equal(fetch.calls.length, 1, `${probe.name}: expected exactly one request`);
      const { url, init } = fetch.calls[0];
      const parsed = new URL(url);

      assert.equal(init.method, probe.rest.method, `${probe.name}: HTTP method`);
      assert.equal(parsed.pathname, probe.rest.path, `${probe.name}: path`);

      const actualQuery = Object.fromEntries(parsed.searchParams.entries());
      assert.deepEqual(
        actualQuery,
        probe.rest.query ?? {},
        `${probe.name}: query params must match the REST contract exactly`
      );

      if (probe.rest.body !== undefined) {
        const actualBody = init.body ? JSON.parse(init.body) : undefined;
        assert.deepEqual(
          actualBody,
          probe.rest.body,
          `${probe.name}: request body must match the REST contract exactly`
        );
      }
    });
  }
});
