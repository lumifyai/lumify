import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { Lumify } from "../dist/lumify.js";
import { fakeFetch } from "./_helpers.js";

function client(responses) {
  const fetch = fakeFetch(responses);
  return { client: new Lumify({ apiKey: "lmfy-test", fetch }), fetch };
}

describe("resources — URL and query construction", () => {
  test("events.get sends includeOdds/includeIntelligence/bookmaker as query params", async () => {
    const { client: c, fetch } = client([{ status: 200, body: {} }]);
    await c.events.get(123, { includeOdds: true, includeIntelligence: true, bookmaker: "pinnacle" });
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.pathname, "/v1/events/123");
    assert.equal(url.searchParams.get("include_odds"), "true");
    assert.equal(url.searchParams.get("include_intelligence"), "true");
    assert.equal(url.searchParams.get("bookmaker"), "pinnacle");
  });

  test("events.batchGet posts event_ids and camelCase includes as snake_case body", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { events: [], not_found: [], total: 0 } }]);
    await c.events.batchGet([1, 2, 3], { includeOdds: true, bookmaker: "pinnacle" });
    const { url, init } = fetch.calls[0];
    assert.equal(init.method, "POST");
    assert.equal(new URL(url).pathname, "/v1/events/batch");
    assert.deepEqual(JSON.parse(init.body), {
      event_ids: [1, 2, 3],
      include_odds: true,
      bookmaker: "pinnacle",
    });
  });

  test("events.query posts the query text and optional limit as the body", async () => {
    const { client: c, fetch } = client([
      { status: 200, body: { query: "nhl games", interpreted: {}, unrecognized_terms: [], equivalent_request: "GET /v1/events", events: [], total: 0, next_after_id: null } },
    ]);
    await c.events.query("nhl games", { limit: 5 });
    const { url, init } = fetch.calls[0];
    assert.equal(init.method, "POST");
    assert.equal(new URL(url).pathname, "/v1/query");
    assert.deepEqual(JSON.parse(init.body), { query: "nhl games", limit: 5 });
  });

  test("events.query omits limit from the body when not provided", async () => {
    const { client: c, fetch } = client([{ status: 200, body: {} }]);
    await c.events.query("live nba games");
    const { init } = fetch.calls[0];
    assert.deepEqual(JSON.parse(init.body), { query: "live nba games" });
  });

  test("events.list maps camelCase filters to the API's snake_case params", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { events: [], total: 0 } }]);
    await c.events.list({
      sport: "nfl",
      seasonId: 7,
      teamId: 42,
      afterId: 100,
      limit: 10,
      includeScores: true,
    });
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.searchParams.get("sport"), "nfl");
    assert.equal(url.searchParams.get("season_id"), "7");
    assert.equal(url.searchParams.get("team_id"), "42");
    assert.equal(url.searchParams.get("after_id"), "100");
    assert.equal(url.searchParams.get("include_scores"), "true");
  });

  test("events.paginate drives after_id across pages until next_after_id is null", async () => {
    const { client: c, fetch } = client([
      { status: 200, body: { events: [{ id: 1 }], next_after_id: 1 } },
      { status: 200, body: { events: [{ id: 2 }], next_after_id: null } },
    ]);
    const seen = [];
    for await (const page of c.events.paginate({ sport: "nba" })) {
      seen.push(...(page.events ?? []));
    }
    assert.deepEqual(seen.map((e) => e.id), [1, 2]);
    assert.equal(fetch.calls.length, 2);
    const secondUrl = new URL(fetch.calls[1].url);
    assert.equal(secondUrl.searchParams.get("after_id"), "1");
  });

  test("events.iterate yields items from the events array (not data)", async () => {
    const { client: c } = client([
      { status: 200, body: { events: [{ id: 7 }, { id: 8 }], next_after_id: 8 } },
      { status: 200, body: { events: [{ id: 9 }], next_after_id: null } },
    ]);
    const ids = [];
    for await (const event of c.events.iterate({ sport: "mlb" })) ids.push(event.id);
    assert.deepEqual(ids, [7, 8, 9]);
  });

  test("teams.list / players.list build expected query strings", async () => {
    const { client: c, fetch } = client([{ status: 200, body: {} }, { status: 200, body: {} }]);
    await c.teams.list({ sport: "nfl", q: "eagles", active: true });
    await c.players.list({ sport: "tennis", ranked: true, limit: 5 });
    const t = new URL(fetch.calls[0].url);
    assert.equal(t.pathname, "/v1/teams");
    assert.equal(t.searchParams.get("q"), "eagles");
    const p = new URL(fetch.calls[1].url);
    assert.equal(p.pathname, "/v1/players");
    assert.equal(p.searchParams.get("ranked"), "true");
  });

  test("players.events hits the nested resource path", async () => {
    const { client: c, fetch } = client([{ status: 200, body: {} }]);
    await c.players.events(55, { status: "final", limit: 5 });
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.pathname, "/v1/players/55/events");
    assert.equal(url.searchParams.get("status"), "final");
  });

  test("webhooks.create posts camelCase params as the API's snake_case body", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { id: 1, signing_secret: "whsec_x" } }]);
    await c.webhooks.create({ url: "https://x.test/hook", eventTypes: ["score"], sport: "nfl" });
    const { init } = fetch.calls[0];
    assert.deepEqual(JSON.parse(init.body), { url: "https://x.test/hook", event_types: ["score"], sport: "nfl" });
  });

  test("webhooks.deliveries sends afterId/limit as after_id/limit query params", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { data: [], next_after_id: null } }]);
    await c.webhooks.deliveries(42, {
      afterId: 100,
      limit: 10,
      success: false,
      givenUp: true,
      eventType: "score",
    });
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.pathname, "/v1/webhooks/42/deliveries");
    assert.equal(url.searchParams.get("after_id"), "100");
    assert.equal(url.searchParams.get("limit"), "10");
    assert.equal(url.searchParams.get("success"), "false");
    assert.equal(url.searchParams.get("given_up"), "true");
    assert.equal(url.searchParams.get("event_type"), "score");
  });

  test("webhooks.deliveries omits after_id when not provided", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { data: [], next_after_id: null } }]);
    await c.webhooks.deliveries(42);
    const url = new URL(fetch.calls[0].url);
    assert.equal(url.searchParams.has("after_id"), false);
    assert.equal(url.searchParams.has("success"), false);
  });

  test("agent.keys.create posts scopes/expiresInDays as expires_in_days", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { id: 1, key: "lmfy-new" } }]);
    await c.agent.keys.create({ name: "bot", scopes: ["nfl"], expiresInDays: 30 });
    const { url, init } = fetch.calls[0];
    assert.equal(new URL(url).pathname, "/api/agent/keys");
    assert.deepEqual(JSON.parse(init.body), { name: "bot", scopes: ["nfl"], expires_in_days: 30 });
  });

  test("agent.credits.topup posts { pack_id }", async () => {
    const { client: c, fetch } = client([{ status: 200, body: { success: true } }]);
    await c.agent.credits.topup(3);
    assert.deepEqual(JSON.parse(fetch.calls[0].init.body), { pack_id: 3 });
  });

  test("sports.list / seasons.list build expected query strings", async () => {
    const { client: c, fetch } = client([{ status: 200, body: {} }, { status: 200, body: {} }]);
    await c.sports.list({ activeOnly: true });
    await c.seasons.list({ sport: "mlb", currentOnly: true });
    assert.equal(new URL(fetch.calls[0].url).searchParams.get("active_only"), "true");
    assert.equal(new URL(fetch.calls[1].url).searchParams.get("current_only"), "true");
  });
});
