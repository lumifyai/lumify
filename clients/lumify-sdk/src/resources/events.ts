import type { LumifyClient } from "../client.js";
import type {
  BatchEventsResponse,
  EventDetail,
  EventListResponse,
  EventSummary,
  IntelligenceResponse,
  NLQueryResponse,
  OddsHistoryResponse,
  OddsResponse,
  ScoreResponse,
  SplitsResponse,
} from "../generated/models.js";
import { paginate, iterateItems, type PaginateOptions } from "../pagination.js";
import { streamScores, type ScoreStreamEvent, type StreamScoresOptions } from "../sse.js";

/**
 * `EventDetail` plus the optional compound-include payloads that the OpenAPI
 * schema doesn't declare (they're attached dynamically when
 * `include_odds` / `include_intelligence` are set).
 */
export type EventDetailWithIncludes = EventDetail & {
  odds?: OddsResponse;
  intelligence?: IntelligenceResponse;
};

export interface ListEventsParams {
  /** Sport slug: nfl, nba, mlb, nhl, tennis, soccer… */
  sport?: string;
  /** League slug: nfl, nba, atp, fifa_world_cup… */
  league?: string;
  /** Event status: scheduled | inprogress | final | … */
  status?: string;
  /** UTC date YYYY-MM-DD (single day). */
  date?: string;
  /** UTC start date YYYY-MM-DD (range start). */
  from?: string;
  /** UTC end date YYYY-MM-DD, inclusive (range end). */
  to?: string;
  seasonId?: number;
  /** Filter to events where this team participates. Resolve via `client.teams.list({ q })`. */
  teamId?: number;
  afterId?: number;
  /** Max 100, default 25. */
  limit?: number;
  /** Inline each event's current score. */
  includeScores?: boolean;
  hasRecommend?: boolean;
  sort?: string;
}

export interface GetEventParams {
  /** Inline current odds (all bookmakers) under `odds`. Costs +1 credit. */
  includeOdds?: boolean;
  /** Inline bet intelligence under `intelligence`. Costs +1 credit. */
  includeIntelligence?: boolean;
  /** Bookmaker for market prices in `intelligence.bets[].market`: pinnacle | fanduel | draftkings. */
  bookmaker?: string;
}

export interface BookmakerParams {
  bookmaker?: string;
}

export interface BatchGetEventsParams {
  /** Inline current odds (all bookmakers) on each event. Costs +1 credit per event where odds are available. */
  includeOdds?: boolean;
  /** Inline bet intelligence on each event. Costs +1 credit per event where available. */
  includeIntelligence?: boolean;
  bookmaker?: string;
}

export interface OddsHistoryParams extends BookmakerParams {
  limit?: number;
}

function toQuery(p: ListEventsParams) {
  return {
    sport: p.sport,
    league: p.league,
    status: p.status,
    date: p.date,
    from: p.from,
    to: p.to,
    season_id: p.seasonId,
    team_id: p.teamId,
    after_id: p.afterId,
    limit: p.limit,
    include_scores: p.includeScores,
    has_recommend: p.hasRecommend,
    sort: p.sort,
  };
}

export class EventsResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /v1/events — cursor-paginated (`after_id`/`limit`; `next_after_id` when more remain). */
  list(params: ListEventsParams = {}): Promise<EventListResponse> {
    return this.client.get<EventListResponse>("/v1/events", { query: toQuery(params) });
  }

  /**
   * Async-iterate every page of `list()` for the given filters, stopping when
   * `next_after_id` is null. Use {@link EventsResource.iterate} to flatten to items.
   */
  paginate(params: Omit<ListEventsParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return paginate(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }

  /** Async-iterate every event matching the filters, across all pages. */
  iterate(params: Omit<ListEventsParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return iterateItems<EventSummary, EventListResponse>(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options, itemsKey: "events" }
    );
  }

  /** GET /v1/events/{id} — full event with participants, venue, and schedule metadata. */
  get(eventId: number, params: GetEventParams = {}): Promise<EventDetailWithIncludes> {
    return this.client.get<EventDetailWithIncludes>(`/v1/events/${eventId}`, {
      query: {
        include_odds: params.includeOdds,
        include_intelligence: params.includeIntelligence,
        bookmaker: params.bookmaker,
      },
    });
  }

  /**
   * POST /v1/events/batch — fetch multiple events by id in one round-trip.
   * Max 25 ids per call; duplicates are billed once. Ids that don't exist are
   * returned under `not_found` rather than failing the call, and cost nothing.
   */
  batchGet(eventIds: number[], params: BatchGetEventsParams = {}): Promise<BatchEventsResponse> {
    return this.client.post<BatchEventsResponse>("/v1/events/batch", {
      body: {
        event_ids: eventIds,
        include_odds: params.includeOdds,
        include_intelligence: params.includeIntelligence,
        bookmaker: params.bookmaker,
      },
    });
  }

  /**
   * POST /v1/query — search events with a natural-language query instead of
   * structured filters, e.g. `"live nfl games today"`. A small rule-based
   * mapper (not an LLM call); the response includes the parsed filters
   * (`interpreted`), the equivalent `GET /v1/events` call, and any words that
   * didn't map to a filter (`unrecognized_terms`). Costs 1 credit, same as
   * `list()` — interpreting the query text is free.
   */
  query(text: string, params: { limit?: number } = {}): Promise<NLQueryResponse> {
    return this.client.post<NLQueryResponse>("/v1/query", {
      body: { query: text, limit: params.limit },
    });
  }

  /** GET /v1/events/{id}/score — live score snapshot. */
  score(eventId: number): Promise<ScoreResponse> {
    return this.client.get<ScoreResponse>(`/v1/events/${eventId}/score`);
  }

  /**
   * GET /v1/events/{id}/odds. `available: false` (not-yet-posted odds) is not
   * charged — `X-Credits-Used: 0` on the response (read via `getMeta()`).
   */
  odds(eventId: number, params: BookmakerParams = {}): Promise<OddsResponse> {
    return this.client.get<OddsResponse>(`/v1/events/${eventId}/odds`, {
      query: { bookmaker: params.bookmaker },
    });
  }

  /** GET /v1/events/{id}/odds/history — line-movement history. */
  oddsHistory(eventId: number, params: OddsHistoryParams = {}): Promise<OddsHistoryResponse> {
    return this.client.get<OddsHistoryResponse>(`/v1/events/${eventId}/odds/history`, {
      query: { bookmaker: params.bookmaker, limit: params.limit },
    });
  }

  /** GET /v1/events/{id}/splits — public betting splits (tickets % vs. money %). */
  splits(eventId: number): Promise<SplitsResponse> {
    return this.client.get<SplitsResponse>(`/v1/events/${eventId}/splits`);
  }

  /** GET /v1/events/{id}/intelligence — AI bet intelligence (confidence, signals, narratives). */
  intelligence(eventId: number, params: BookmakerParams = {}): Promise<IntelligenceResponse> {
    return this.client.get<IntelligenceResponse>(`/v1/events/${eventId}/intelligence`, {
      query: { bookmaker: params.bookmaker },
    });
  }

  /**
   * GET /v1/events/{id}/stream (SSE) — async-iterate live score updates,
   * emitted only on change, until the event finishes.
   *
   * @example
   * for await (const evt of client.events.stream(eventId)) {
   *   if (evt.event === "score") console.log(evt.data.status);
   *   if (evt.event === "done") break;
   * }
   */
  stream(eventId: number, options: StreamScoresOptions = {}): AsyncGenerator<ScoreStreamEvent, void, void> {
    return streamScores(this.client, eventId, options);
  }
}
