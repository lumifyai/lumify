// Shared test doubles. Plain JS (not TS) so `node --test` runs it directly
// against the built `dist/` output with zero extra tooling.

/**
 * Build a fake `fetch` that records every call and answers with a queue of
 * canned responses (or a handler function for dynamic behavior).
 */
export function fakeFetch(responses) {
  const calls = [];
  let index = 0;
  const fn = async (url, init) => {
    calls.push({ url, init });
    const next = typeof responses === "function" ? responses(calls.length - 1, url, init) : responses[index++];
    if (!next) throw new Error(`fakeFetch: no response queued for call #${calls.length}`);
    if (next.throw) throw next.throw;
    const headers = new Headers(next.headers || {});
    const bodyText = next.body === undefined ? "" : JSON.stringify(next.body);
    return {
      ok: (next.status ?? 200) < 400,
      status: next.status ?? 200,
      headers,
      text: async () => (next.rawText !== undefined ? next.rawText : bodyText),
      json: async () => (next.rawText !== undefined ? JSON.parse(next.rawText) : next.body),
      body: next.stream,
    };
  };
  fn.calls = calls;
  return fn;
}

/** Build a ReadableStream<Uint8Array> from an array of string chunks. */
export function streamOf(chunks) {
  const encoder = new TextEncoder();
  let i = 0;
  return new ReadableStream({
    pull(controller) {
      if (i < chunks.length) {
        controller.enqueue(encoder.encode(chunks[i++]));
      } else {
        controller.close();
      }
    },
  });
}
