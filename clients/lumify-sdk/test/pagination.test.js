import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { paginate, iterateItems } from "../dist/pagination.js";

function makePages(pages) {
  let calls = 0;
  const fetchPage = async (afterId, limit) => {
    calls++;
    const page = pages.find((p) => p.afterId === afterId);
    if (!page) throw new Error(`no page stubbed for afterId=${afterId}`);
    assert.equal(limit, page.expectedLimit ?? limit);
    return page.response;
  };
  return { fetchPage, callCount: () => calls };
}

describe("paginate()", () => {
  test("stops when next_after_id is null", async () => {
    const { fetchPage, callCount } = makePages([
      { afterId: undefined, response: { data: [1, 2], next_after_id: 2 } },
      { afterId: 2, response: { data: [3], next_after_id: null } },
    ]);
    const pages = [];
    for await (const page of paginate(fetchPage, { limit: 2 })) {
      pages.push(page);
    }
    assert.equal(pages.length, 2);
    assert.equal(callCount(), 2);
    assert.deepEqual(pages[1].data, [3]);
  });

  test("single page when next_after_id is absent", async () => {
    const { fetchPage } = makePages([{ afterId: undefined, response: { data: [1] } }]);
    const pages = [];
    for await (const page of paginate(fetchPage)) pages.push(page);
    assert.equal(pages.length, 1);
  });

  test("respects maxPages as a safety cap", async () => {
    let calls = 0;
    const fetchPage = async () => {
      calls++;
      return { data: [calls], next_after_id: calls }; // never terminates on its own
    };
    const pages = [];
    for await (const page of paginate(fetchPage, { maxPages: 3 })) pages.push(page);
    assert.equal(pages.length, 3);
    assert.equal(calls, 3);
  });
});

describe("iterateItems()", () => {
  test("flattens every page's data array into a single item stream (default itemsKey)", async () => {
    const { fetchPage } = makePages([
      { afterId: undefined, response: { data: [{ id: 1 }, { id: 2 }], next_after_id: 2 } },
      { afterId: 2, response: { data: [{ id: 3 }], next_after_id: null } },
    ]);
    const ids = [];
    for await (const item of iterateItems(fetchPage)) ids.push(item.id);
    assert.deepEqual(ids, [1, 2, 3]);
  });

  test("reads the events array when itemsKey is 'events' (EventListResponse shape)", async () => {
    const { fetchPage } = makePages([
      { afterId: undefined, response: { events: [{ id: 10 }, { id: 11 }], next_after_id: 11 } },
      { afterId: 11, response: { events: [{ id: 12 }], next_after_id: null } },
    ]);
    const ids = [];
    for await (const item of iterateItems(fetchPage, { itemsKey: "events" })) ids.push(item.id);
    assert.deepEqual(ids, [10, 11, 12]);
  });

  test("yields nothing when the configured itemsKey is missing (does not invent a data field)", async () => {
    const fetchPage = async () => ({ events: [{ id: 1 }], next_after_id: null });
    const items = [];
    // Default itemsKey is "data" — must not silently read "events".
    for await (const item of iterateItems(fetchPage)) items.push(item);
    assert.deepEqual(items, []);
  });

  test("handles a page with no item array gracefully", async () => {
    const fetchPage = async () => ({ next_after_id: null });
    const items = [];
    for await (const item of iterateItems(fetchPage)) items.push(item);
    assert.deepEqual(items, []);
  });
});
