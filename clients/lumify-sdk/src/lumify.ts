import { LumifyClient, type LumifyClientOptions } from "./client.js";
import { AgentResource } from "./resources/agent.js";
import { EstimateResource } from "./resources/estimate.js";
import { EventsResource } from "./resources/events.js";
import { PlayersResource } from "./resources/players.js";
import { SeasonsResource, SportsResource } from "./resources/sports.js";
import { TeamsResource } from "./resources/teams.js";
import { WebhooksResource } from "./resources/webhooks.js";

export type { LumifyClientOptions } from "./client.js";

/**
 * The Lumify SDK entry point.
 *
 * @example
 * import { Lumify } from "@lumifyai/sdk";
 *
 * const client = new Lumify({ apiKey: process.env.LUMIFY_API_KEY! });
 * const { data: sports } = await client.sports.list();
 * const event = await client.events.get(12345, { includeOdds: true });
 */
export class Lumify {
  private readonly client: LumifyClient;

  readonly sports: SportsResource;
  readonly seasons: SeasonsResource;
  readonly events: EventsResource;
  readonly teams: TeamsResource;
  readonly players: PlayersResource;
  readonly webhooks: WebhooksResource;
  readonly agent: AgentResource;
  readonly estimate: EstimateResource;

  constructor(options: LumifyClientOptions) {
    this.client = new LumifyClient(options);
    this.sports = new SportsResource(this.client);
    this.seasons = new SeasonsResource(this.client);
    this.events = new EventsResource(this.client);
    this.teams = new TeamsResource(this.client);
    this.players = new PlayersResource(this.client);
    this.webhooks = new WebhooksResource(this.client);
    this.agent = new AgentResource(this.client);
    this.estimate = new EstimateResource(this.client);
  }

  /** The configured API origin (default `https://lumify.ai`). */
  get baseUrl(): string {
    return this.client.baseUrl;
  }
}
