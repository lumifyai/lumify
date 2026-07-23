import type { LumifyClient } from "../client.js";
import type {
  AgentApiKey,
  AgentApiKeyListResponse,
  AgentApiKeyRevokeResponse,
  AgentCreditsResponse,
  CreditPackListResponse,
  CreditTopupResponse,
} from "../generated/models.js";

export interface CreateApiKeyParams {
  /** Defaults to "Agent key" server-side if omitted. */
  name?: string;
  /** Sport slugs the key is scoped to, or `["all"]`. Defaults to the account's full access. */
  scopes?: string[];
  /** Key auto-expires after this many days if set. */
  expiresInDays?: number;
}

/** Programmatic API-key lifecycle — mint/list/revoke keys without the dashboard. */
export class AgentKeysResource {
  constructor(private readonly client: LumifyClient) {}

  /** POST /api/agent/keys — the full key is only returned once, on creation. */
  create(params: CreateApiKeyParams = {}): Promise<AgentApiKey> {
    return this.client.post<AgentApiKey>("/api/agent/keys", {
      body: { name: params.name, scopes: params.scopes, expires_in_days: params.expiresInDays },
    });
  }

  /** GET /api/agent/keys */
  list(): Promise<AgentApiKeyListResponse> {
    return this.client.get<AgentApiKeyListResponse>("/api/agent/keys");
  }

  /** DELETE /api/agent/keys/{id} */
  revoke(keyId: number): Promise<AgentApiKeyRevokeResponse> {
    return this.client.delete<AgentApiKeyRevokeResponse>(`/api/agent/keys/${keyId}`);
  }
}

/** Credit balance, usage, and top-ups — for agents managing their own spend. */
export class AgentCreditsResource {
  constructor(private readonly client: LumifyClient) {}

  /** GET /api/agent/credits — current balance, usage, and billing period. */
  get(): Promise<AgentCreditsResponse> {
    return this.client.get<AgentCreditsResponse>("/api/agent/credits");
  }

  /** GET /api/agent/credit-packs — purchasable one-off credit packs. */
  listPacks(): Promise<CreditPackListResponse> {
    return this.client.get<CreditPackListResponse>("/api/agent/credit-packs");
  }

  /** POST /api/agent/credits/topup — charges the account's saved payment method for `packId` (see `listPacks()`). */
  topup(packId: number): Promise<CreditTopupResponse> {
    return this.client.post<CreditTopupResponse>("/api/agent/credits/topup", {
      body: { pack_id: packId },
    });
  }
}

/** Agent onboarding surface: `client.agent.keys.*` and `client.agent.credits.*`. */
export class AgentResource {
  readonly keys: AgentKeysResource;
  readonly credits: AgentCreditsResource;

  constructor(client: LumifyClient) {
    this.keys = new AgentKeysResource(client);
    this.credits = new AgentCreditsResource(client);
  }
}
