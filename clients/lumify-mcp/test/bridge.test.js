import { test } from "node:test";
import assert from "node:assert/strict";

import { createBridge, DEFAULT_MCP_URL } from "../src/bridge.js";

// Build a fetch stub that records calls and returns a canned Response-like object.
function stubFetch(responder) {
  const calls = [];
  const fetchImpl = async (url, opts) => {
    calls.push({ url, opts });
    const r = typeof responder === "function" ? responder(url, opts) : responder;
    return {
      ok: r.status >= 200 && r.status < 300,
      status: r.status,
      text: async () => r.body ?? "",
    };
  };
  return { fetchImpl, calls };
}

test("passes a successful JSON-RPC response through (compact, single-line)", async () => {
  const upstream = '{"jsonrpc":"2.0","id":1,"result":{"tools":[]}}';
  const { fetchImpl } = stubFetch({ status: 200, body: upstream });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"tools/list"}');
  assert.equal(out, upstream);
  assert.ok(!out.includes("\n"));
});

test("re-serializes pretty-printed 200 bodies to a single NDJSON line", async () => {
  const pretty = '{\n  "jsonrpc": "2.0",\n  "id": 1,\n  "result": { "ok": true }\n}';
  const { fetchImpl } = stubFetch({ status: 200, body: pretty });
  const bridge = createBridge({ fetchImpl });
  const out = await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}');
  assert.ok(!out.includes("\n"));
  assert.deepEqual(JSON.parse(out), { jsonrpc: "2.0", id: 1, result: { ok: true } });
});

test("non-JSON 200 body becomes a JSON-RPC -32603 (never plaintext on stdout)", async () => {
  const { fetchImpl } = stubFetch({ status: 200, body: "<html>ok</html>" });
  const bridge = createBridge({ fetchImpl });
  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}'));
  assert.equal(out.error.code, -32603);
  assert.match(out.error.message, /non-JSON/);
});

test("returns null for a notification-only 202 (nothing to answer)", async () => {
  const { fetchImpl } = stubFetch({ status: 202, body: "" });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = await bridge.handleMessage('{"jsonrpc":"2.0","method":"notifications/initialized"}');
  assert.equal(out, null);
});

test("blank input yields no output", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: "{}" });
  const bridge = createBridge({ fetchImpl });
  assert.equal(await bridge.handleMessage("   "), null);
  assert.equal(calls.length, 0, "must not contact upstream on empty input");
});

test("malformed JSON never hits upstream and returns a parse error", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: "{}" });
  const bridge = createBridge({ fetchImpl });

  const out = JSON.parse(await bridge.handleMessage("{not json"));
  assert.equal(out.error.code, -32700);
  assert.equal(out.id, null);
  assert.equal(calls.length, 0);
});

test("attaches the Bearer token, endpoint, and JSON headers", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: '{"jsonrpc":"2.0","id":1,"result":{}}' });
  const bridge = createBridge({ apiKey: "lmfy-abc.def", fetchImpl });

  await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}');
  const { url, opts } = calls[0];
  assert.equal(url, DEFAULT_MCP_URL);
  assert.equal(opts.method, "POST");
  assert.equal(opts.headers.Authorization, "Bearer lmfy-abc.def");
  assert.equal(opts.headers.Accept, "application/json");
  assert.equal(opts.headers["Content-Type"], "application/json");
  assert.equal("MCP-Protocol-Version" in opts.headers, false);
});

test("pins MCP-Protocol-Version after initialize", async () => {
  const initBody = JSON.stringify({
    jsonrpc: "2.0",
    id: 1,
    result: {
      protocolVersion: "2025-06-18",
      capabilities: {},
      serverInfo: { name: "lumify-mcp", version: "1.0.0" },
    },
  });
  const { fetchImpl, calls } = stubFetch((url, opts) => {
    const body = JSON.parse(opts.body);
    if (body.method === "initialize") return { status: 200, body: initBody };
    return { status: 200, body: '{"jsonrpc":"2.0","id":2,"result":{}}' };
  });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  await bridge.handleMessage(
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}',
  );
  assert.equal(bridge.getProtocolVersion(), "2025-06-18");

  await bridge.handleMessage('{"jsonrpc":"2.0","id":2,"method":"ping"}');
  assert.equal(calls[1].opts.headers["MCP-Protocol-Version"], "2025-06-18");
});

test("omits Authorization when no key is configured", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: '{"jsonrpc":"2.0","id":1,"result":{}}' });
  const bridge = createBridge({ fetchImpl });

  await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"tools/list"}');
  assert.equal("Authorization" in calls[0].opts.headers, false);
});

test("maps a 429 envelope to a JSON-RPC error with retry_after", async () => {
  const body = JSON.stringify({
    error: { code: "rate_limit_exceeded", message: "Rate limit exceeded", retry_after: 60 },
    detail: "Rate limit exceeded",
  });
  const { fetchImpl } = stubFetch({ status: 429, body });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":7,"method":"tools/call","params":{"name":"list_sports","arguments":{}}}'));
  assert.equal(out.id, 7);
  assert.equal(out.error.code, -32603);
  assert.match(out.error.message, /HTTP 429/);
  assert.match(out.error.message, /retry after 60s/);
  assert.equal(out.error.data.retry_after, 60);
  assert.equal(out.error.data.upstream_code, "rate_limit_exceeded");
});

test("maps a non-JSON error body (edge HTML) to a status-only error", async () => {
  const { fetchImpl } = stubFetch({ status: 502, body: "<html>bad gateway</html>" });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":3,"method":"ping"}'));
  assert.equal(out.error.code, -32603);
  assert.equal(out.error.message, "HTTP 502");
  assert.equal(out.id, 3);
});

test("a failed batch produces one error per request id", async () => {
  const { fetchImpl } = stubFetch({ status: 500, body: '{"error":{"message":"boom"}}' });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const batch = '[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","id":2,"method":"ping"}]';
  const out = JSON.parse(await bridge.handleMessage(batch));
  assert.ok(Array.isArray(out));
  assert.deepEqual(out.map((e) => e.id), [1, 2]);
  assert.ok(out.every((e) => e.error.code === -32603));
});

test("a failed notification-only message has nothing to answer", async () => {
  const { fetchImpl } = stubFetch({ status: 500, body: '{"error":{"message":"boom"}}' });
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = await bridge.handleMessage('{"jsonrpc":"2.0","method":"notifications/cancelled"}');
  assert.equal(out, null);
});

test("network failure becomes an internal JSON-RPC error", async () => {
  const fetchImpl = async () => {
    throw new Error("ECONNREFUSED");
  };
  const bridge = createBridge({ apiKey: "lmfy-x.y", fetchImpl });

  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":9,"method":"ping"}'));
  assert.equal(out.id, 9);
  assert.equal(out.error.code, -32603);
  assert.match(out.error.message, /Upstream request failed/);
});

test("honors a custom endpoint url", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: '{"jsonrpc":"2.0","id":1,"result":{}}' });
  const bridge = createBridge({ url: "https://staging.lumify.ai/mcp", fetchImpl });
  await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}');
  assert.equal(calls[0].url, "https://staging.lumify.ai/mcp");
});
