// Cursor pagination helper — every /v1 list endpoint takes `after_id` + `limit`
// (max 100, default 25) and returns `next_after_id` (null when exhausted). Some
// responses also carry `has_more`; others (events) omit it, so callers must
// derive "done" from `next_after_id == null` rather than relying on `has_more`.
//
// List envelopes are not uniform: teams/players use `data`, events uses
// `events`, sports/seasons are non-cursor (`sports`/`seasons`). Pass `itemsKey`
// to {@link iterateItems} when the array field is not `data`.

export interface CursorPage {
  next_after_id?: number | null;
  [key: string]: unknown;
}

export interface PaginateOptions {
  /** Page size per request (API max 100, default 25). */
  limit?: number;
  /** Safety cap on total pages fetched, to bound a runaway loop. Default 1000. */
  maxPages?: number;
}

export interface IterateOptions extends PaginateOptions {
  /**
   * Field on each page that holds the item array.
   * Default `"data"` (teams/players). Events use `"events"`.
   */
  itemsKey?: string;
}

/**
 * Async-generator over every page of a cursor-paginated list endpoint.
 *
 * @example
 * for await (const page of paginate((afterId, limit) => client.events.list({ ...filters, afterId, limit }))) {
 *   for (const event of page.events ?? []) { ... }
 * }
 */
export async function* paginate<TPage extends CursorPage>(
  fetchPage: (afterId: number | undefined, limit: number) => Promise<TPage>,
  options: PaginateOptions = {}
): AsyncGenerator<TPage, void, void> {
  const limit = options.limit ?? 25;
  const maxPages = options.maxPages ?? 1000;
  let afterId: number | undefined;

  for (let page = 0; page < maxPages; page++) {
    const result = await fetchPage(afterId, limit);
    yield result;
    if (result.next_after_id == null) return;
    afterId = result.next_after_id;
  }
}

/**
 * Flatten a paginated list endpoint into a single async iterator over its items.
 *
 * @example
 * // teams/players — default itemsKey "data"
 * for await (const team of iterateItems((afterId, limit) => client.teams.list({ afterId, limit }))) { ... }
 *
 * // events — items live under "events"
 * for await (const event of iterateItems(
 *   (afterId, limit) => client.events.list({ afterId, limit }),
 *   { itemsKey: "events" }
 * )) { ... }
 */
export async function* iterateItems<TItem, TPage extends CursorPage = CursorPage>(
  fetchPage: (afterId: number | undefined, limit: number) => Promise<TPage>,
  options: IterateOptions = {}
): AsyncGenerator<TItem, void, void> {
  const itemsKey = options.itemsKey ?? "data";
  for await (const page of paginate(fetchPage, options)) {
    const items = (page as Record<string, unknown>)[itemsKey];
    if (!Array.isArray(items)) continue;
    for (const item of items as TItem[]) {
      yield item;
    }
  }
}
