import type { LumifyClient } from "../client.js";
import type { Team, TeamsListResponse } from "../generated/models.js";
import { paginate, iterateItems, type PaginateOptions } from "../pagination.js";

export interface ListTeamsParams {
  sport?: string;
  league?: string;
  conference?: string;
  division?: string;
  country?: string;
  /** Free-text search on team name/abbreviation. */
  q?: string;
  active?: boolean;
  afterId?: number;
  /** Max 100, default 25. */
  limit?: number;
}

function toQuery(p: ListTeamsParams) {
  return {
    sport: p.sport,
    league: p.league,
    conference: p.conference,
    division: p.division,
    country: p.country,
    q: p.q,
    active: p.active,
    after_id: p.afterId,
    limit: p.limit,
  };
}

export class TeamsResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /v1/teams — cursor-paginated. */
  list(params: ListTeamsParams = {}): Promise<TeamsListResponse> {
    return this.client.get<TeamsListResponse>("/v1/teams", { query: toQuery(params) });
  }

  /** Async-iterate every page of `list()` for the given filters. */
  paginate(params: Omit<ListTeamsParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return paginate(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }

  /** Async-iterate every team matching the filters, across all pages. */
  iterate(params: Omit<ListTeamsParams, "afterId"> = {}, options: PaginateOptions = {}) {
    return iterateItems(
      (afterId, limit) => this.list({ ...params, afterId, limit }),
      { limit: params.limit, ...options }
    );
  }

  /** GET /v1/teams/{id} */
  get(teamId: number): Promise<Team> {
    return this.client.get<Team>(`/v1/teams/${teamId}`);
  }
}
