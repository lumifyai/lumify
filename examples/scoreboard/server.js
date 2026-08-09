/**
 * Live scoreboard demo — small Express proxy in front of the Lumify API.
 *
 * Why a proxy? Lumify keys must stay server-side. The browser talks only to
 * this local origin; we forward authenticated calls to https://lumify.ai.
 *
 * Endpoints:
 *   GET /api/live-games[?sport=nba]  — discover in-progress events
 *   GET /api/games/:id/score         — one-shot score snapshot (poll fallback)
 *   GET /api/games/:id/stream        — SSE proxy of Lumify's /v1/events/{id}/stream
 */
import "dotenv/config";
import express from "express";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Lumify } from "@lumifyai/sdk";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT) || 3000;
const API_KEY = process.env.LUMIFY_API_KEY;

if (!API_KEY || !API_KEY.startsWith("lmfy-") || API_KEY.includes("your-key")) {
  console.error(
    [
      "Missing LUMIFY_API_KEY.",
      "  1. Copy .env.example → .env",
      "  2. Paste a key from https://lumify.ai/docs (instant trial) or /api-keys",
      "  3. npm start",
    ].join("\n")
  );
  process.exit(1);
}

const client = new Lumify({ apiKey: API_KEY });
const app = express();

app.use(express.static(path.join(__dirname, "public")));

/**
 * Discover live games.
 * Proxies: GET /v1/events?status=inprogress&include_scores=true&sort=status
 */
app.get("/api/live-games", async (req, res) => {
  try {
    const sport = typeof req.query.sport === "string" ? req.query.sport : undefined;
    const data = await client.events.list({
      sport,
      status: "inprogress",
      includeScores: true,
      sort: "status",
      limit: 50,
    });
    res.json(data);
  } catch (err) {
    sendApiError(res, err, "Failed to list live games");
  }
});

/**
 * One-shot score snapshot — used as a polling fallback when EventSource
 * isn't available. Proxies: GET /v1/events/{id}/score
 */
app.get("/api/games/:id/score", async (req, res) => {
  const eventId = Number(req.params.id);
  if (!Number.isFinite(eventId)) {
    return res.status(400).json({ error: "Invalid event id" });
  }
  try {
    const data = await client.events.score(eventId);
    res.json(data);
  } catch (err) {
    sendApiError(res, err, "Failed to fetch score");
  }
});

/**
 * SSE proxy. The browser EventSource connects here (same origin, no key).
 * We open Lumify's authenticated stream with @lumifyai/sdk, which auto-
 * reconnects across the 5-minute server cap, and re-emit frames.
 *
 * Proxies: GET /v1/events/{id}/stream
 */
app.get("/api/games/:id/stream", async (req, res) => {
  const eventId = Number(req.params.id);
  if (!Number.isFinite(eventId)) {
    return res.status(400).json({ error: "Invalid event id" });
  }

  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.flushHeaders?.();

  // Keep-alive comment so intermediaries don't idle-close the pipe.
  const keepalive = setInterval(() => {
    res.write(": keepalive\n\n");
  }, 15000);

  const abort = new AbortController();
  req.on("close", () => {
    clearInterval(keepalive);
    abort.abort();
  });

  try {
    for await (const evt of client.events.stream(eventId, {
      signal: abort.signal,
    })) {
      // Re-emit as a named SSE event so the browser can switch on evt.event.
      const payload = evt.data === undefined ? "" : JSON.stringify(evt.data);
      res.write(`event: ${evt.event}\ndata: ${payload}\n\n`);

      // Game over — close the browser stream. (SDK already stops iterating.)
      if (evt.event === "done" || evt.event === "error") break;
      // `reconnect` is informational: the SDK already opened a fresh Lumify
      // connection. Forward it so the UI can show a brief "reconnecting" state.
    }
  } catch (err) {
    if (!abort.signal.aborted) {
      const message = err instanceof Error ? err.message : "stream error";
      res.write(`event: error\ndata: ${JSON.stringify({ message })}\n\n`);
    }
  } finally {
    clearInterval(keepalive);
    if (!res.writableEnded) res.end();
  }
});

app.listen(PORT, () => {
  console.log(`Live scoreboard running at http://localhost:${PORT}`);
  console.log("API key stays on this server — the browser never sees it.");
});

function sendApiError(res, err, fallback) {
  const status = Number(err?.status) || 502;
  const retryAfter = err?.headers?.get?.("retry-after") || err?.retryAfter;
  if (retryAfter) res.setHeader("Retry-After", String(retryAfter));
  // Surface rate-limit headers when the SDK exposes them.
  const limit = err?.headers?.get?.("x-ratelimit-remaining");
  if (limit != null) res.setHeader("X-RateLimit-Remaining", String(limit));

  console.error(fallback, err);
  res.status(status).json({
    error: err?.message || fallback,
    code: err?.code || undefined,
  });
}
