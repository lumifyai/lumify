import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { parseSSEStream, streamScores } from "../dist/sse.js";
import { LumifyError } from "../dist/errors.js";
import { LumifyClient } from "../dist/client.js";
import { fakeFetch, streamOf } from "./_helpers.js";

describe("parseSSEStream()", () => {
  test("parses named events with JSON data", async () => {
    const stream = streamOf(['event: score\ndata: {"status":"inprogress"}\n\n']);
    const frames = [];
    for await (const f of parseSSEStream(stream)) frames.push(f);
    assert.equal(frames.length, 1);
    assert.equal(frames[0].event, "score");
    assert.deepEqual(JSON.parse(frames[0].data), { status: "inprogress" });
  });

  test("accepts CRLF-delimited frames (\\r\\n\\r\\n)", async () => {
    const stream = streamOf(['event: score\r\ndata: {"status":"final"}\r\n\r\n']);
    const frames = [];
    for await (const f of parseSSEStream(stream)) frames.push(f);
    assert.equal(frames.length, 1);
    assert.equal(frames[0].event, "score");
    assert.deepEqual(JSON.parse(frames[0].data), { status: "final" });
  });

  test("skips pure keep-alive comment frames", async () => {
    const stream = streamOf([": keep-alive\n\n", 'event: done\ndata: {"event_id":1}\n\n']);
    const frames = [];
    for await (const f of parseSSEStream(stream)) frames.push(f);
    assert.equal(frames.length, 1);
    assert.equal(frames[0].event, "done");
  });

  test("handles a frame split across multiple stream chunks", async () => {
    const stream = streamOf(['event: sc', 'ore\ndata: {"a":1}', "\n\n"]);
    const frames = [];
    for await (const f of parseSSEStream(stream)) frames.push(f);
    assert.equal(frames.length, 1);
    assert.equal(frames[0].event, "score");
  });

  test("joins multiline data fields with newlines", async () => {
    const stream = streamOf(["data: line1\ndata: line2\n\n"]);
    const frames = [];
    for await (const f of parseSSEStream(stream)) frames.push(f);
    assert.equal(frames[0].data, "line1\nline2");
  });
});

describe("streamScores()", () => {
  test("yields typed score/done events from the live endpoint", async () => {
    const fetch = fakeFetch([
      {
        status: 200,
        stream: streamOf([
          'event: score\ndata: {"event_id":1,"status":"inprogress"}\n\n',
          ': keep-alive\n\n',
          'event: done\ndata: {"event_id":1}\n\n',
        ]),
      },
    ]);
    const client = new LumifyClient({ apiKey: "lmfy-x", fetch });
    const events = [];
    for await (const evt of streamScores(client, 1)) events.push(evt);
    assert.equal(events.length, 2);
    assert.equal(events[0].event, "score");
    assert.equal(events[0].data.status, "inprogress");
    assert.equal(events[1].event, "done");
  });

  test("throws a LumifyError if the endpoint rejects before streaming", async () => {
    const fetch = fakeFetch([{ status: 404, body: { error: { code: "not_found", message: "no such event", status: 404 } } }]);
    const client = new LumifyClient({ apiKey: "lmfy-x", fetch });
    await assert.rejects(
      (async () => {
        for await (const _ of streamScores(client, 999)) {
          // never reached
        }
      })(),
      LumifyError
    );
  });

  test("skips a malformed data frame instead of throwing mid-stream", async () => {
    const fetch = fakeFetch([
      {
        status: 200,
        stream: streamOf(["event: score\ndata: {not json\n\n", 'event: done\ndata: {"event_id":1}\n\n']),
      },
    ]);
    const client = new LumifyClient({ apiKey: "lmfy-x", fetch });
    const events = [];
    for await (const evt of streamScores(client, 1)) events.push(evt);
    assert.equal(events.length, 1);
    assert.equal(events[0].event, "done");
  });

  test("transparently reconnects on `event: reconnect` and keeps yielding", async () => {
    const fetch = fakeFetch([
      {
        status: 200,
        stream: streamOf([
          'event: score\ndata: {"event_id":1,"status":"inprogress"}\n\n',
          'event: reconnect\ndata: {"event_id":1,"reason":"max_stream_duration","max_seconds":300}\n\n',
        ]),
      },
      {
        status: 200,
        stream: streamOf([
          'event: score\ndata: {"event_id":1,"status":"inprogress","clock":"9:00"}\n\n',
          'event: done\ndata: {"event_id":1}\n\n',
        ]),
      },
    ]);
    const client = new LumifyClient({ apiKey: "lmfy-x", fetch });
    const events = [];
    for await (const evt of streamScores(client, 1)) events.push(evt);

    assert.equal(fetch.calls.length, 2, "expected a second connection after the reconnect signal");
    assert.equal(events.length, 4);
    assert.deepEqual(
      events.map((e) => e.event),
      ["score", "reconnect", "score", "done"]
    );
    // The caller sees a single continuous stream of domain events across the
    // reconnect boundary — the second connection's score update is present.
    assert.equal(events[2].data.clock, "9:00");
  });

  test("stops without looping forever if the connection just drops (no reconnect signal)", async () => {
    const fetch = fakeFetch([
      { status: 200, stream: streamOf(['event: score\ndata: {"event_id":1,"status":"inprogress"}\n\n']) },
    ]);
    const client = new LumifyClient({ apiKey: "lmfy-x", fetch });
    const events = [];
    for await (const evt of streamScores(client, 1)) events.push(evt);
    assert.equal(fetch.calls.length, 1, "must not attempt a reconnect on a plain stream end");
    assert.equal(events.length, 1);
  });
});
