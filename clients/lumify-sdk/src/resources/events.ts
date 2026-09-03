import type { LumifyClient } from "../client.js";
import type {
  BatchEventsResponse,
  EventDetail,
  EventListResponse,
  EventSummary,
  ForecastsResponse,
  IntelligenceEvResponse,
  IntelligenceResponse,
  NLQueryResponse,
  OddsHistoryResponse,
  MlbStatsResponse,
  NflStatsResponse,
  OddsResponse,
  PeriodOddsResponse,
  PlayerPropsResponse,
  PredictionMarketsResponse,
  ScoreResponse,
  SplitsResponse,
  TeamPropsResponse,
  StatsResponse,
  TennisStatsResponse,
} from "../generated/models.js";

/** Sport-specific /stats payloads — branch on sport, never shared field names. */
export type EventStatsResponse = StatsResponse | MlbStatsResponse | TennisStatsResponse | NflStatsResponse;
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
  /** League slug: nfl, nba, atp, mls… */
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
  /**
   * Inline current odds under `odds`, scoped by `bookmaker` (default: pinnacle).
   * Does not add credits — the event call stays 1 credit.
   */
  includeOdds?: boolean;
  /** Inline bet intelligence under `intelligence`. Does not add credits. */
  includeIntelligence?: boolean;
  /** Bookmaker for inlined odds / intelligence market prices: pinnacle | fanduel | draftkings | betmgm | caesars | bet365 | circa | hardrock | betonline | all. */
  bookmaker?: string;
  /** When includeOdds is true, include alternate spread/total rungs. Default is mains only. */
  includeAlts?: boolean;
}

export interface BookmakerParams {
  bookmaker?: string;
}

export interface ListForecastsParams {
  /** Sport slug: mlb, ncaaf, nfl, nba, ncaab, or nhl. */
  sport: string;
  /** UTC slate date YYYY-MM-DD. Defaults to today UTC. */
  date?: string;
  /** Main-line family filter (h2h, spreads, or totals) for a sport's main-line forecast rows, once one exists. Inert today — no sport publishes one yet. */
  market?: string;
  /** Max wagers (1–100). Default 25. */
  limit?: number;
}

export interface ListEvParams {
  /** Sport slug: soccer, mlb, tennis, nfl, or ncaaf. */
  sport: string;
  /** Optional league slug. Soccer without a league scans every migrated league. */
  league?: string;
  /** Main-line family: h2h (default, moneyline), spreads, or totals. Tennis totals return 400. */
  market?: string;
  /** Minimum EV%. Default 0. Clamped to 0–25. */
  minEv?: number;
  /** Restrict to one sportsbook slug. */
  book?: string;
  /** Max rows (1–200). Default 50. */
  limit?: number;
}

export interface OddsParams extends BookmakerParams {
  /** Include alternate spread/total rungs. Default is mains only. */
  includeAlts?: boolean;
}

export interface BatchGetEventsParams {
  /**
   * Inline current odds on each event, scoped by `bookmaker` (default: pinnacle).
   * Does not add credits — each found event stays 1 credit.
   */
  includeOdds?: boolean;
  /** Inline bet intelligence on each event. Does not add credits. */
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
        include_alts: params.includeAlts,
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
  odds(eventId: number, params: OddsParams = {}): Promise<OddsResponse> {
    return this.client.get<OddsResponse>(`/v1/events/${eventId}/odds`, {
      query: { bookmaker: params.bookmaker, include_alts: params.includeAlts },
    });
  }

  /** GET /v1/events/{id}/odds/history — line-movement history. */
  oddsHistory(eventId: number, params: OddsHistoryParams = {}): Promise<OddsHistoryResponse> {
    return this.client.get<OddsHistoryResponse>(`/v1/events/${eventId}/odds/history`, {
      query: { bookmaker: params.bookmaker, limit: params.limit },
    });
  }

  /**
   * GET /v1/events/{id}/stats — raw, deterministic team/match statistics
   * (the "Data" layer). No market/odds data — use `odds()` for that. Soccer,
   * MLB, tennis (singles), and NFL Stage-1 today. `available: false` (teams
   * not yet resolved) is not charged — `X-Credits-Used: 0` on the response.
   */
  stats(eventId: number): Promise<EventStatsResponse> {
    return this.client.get<EventStatsResponse>(`/v1/events/${eventId}/stats`);
  }

  /**
   * GET /v1/events/{id}/player-props — NFL/NCAAF/NBA/NCAAB player-prop mains +
   * live box progress. `available: false` is not charged.
   */
  playerProps(eventId: number): Promise<PlayerPropsResponse> {
    return this.client.get<PlayerPropsResponse>(`/v1/events/${eventId}/player-props`);
  }

  /**
   * GET /v1/events/{id}/team-props — NFL/NCAAF/MLB/soccer team-total mains +
   * this-event team score. `available: false` is not charged.
   */
  teamProps(eventId: number): Promise<TeamPropsResponse> {
    return this.client.get<TeamPropsResponse>(`/v1/events/${eventId}/team-props`);
  }

  /**
   * GET /v1/events/{id}/prediction-markets — Fanatics Markets / Kalshi /
   * Polymarket 0–1 game-line probabilities. Not sportsbook odds.
   * `available: false` is not charged.
   */
  predictionMarkets(eventId: number): Promise<PredictionMarketsResponse> {
    return this.client.get<PredictionMarketsResponse>(
      `/v1/events/${eventId}/prediction-markets`,
    );
  }

  /**
   * GET /v1/events/{id}/period-odds — first-half / first-five / first-set mains
   * + period scores. `available: false` is not charged.
   */
  periodOdds(eventId: number): Promise<PeriodOddsResponse> {
    return this.client.get<PeriodOddsResponse>(`/v1/events/${eventId}/period-odds`);
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

  /** GET /v1/intelligence/ev — Beta main-line EV scan (h2h / spreads / totals). */
  listEv(params: ListEvParams): Promise<IntelligenceEvResponse> {
    return this.client.get<IntelligenceEvResponse>("/v1/intelligence/ev", {
      query: {
        sport: params.sport,
        league: params.league,
        market: params.market,
        min_ev: params.minEv,
        book: params.book,
        limit: params.limit,
      },
    });
  }

  /** GET /v1/intelligence/forecasts — daily board of forecasted wagers: a model prediction, not a beat-the-market claim. Player-prop wagers today; schema also carries main-line rows once a sport ships one. */
  listForecasts(params: ListForecastsParams): Promise<ForecastsResponse> {
    return this.client.get<ForecastsResponse>("/v1/intelligence/forecasts", {
      query: {
        sport: params.sport,
        date: params.date,
        market: params.market,
        limit: params.limit,
      },
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
