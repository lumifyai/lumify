import type { LumifyClient } from "../client.js";
import type { SeasonsListResponse, SportsListResponse } from "../generated/models.js";

export interface ListSportsParams {
  /** Only return currently-active sports. */
  activeOnly?: boolean;
}

export class SportsResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /v1/sports — every sport Lumify covers (mlb, nfl, nba, nhl, tennis, soccer, ncaaf, ncaab, ...). */
  list(params: ListSportsParams = {}): Promise<SportsListResponse> {
    return this.client.get<SportsListResponse>("/v1/sports", {
      query: { active_only: params.activeOnly },
    });
  }
}

export interface ListSeasonsParams {
  /** Sport slug filter (e.g. "nfl"). */
  sport?: string;
  /** Only return each sport/league's current season. */
  currentOnly?: boolean;
}

export class SeasonsResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /v1/seasons */
  list(params: ListSeasonsParams = {}): Promise<SeasonsListResponse> {
    return this.client.get<SeasonsListResponse>("/v1/seasons", {
      query: { sport: params.sport, current_only: params.currentOnly },
    });
  }
}
