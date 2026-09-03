/**
 * Adversarial / pressure tests — assert hardened wire-format + CLI behavior.
 * Run: node --test test/pressure.test.js
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { createBridge } from "../src/bridge.js";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const BIN = join(ROOT, "bin", "lumify-mcp.js");

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

test("PRESSURE: pretty-printed 200 body is collapsed to one NDJSON line", async () => {
  const pretty = '{\n  "jsonrpc": "2.0",\n  "id": 1,\n  "result": {}\n}';
  const { fetchImpl } = stubFetch({ status: 200, body: pretty });
  const bridge = createBridge({ fetchImpl });
  const out = await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}');
  assert.equal(out.includes("\n"), false);
  assert.deepEqual(JSON.parse(out), { jsonrpc: "2.0", id: 1, result: {} });
});

test("PRESSURE: non-JSON 200 body is rejected as JSON-RPC error", async () => {
  const { fetchImpl } = stubFetch({ status: 200, body: "OK" });
  const bridge = createBridge({ fetchImpl });
  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":1,"method":"ping"}'));
  assert.equal(out.error.code, -32603);
  assert.match(out.error.message, /non-JSON/);
});

test("PRESSURE: id 0 is preserved as a request id", async () => {
  const { fetchImpl } = stubFetch({ status: 500, body: '{"error":{"message":"x"}}' });
  const bridge = createBridge({ fetchImpl });
  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":0,"method":"ping"}'));
  assert.equal(out.id, 0);
});

test("PRESSURE: mixed batch (request + notification) errors only the request ids", async () => {
  const { fetchImpl } = stubFetch({ status: 503, body: '{"error":{"message":"down"}}' });
  const bridge = createBridge({ fetchImpl });
  const batch =
    '[{"jsonrpc":"2.0","id":1,"method":"ping"},{"jsonrpc":"2.0","method":"notifications/cancelled"}]';
  const out = JSON.parse(await bridge.handleMessage(batch));
  assert.ok(Array.isArray(out));
  assert.deepEqual(out.map((e) => e.id), [1]);
});

test("PRESSURE: AbortError / TimeoutError maps to timeout message", async () => {
  const fetchImpl = async () => {
    const err = new Error("The operation was aborted due to timeout");
    err.name = "TimeoutError";
    throw err;
  };
  const bridge = createBridge({ fetchImpl, timeoutMs: 50 });
  const out = JSON.parse(await bridge.handleMessage('{"jsonrpc":"2.0","id":2,"method":"ping"}'));
  assert.match(out.error.message, /Upstream timeout after 50ms/);
});

test("PRESSURE: JSON-RPC error on HTTP 200 passes through (auth/tool errors)", async () => {
  const upstream =
    '{"jsonrpc":"2.0","id":1,"error":{"code":-32001,"message":"Unauthorized: provide a valid Lumify API key as a Bearer token."}}';
  const { fetchImpl } = stubFetch({ status: 200, body: upstream });
  const bridge = createBridge({ fetchImpl });
  const out = await bridge.handleMessage(
    '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_sports","arguments":{}}}',
  );
  assert.equal(out, upstream);
  assert.equal(JSON.parse(out).error.code, -32001);
});

test("PRESSURE: --api-key without value exits 2 with a clear error", async () => {
  const child = spawn(process.execPath, [BIN, "--api-key"], {
    stdio: ["ignore", "pipe", "pipe"],
  });
  let stderr = "";
  child.stderr.on("data", (d) => (stderr += d));
  const code = await new Promise((resolve) => child.on("close", resolve));
  assert.equal(code, 2);
  assert.match(stderr, /--api-key requires a value/);
});

test("PRESSURE: --help and --version write to stderr, not stdout", async () => {
  for (const flag of ["--help", "--version"]) {
    const child = spawn(process.execPath, [BIN, flag], {
      stdio: ["ignore", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (d) => (stdout += d));
    child.stderr.on("data", (d) => (stderr += d));
    const code = await new Promise((resolve) => child.on("close", resolve));
    assert.equal(code, 0, flag);
    assert.equal(stdout, "", `${flag} must not write to stdout`);
    assert.ok(stderr.length > 0, `${flag} should write to stderr`);
  }
});

test("PRESSURE: concurrent handleMessage replies stay valid JSON lines", async () => {
  let n = 0;
  const { fetchImpl } = stubFetch(() => {
    const id = ++n;
    return {
      status: 200,
      body: JSON.stringify({
        jsonrpc: "2.0",
        id,
        result: { pad: "x".repeat(2048), n: id },
      }),
    };
  });
  const bridge = createBridge({ fetchImpl });
  const msgs = Array.from({ length: 20 }, (_, i) =>
    JSON.stringify({ jsonrpc: "2.0", id: i + 1, method: "ping" }),
  );
  const outs = await Promise.all(msgs.map((m) => bridge.handleMessage(m)));
  for (const o of outs) {
    assert.ok(o && !o.includes("\n"), "each reply must be a single line");
    const parsed = JSON.parse(o);
    assert.equal(parsed.jsonrpc, "2.0");
    assert.ok(parsed.result);
  }
});

test("PRESSURE: body sent upstream is the trimmed line (no surrounding whitespace)", async () => {
  const { fetchImpl, calls } = stubFetch({ status: 200, body: '{"jsonrpc":"2.0","id":1,"result":{}}' });
  const bridge = createBridge({ fetchImpl });
  await bridge.handleMessage('  {"jsonrpc":"2.0","id":1,"method":"ping"}  ');
  assert.equal(calls[0].opts.body, '{"jsonrpc":"2.0","id":1,"method":"ping"}');
});
