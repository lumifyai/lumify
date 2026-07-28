#!/usr/bin/env node
// lumify-mcp — run the hosted Lumify MCP server locally over stdio.
//
//   npx @lumifyai/mcp                     # key from $LUMIFY_API_KEY
//   npx @lumifyai/mcp --api-key lmfy-...  # key inline
//
// Wire it into an MCP client (Cursor, Claude Desktop, …) as a stdio command.
// See the README for ready-to-paste client config.

import { createInterface } from "node:readline";
import { createRequire } from "node:module";
import { once } from "node:events";

import { createBridge, DEFAULT_MCP_URL } from "../src/bridge.js";

const require = createRequire(import.meta.url);
const pkg = require("../package.json");

function parseArgs(argv) {
  const out = {
    apiKey: undefined,
    url: undefined,
    help: false,
    version: false,
    error: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") out.help = true;
    else if (a === "--version" || a === "-v") out.version = true;
    else if (a === "--api-key") {
      const v = argv[++i];
      if (!v || v.startsWith("-")) {
        out.error = "--api-key requires a value (e.g. --api-key lmfy-...)";
        return out;
      }
      out.apiKey = v;
    } else if (a.startsWith("--api-key=")) {
      const v = a.slice("--api-key=".length);
      if (!v) {
        out.error = "--api-key requires a value (e.g. --api-key=lmfy-...)";
        return out;
      }
      out.apiKey = v;
    } else if (a === "--url") {
      const v = argv[++i];
      if (!v || v.startsWith("-")) {
        out.error = "--url requires a value";
        return out;
      }
      out.url = v;
    } else if (a.startsWith("--url=")) {
      const v = a.slice("--url=".length);
      if (!v) {
        out.error = "--url requires a value";
        return out;
      }
      out.url = v;
    } else {
      out.error = `unknown argument '${a}'`;
      return out;
    }
  }
  return out;
}

const USAGE = `lumify-mcp v${pkg.version} — local stdio bridge to the hosted Lumify MCP server

Usage:
  lumify-mcp [--api-key lmfy-...] [--url <endpoint>]

Options:
  --api-key <key>   Lumify API key (or set LUMIFY_API_KEY). Create one at
                    https://lumify.ai/api-keys. Handshake works without a key;
                    tool calls require it.
  --url <endpoint>  Override the upstream MCP endpoint (or set LUMIFY_MCP_URL).
                    Default: ${DEFAULT_MCP_URL}
  -h, --help        Show this help.
  -v, --version     Print the version.

The process speaks the MCP stdio transport on stdin/stdout; all diagnostics go
to stderr. Configure it as a stdio MCP server in your client — see the README.
`;

/**
 * Serialize writes to stdout so concurrent replies never interleave under
 * backpressure (MCP stdio is newline-delimited; a split write would corrupt
 * framing).
 */
function createStdoutWriter(stream = process.stdout) {
  let chain = Promise.resolve();
  return function writeLine(line) {
    chain = chain.then(async () => {
      if (!stream.write(line + "\n")) {
        await once(stream, "drain");
      }
    });
    return chain;
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.error) {
    process.stderr.write(`lumify-mcp: ${args.error}\n`);
    process.stderr.write(`Try 'lumify-mcp --help' for usage.\n`);
    process.exit(2);
  }

  if (args.help) {
    // Help is a human CLI path — write to stderr so a misconfigured MCP client
    // never sees non-protocol bytes on stdout.
    process.stderr.write(USAGE);
    return;
  }
  if (args.version) {
    process.stderr.write(`${pkg.version}\n`);
    return;
  }

  const apiKey = args.apiKey || process.env.LUMIFY_API_KEY;
  const url = args.url || process.env.LUMIFY_MCP_URL || DEFAULT_MCP_URL;

  const bridge = createBridge({
    url,
    apiKey,
    userAgent: `${pkg.name}/${pkg.version} (node ${process.version})`,
  });
  const writeLine = createStdoutWriter();

  // Startup diagnostics on stderr only — stdout is reserved for the protocol.
  process.stderr.write(`lumify-mcp v${pkg.version} → ${bridge.endpoint}\n`);
  if (!apiKey) {
    process.stderr.write(
      "lumify-mcp: no API key set (LUMIFY_API_KEY or --api-key). The handshake " +
        "will work, but tools/call will return an unauthorized error until a key " +
        "is provided.\n",
    );
  }

  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });

  // Track in-flight requests so a stdin close (client gone / piped input) drains
  // pending replies before exiting instead of truncating them.
  const pending = new Set();

  rl.on("line", (line) => {
    // Handle upstream concurrently; serialize only the stdout write so
    // JSON-RPC id-matching stays correct without interleaved NDJSON lines.
    const p = bridge
      .handleMessage(line)
      .then(async (reply) => {
        if (reply != null) await writeLine(reply);
      })
      .catch((err) => {
        process.stderr.write(`lumify-mcp: unexpected error: ${(err && err.stack) || err}\n`);
      })
      .finally(() => pending.delete(p));
    pending.add(p);
  });

  rl.on("close", async () => {
    await Promise.allSettled([...pending]);
    process.exit(0);
  });
}

main();
