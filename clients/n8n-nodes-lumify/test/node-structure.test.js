const test = require("node:test");
const assert = require("node:assert/strict");

const { Lumify } = require("../dist/nodes/Lumify/Lumify.node.js");
const { LumifyApi } = require("../dist/credentials/LumifyApi.credentials.js");

test("Lumify node declares all expected resources in alphabetical display order", () => {
  const node = new Lumify();
  const resourceProp = node.description.properties.find(
    (p) => p.name === "resource",
  );
  assert.deepEqual(
    resourceProp.options.map((o) => o.name),
    [
      "Bet Intelligence",
      "Event",
      "Live Score",
      "Odd",
      "Player",
      "Sport",
      "Team",
    ],
  );
  assert.deepEqual(
    resourceProp.options.map((o) => o.value).sort(),
    ["event", "intelligence", "odds", "player", "score", "sport", "team"],
  );
});

test("list filter collections are alphabetized by displayName", () => {
  const node = new Lumify();
  const expected = {
    eventListFilters: [
      "After ID",
      "Date",
      "From Date",
      "Include Scores",
      "League",
      "Limit",
      "Only Events With Recommended Bets",
      "Season ID",
      "Sort",
      "Sport",
      "Status",
      "Team ID",
      "To Date",
    ],
    teamListFilters: [
      "Active Only",
      "After ID",
      "Conference",
      "Country",
      "Division",
      "League",
      "Limit",
      "Name Search",
      "Sport",
    ],
    playerListFilters: [
      "Active Only",
      "After ID",
      "Country",
      "Limit",
      "Name Search",
      "Ranked Only",
      "Sport",
    ],
    playerEventsFilters: [
      "After ID",
      "From Date",
      "Limit",
      "Status",
      "To Date",
    ],
  };
  for (const [name, displayNames] of Object.entries(expected)) {
    const prop = node.description.properties.find((p) => p.name === name);
    assert.ok(prop, `missing ${name}`);
    assert.deepEqual(
      prop.options.map((o) => o.displayName),
      displayNames,
      `${name} displayName order`,
    );
    const limit = prop.options.find((o) => o.name === "limit");
    assert.equal(limit.default, 50, `${name} limit default`);
    assert.ok(limit.description, `${name} limit description`);
  }
});

test("Lumify node requires the lumifyApi credential", () => {
  const node = new Lumify();
  assert.equal(node.description.credentials.length, 1);
  assert.equal(node.description.credentials[0].name, "lumifyApi");
  assert.equal(node.description.credentials[0].required, true);
});

test("Lumify node is usable as an AI Agent tool", () => {
  const node = new Lumify();
  assert.equal(node.description.usableAsTool, true);
});

test("Lumify node has no declarative requestDefaults (uses execute())", () => {
  const node = new Lumify();
  // Programmatic execute() nodes must not declare requestDefaults — n8n
  // never applies them. Base URL comes from credentials + helpers.ts.
  assert.equal(node.description.requestDefaults, undefined);
});

test("list filters expose after_id for cursor pagination", () => {
  const node = new Lumify();
  for (const name of [
    "eventListFilters",
    "teamListFilters",
    "playerListFilters",
    "playerEventsFilters",
  ]) {
    const prop = node.description.properties.find((p) => p.name === name);
    assert.ok(prop, `missing ${name}`);
    const after = prop.options.find((o) => o.name === "after_id");
    assert.ok(after, `${name} missing after_id`);
  }
});

test("batch options expose include_odds / include_intelligence", () => {
  const node = new Lumify();
  const prop = node.description.properties.find(
    (p) => p.name === "eventBatchOptions",
  );
  const names = prop.options.map((o) => o.name);
  assert.ok(names.includes("include_odds"));
  assert.ok(names.includes("include_intelligence"));
  assert.ok(names.includes("bookmaker"));
});

test("odds history exposes bookmaker and limit", () => {
  const node = new Lumify();
  const bookmaker = node.description.properties.find(
    (p) => p.name === "oddsBookmaker",
  );
  assert.deepEqual(bookmaker.displayOptions.show.operation, ["get", "history"]);
  const limit = node.description.properties.find(
    (p) => p.name === "oddsHistoryLimit",
  );
  assert.ok(limit);
});

test("splitIntoItems is offered on list-like operations", () => {
  const node = new Lumify();
  const prop = node.description.properties.find(
    (p) => p.name === "splitIntoItems",
  );
  assert.ok(prop);
  assert.deepEqual(prop.displayOptions.show.operation.sort(), [
    "batch",
    "events",
    "list",
    "listSeasons",
    "listSports",
    "query",
  ]);
});

test("LumifyApi credential authenticates via function (normalizes Bearer)", async () => {
  const creds = new LumifyApi();
  assert.equal(creds.name, "lumifyApi");
  assert.equal(typeof creds.authenticate, "function");

  const result = await creds.authenticate(
    { apiKey: "Bearer lmfy-test-key" },
    { headers: {} },
  );
  assert.equal(result.headers.Authorization, "Bearer lmfy-test-key");
  assert.match(result.headers["User-Agent"], /^n8n-nodes-lumify\//);
  assert.equal(
    result.headers["X-Lumify-Client"],
    result.headers["User-Agent"],
  );
});

test("LumifyApi credential rejects empty / bare Bearer keys", async () => {
  const creds = new LumifyApi();
  await assert.rejects(
    () => creds.authenticate({ apiKey: "Bearer" }, { headers: {} }),
    /API key is required/,
  );
});

test("LumifyApi credential test request hits a real sports endpoint", () => {
  const creds = new LumifyApi();
  assert.equal(creds.test.request.url, "/v1/sports");
});

test("every operation option exposes an action label (n8n AI-tool requirement)", () => {
  const node = new Lumify();
  const operationProps = node.description.properties.filter(
    (p) => p.name === "operation",
  );
  assert.ok(operationProps.length >= 7, "expected an operation list per resource");
  for (const prop of operationProps) {
    for (const option of prop.options) {
      assert.ok(
        option.action,
        `operation "${option.value}" is missing an action label`,
      );
    }
  }
});
