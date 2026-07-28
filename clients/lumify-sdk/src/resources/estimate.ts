import type { LumifyClient } from "../client.js";
import type { EstimateCall, EstimateResponse } from "../generated/models.js";

export interface EstimateToolsResponse {
  [key: string]: unknown;
}

/** Pre-call credit-cost estimates — plan spend without spending. */
export class EstimateResource {
  constructor(private readonly client: LumifyClient) {}

  /**
   * POST /v1/estimate — pre-call credit-cost estimate for one or more planned
   * tool calls, without making them or spending credits. Costs are
   * data-dependent (e.g. odds/intelligence not yet ingested are free), so
   * each result is a `[min_credits, max_credits]` range, not a single number.
   * Always free (0 credits) to call.
   *
   * Each entry in `calls` is `{ tool: "get_event", arguments: {...} }` — the
   * same tool name and arguments you'd pass to the matching MCP tool or SDK
   * method. See `listTools()` for the supported tool names.
   */
  cost(calls: EstimateCall[]): Promise<EstimateResponse> {
    return this.client.post<EstimateResponse>("/v1/estimate", { body: { calls } });
  }

  /** GET /v1/estimate/tools — the tool names `cost()` understands, grouped by how their cost varies. */
  listTools(): Promise<EstimateToolsResponse> {
    return this.client.get<EstimateToolsResponse>("/v1/estimate/tools");
  }
}
