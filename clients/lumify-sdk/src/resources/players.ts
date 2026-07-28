import type { LumifyClient } from "../client.js";
import type { Player, PlayerEventsResponse, PlayersListResponse } from "../generated/models.js";
import { paginate, iterateItems, type PaginateOptions } from "../pagination.js";

export interface ListPlayersParams {
  sport?: string;
  /** Free-text search on player name. */
  q?: string;
  country?: string;
  active?: boolean;
  /** Only players with a ranking (e.g. tennis ATP/WTA). */
  ranked?: boolean;
  afterId?: number;
  /** Max 100, default 25. */
  limit?: number;
}

export interface PlayerEventsParams {
  status?: string;
  from?: string;
  to?: string;
  afterId?: number;
  limit?: number;
}

function toQuery(p: ListPlayersParams) {
  return {
    sport: p.sport,
    q: p.q,
    country: p.country,
    active: p.active,
    ranked: p.ranked,
    after_id: p.afterId,
    limit: p.limit,
  };
}

export class PlayersResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /v1/players — cursor-paginated. */
  list(params: ListPlayersParams = {}): Promise<PlayersListResponse> {
    return this.client.get<PlayersListResponse>("/v1/players", { query: toQuery(params) });
  }

  /** Async-iterate every page of `list()` for the given filters. */
  paginate(params: Omit<ListPlayersParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return paginate(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }

  /** Async-iterate every player matching the filters, across all pages. */
  iterate(params: Omit<ListPlayersParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return iterateItems(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }

  /** GET /v1/players/{id} */
  get(playerId: number): Promise<Player> {
    return this.client.get<Player>(`/v1/players/${playerId}`);
  }

  /** GET /v1/players/{id}/events — cursor-paginated schedule/results for a player. */
  events(playerId: number, params: PlayerEventsParams = {}): Promise<PlayerEventsResponse> {
    return this.client.get<PlayerEventsResponse>(`/v1/players/${playerId}/events`, {
      query: {
        status: params.status,
        from: params.from,
        to: params.to,
        after_id: params.afterId,
        limit: params.limit,
      },
    });
  }

  /** Async-iterate every page of `events()` for the given player/filters. */
  paginateEvents(playerId: number, params: Omit<PlayerEventsParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return paginate(
      (afterId, limit) => this.events(playerId, { ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }
}
