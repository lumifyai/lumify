import {
  NodeApiError,
  NodeConnectionTypes,
  NodeOperationError,
  type IDataObject,
  type IExecuteFunctions,
  type IHttpRequestMethods,
  type INodeExecutionData,
  type INodeType,
  type INodeTypeDescription,
  type JsonObject,
} from "n8n-workflow";

import {
  BASE_URL_DEFAULT,
  BATCH_MAX_IDS,
  extractApiMessage,
  extractHttpStatus,
  friendlyAuthError,
  parseIdList,
  splitEnvelope,
  validateBatchIds,
  validatePositiveId,
  withDefinedValues,
} from "./helpers";

async function apiRequest(
  ctx: IExecuteFunctions,
  method: IHttpRequestMethods,
  path: string,
  options: {
    qs?: IDataObject;
    body?: IDataObject;
    itemIndex: number;
  },
): Promise<unknown> {
  const credentials = await ctx.getCredentials("lumifyApi");
  const rawBase =
    typeof credentials.baseUrl === "string" && credentials.baseUrl.trim()
      ? credentials.baseUrl.trim().replace(/\/+$/, "")
      : BASE_URL_DEFAULT;

  try {
    return await ctx.helpers.httpRequestWithAuthentication.call(
      ctx,
      "lumifyApi",
      {
        method,
        url: `${rawBase}${path}`,
        qs: options.qs,
        body: options.body,
        json: true,
      },
    );
  } catch (error) {
    const status = extractHttpStatus(error);
    if (status !== null) {
      const friendly = friendlyAuthError(status, extractApiMessage(error));
      if (friendly) {
        throw new NodeApiError(ctx.getNode(), error as JsonObject, {
          message: friendly.message,
          description: friendly.description,
          httpCode: String(status),
          itemIndex: options.itemIndex,
        });
      }
    }
    throw new NodeApiError(ctx.getNode(), error as JsonObject, {
      itemIndex: options.itemIndex,
    });
  }
}

function pushResponse(
  returnData: INodeExecutionData[],
  responseData: unknown,
  itemIndex: number,
  splitIntoItems: boolean,
): void {
  if (splitIntoItems) {
    const items = splitEnvelope(responseData);
    if (items !== null) {
      if (items.length === 0) {
        returnData.push({
          json: { empty: true },
          pairedItem: { item: itemIndex },
        });
        return;
      }
      for (const entry of items) {
        returnData.push({
          json: entry,
          pairedItem: { item: itemIndex },
        });
      }
      return;
    }
  }

  if (Array.isArray(responseData)) {
    for (const entry of responseData) {
      returnData.push({
        json: (entry as IDataObject) ?? {},
        pairedItem: { item: itemIndex },
      });
    }
    return;
  }

  returnData.push({
    json: (responseData as IDataObject) ?? {},
    pairedItem: { item: itemIndex },
  });
}

export class Lumify implements INodeType {
  description: INodeTypeDescription = {
    displayName: "Lumify",
    name: "lumify",
    icon: "file:lumify.svg",
    group: ["transform"],
    version: 1,
    subtitle: '={{$parameter["resource"] + ": " + $parameter["operation"]}}',
    description:
      "Agent-ready sports intelligence: schedules, live scores, odds, public betting splits, and explainable AI bet confidence across 8+ sports",
    defaults: {
      name: "Lumify",
    },
    inputs: [NodeConnectionTypes.Main],
    outputs: [NodeConnectionTypes.Main],
    usableAsTool: true,
    credentials: [
      {
        name: "lumifyApi",
        required: true,
      },
    ],
    // No requestDefaults — this node uses a programmatic execute() path, so
    // n8n never applies declarative requestDefaults (baseURL / headers live in
    // helpers.ts + credential baseUrl instead).
    properties: [
      // ----------------------------------
      //             Resource
      // ----------------------------------
      {
        displayName: "Resource",
        name: "resource",
        type: "options",
        noDataExpression: true,
        options: [
          { name: "Bet Intelligence", value: "intelligence" },
          { name: "Event", value: "event" },
          { name: "Live Score", value: "score" },
          { name: "Odd", value: "odds" },
          { name: "Player", value: "player" },
          { name: "Sport", value: "sport" },
          { name: "Team", value: "team" },
        ],
        default: "event",
      },

      // ----------------------------------
      //             Operations
      // ----------------------------------
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["sport"] } },
        options: [
          {
            name: "List Sports",
            value: "listSports",
            description: "List all supported sports",
            action: "List sports",
          },
          {
            name: "List Seasons",
            value: "listSeasons",
            description: "List seasons for a sport/league",
            action: "List seasons",
          },
        ],
        default: "listSports",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["event"] } },
        options: [
          {
            name: "List Events",
            value: "list",
            description: "List events with optional filters",
            action: "List events",
          },
          {
            name: "Get Event",
            value: "get",
            description: "Get a single event by ID",
            action: "Get an event",
          },
          {
            name: "Get Many Events (Batch)",
            value: "batch",
            description: "Get multiple events by ID in one call",
            action: "Get many events",
          },
          {
            name: "Search (Natural Language)",
            value: "query",
            description:
              'Free-text event search, e.g. "live nfl games today"',
            action: "Search events",
          },
        ],
        default: "list",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["odds"] } },
        options: [
          {
            name: "Get Odds",
            value: "get",
            description: "Get current betting odds for an event",
            action: "Get odds",
          },
          {
            name: "Get Odds History",
            value: "history",
            description: "Get line movement history for an event",
            action: "Get odds history",
          },
        ],
        default: "get",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["score"] } },
        options: [
          {
            name: "Get Live Score",
            value: "get",
            description: "Get an event's current score",
            action: "Get live score",
          },
        ],
        default: "get",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["intelligence"] } },
        options: [
          {
            name: "Get Bet Intelligence",
            value: "get",
            description:
              "Get explainable AI bet confidence (signals, bets, narratives) for an event",
            action: "Get bet intelligence",
          },
          {
            name: "Get Betting Splits",
            value: "splits",
            description: "Get public betting splits for an event",
            action: "Get betting splits",
          },
        ],
        default: "get",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["team"] } },
        options: [
          {
            name: "List Teams",
            value: "list",
            description: "List teams with optional filters",
            action: "List teams",
          },
          {
            name: "Get Team",
            value: "get",
            description: "Get a single team by ID",
            action: "Get a team",
          },
        ],
        default: "list",
      },
      {
        displayName: "Operation",
        name: "operation",
        type: "options",
        noDataExpression: true,
        displayOptions: { show: { resource: ["player"] } },
        options: [
          {
            name: "List Players",
            value: "list",
            description: "List players with optional filters",
            action: "List players",
          },
          {
            name: "Get Player",
            value: "get",
            description: "Get a single player by ID",
            action: "Get a player",
          },
          {
            name: "Get Player Events",
            value: "events",
            description: "List a player's events",
            action: "Get player events",
          },
        ],
        default: "list",
      },

      // ----------------------------------
      //         Shared ID fields
      // ----------------------------------
      {
        displayName: "Event ID",
        name: "eventId",
        type: "number",
        default: 0,
        required: true,
        displayOptions: {
          show: {
            resource: ["event", "odds", "score", "intelligence"],
            operation: ["get", "history", "splits"],
          },
        },
        description: "The Lumify event ID (must be a positive integer)",
      },
      {
        displayName: "Event IDs",
        name: "eventIds",
        type: "string",
        default: "",
        required: true,
        displayOptions: { show: { resource: ["event"], operation: ["batch"] } },
        placeholder: "12345,12346,12347",
        description: `Comma-separated list of Lumify event IDs (max ${BATCH_MAX_IDS})`,
      },
      {
        displayName: "Team ID",
        name: "teamId",
        type: "number",
        default: 0,
        required: true,
        displayOptions: { show: { resource: ["team"], operation: ["get"] } },
        description: "The Lumify team ID (must be a positive integer)",
      },
      {
        displayName: "Player ID",
        name: "playerId",
        type: "number",
        default: 0,
        required: true,
        displayOptions: {
          show: { resource: ["player"], operation: ["get", "events"] },
        },
        description: "The Lumify player ID (must be a positive integer)",
      },

      // ----------------------------------
      //   Sport: List Seasons
      // ----------------------------------
      {
        displayName: "Sport",
        name: "sportSlug",
        type: "string",
        default: "",
        displayOptions: {
          show: { resource: ["sport"], operation: ["listSeasons"] },
        },
        placeholder: "nfl",
        description: "Sport slug, e.g. nfl, nba, mlb, nhl, tennis, soccer",
      },
      {
        displayName: "Current Only",
        name: "currentOnly",
        type: "boolean",
        default: false,
        displayOptions: {
          show: { resource: ["sport"], operation: ["listSeasons"] },
        },
        description: "Whether to return only currently active seasons",
      },

      // ----------------------------------
      //   Event: Search (Natural Language)
      // ----------------------------------
      {
        displayName: "Query",
        name: "queryText",
        type: "string",
        default: "",
        required: true,
        displayOptions: { show: { resource: ["event"], operation: ["query"] } },
        placeholder: "e.g. live nfl games today",
        description: 'Free text search, e.g. "college basketball this week"',
      },
      {
        displayName: "Limit",
        name: "queryLimit",
        type: "number",
        default: 25,
        typeOptions: { minValue: 1, maxValue: 100 },
        displayOptions: { show: { resource: ["event"], operation: ["query"] } },
        description: "Max results to return (1-100)",
      },

      // ----------------------------------
      //   Event: List
      // ----------------------------------
      {
        displayName: "Filters",
        name: "eventListFilters",
        type: "collection",
        placeholder: "Add Filter",
        default: {},
        displayOptions: { show: { resource: ["event"], operation: ["list"] } },
        options: [
          {
            displayName: "After ID",
            name: "after_id",
            type: "number",
            default: 0,
            description:
              "Cursor pagination: return events with ID > after_id. Use next_after_id from the previous response",
          },
          {
            displayName: "Date",
            name: "date",
            type: "string",
            default: "",
            placeholder: "2026-08-01",
            description: "UTC date YYYY-MM-DD (single day)",
          },
          {
            displayName: "From Date",
            name: "from",
            type: "string",
            default: "",
            placeholder: "2026-08-01",
            description: "UTC start date YYYY-MM-DD",
          },
          {
            displayName: "Include Scores",
            name: "include_scores",
            type: "boolean",
            default: false,
            description:
              "Whether to inline participants + scores in each event (small result sets only, ≤ 200 events)",
          },
          {
            displayName: "League",
            name: "league",
            type: "string",
            default: "",
            placeholder: "nfl",
            description: "League slug, e.g. nfl, nba, atp, fifa_world_cup",
          },
          {
            displayName: "Limit",
            name: "limit",
            type: "number",
            default: 50,
            typeOptions: { minValue: 1, maxValue: 100 },
            description: "Max number of results to return",
          },
          {
            displayName: "Only Events With Recommended Bets",
            name: "has_recommend",
            type: "boolean",
            default: false,
          },
          {
            displayName: "Season ID",
            name: "season_id",
            type: "number",
            default: 0,
            description: "Filter by season ID (leave 0 / unset to skip)",
          },
          {
            displayName: "Sort",
            name: "sort",
            type: "options",
            options: [
              { name: "Status (Live First)", value: "status" },
              { name: "Time (Chronological)", value: "time" },
            ],
            default: "time",
          },
          {
            displayName: "Sport",
            name: "sport",
            type: "string",
            default: "",
            placeholder: "nfl",
            description: "Sport slug, e.g. nfl, nba, mlb, nhl, tennis, soccer",
          },
          {
            displayName: "Status",
            name: "status",
            type: "options",
            options: [
              { name: "Any", value: "" },
              { name: "Cancelled", value: "cancelled" },
              { name: "Final", value: "final" },
              { name: "In Progress", value: "inprogress" },
              { name: "Postponed", value: "postponed" },
              { name: "Scheduled", value: "scheduled" },
            ],
            default: "",
          },
          {
            displayName: "Team ID",
            name: "team_id",
            type: "number",
            default: 0,
            description:
              "Filter to events where this team participates. Resolve IDs via List Teams. Leave 0 / unset to skip",
          },
          {
            displayName: "To Date",
            name: "to",
            type: "string",
            default: "",
            placeholder: "2026-08-07",
            description: "UTC end date YYYY-MM-DD (inclusive)",
          },
        ],
      },

      // ----------------------------------
      //   Event: Get
      // ----------------------------------
      {
        displayName: "Options",
        name: "eventGetOptions",
        type: "collection",
        placeholder: "Add Option",
        default: {},
        displayOptions: { show: { resource: ["event"], operation: ["get"] } },
        options: [
          {
            displayName: "Include Odds",
            name: "include_odds",
            type: "boolean",
            default: false,
            description:
              "Whether to inline current odds (all bookmakers). Costs +1 credit",
          },
          {
            displayName: "Include Bet Intelligence",
            name: "include_intelligence",
            type: "boolean",
            default: false,
            description:
              "Whether to inline bet intelligence (signals, bets, narratives). Costs +1 credit",
          },
          {
            displayName: "Bookmaker",
            name: "bookmaker",
            type: "string",
            default: "",
            placeholder: "pinnacle",
            description:
              "Bookmaker for market prices when Include Bet Intelligence is on. E.g. pinnacle, fanduel, draftkings",
          },
        ],
      },

      // ----------------------------------
      //   Event: Batch options
      // ----------------------------------
      {
        displayName: "Options",
        name: "eventBatchOptions",
        type: "collection",
        placeholder: "Add Option",
        default: {},
        displayOptions: { show: { resource: ["event"], operation: ["batch"] } },
        options: [
          {
            displayName: "Include Odds",
            name: "include_odds",
            type: "boolean",
            default: false,
            description:
              "Whether to inline current odds on each event (+1 credit per event when available)",
          },
          {
            displayName: "Include Bet Intelligence",
            name: "include_intelligence",
            type: "boolean",
            default: false,
            description:
              "Whether to inline bet intelligence on each event (+1 credit per event when available)",
          },
          {
            displayName: "Bookmaker",
            name: "bookmaker",
            type: "string",
            default: "",
            placeholder: "pinnacle",
            description:
              "Bookmaker for market prices when Include Bet Intelligence is on",
          },
        ],
      },

      // ----------------------------------
      //   Odd: Get / History
      // ----------------------------------
      {
        displayName: "Bookmaker",
        name: "oddsBookmaker",
        type: "string",
        default: "",
        displayOptions: {
          show: { resource: ["odds"], operation: ["get", "history"] },
        },
        placeholder: "pinnacle",
        description:
          'Bookmaker filter. Default: pinnacle. Use "all" or a comma-separated list (e.g. fanduel,draftkings) for multiple books',
      },
      {
        displayName: "Limit",
        name: "oddsHistoryLimit",
        type: "number",
        default: 50,
        typeOptions: { minValue: 1, maxValue: 200 },
        displayOptions: {
          show: { resource: ["odds"], operation: ["history"] },
        },
        description: "Max line movements to return (1-200)",
      },

      // ----------------------------------
      //   Bet Intelligence: Get
      // ----------------------------------
      {
        displayName: "Bookmaker",
        name: "intelligenceBookmaker",
        type: "string",
        default: "",
        displayOptions: {
          show: { resource: ["intelligence"], operation: ["get"] },
        },
        placeholder: "pinnacle",
        description:
          "Bookmaker for market.price / market.line. Overrides the system default (pinnacle)",
      },

      // ----------------------------------
      //   Team: List
      // ----------------------------------
      {
        displayName: "Filters",
        name: "teamListFilters",
        type: "collection",
        placeholder: "Add Filter",
        default: {},
        displayOptions: { show: { resource: ["team"], operation: ["list"] } },
        options: [
          {
            displayName: "Active Only",
            name: "active",
            type: "boolean",
            default: true,
          },
          {
            displayName: "After ID",
            name: "after_id",
            type: "number",
            default: 0,
            description:
              "Cursor pagination: last team ID from the previous page (next_after_id)",
          },
          {
            displayName: "Conference",
            name: "conference",
            type: "string",
            default: "",
          },
          {
            displayName: "Country",
            name: "country",
            type: "string",
            default: "",
            placeholder: "USA",
            description: "ISO country code, e.g. USA",
          },
          {
            displayName: "Division",
            name: "division",
            type: "string",
            default: "",
          },
          {
            displayName: "League",
            name: "league",
            type: "string",
            default: "",
          },
          {
            displayName: "Limit",
            name: "limit",
            type: "number",
            default: 50,
            typeOptions: { minValue: 1, maxValue: 100 },
            description: "Max number of results to return",
          },
          {
            displayName: "Name Search",
            name: "q",
            type: "string",
            default: "",
            description: "Team name search (partial match)",
          },
          { displayName: "Sport", name: "sport", type: "string", default: "" },
        ],
      },

      // ----------------------------------
      //   Player: List
      // ----------------------------------
      {
        displayName: "Filters",
        name: "playerListFilters",
        type: "collection",
        placeholder: "Add Filter",
        default: {},
        displayOptions: { show: { resource: ["player"], operation: ["list"] } },
        options: [
          {
            displayName: "Active Only",
            name: "active",
            type: "boolean",
            default: true,
          },
          {
            displayName: "After ID",
            name: "after_id",
            type: "number",
            default: 0,
            description:
              "Cursor pagination: last player ID from the previous page (next_after_id)",
          },
          {
            displayName: "Country",
            name: "country",
            type: "string",
            default: "",
            placeholder: "USA",
            description: "ISO 3166-1 alpha-3 country code, e.g. USA",
          },
          {
            displayName: "Limit",
            name: "limit",
            type: "number",
            default: 50,
            typeOptions: { minValue: 1, maxValue: 100 },
            description: "Max number of results to return",
          },
          {
            displayName: "Name Search",
            name: "q",
            type: "string",
            default: "",
            description: "Name search (partial match)",
          },
          {
            displayName: "Ranked Only",
            name: "ranked",
            type: "boolean",
            default: false,
            description: "Whether to only return players with a tennis ranking",
          },
          {
            displayName: "Sport",
            name: "sport",
            type: "string",
            default: "",
            placeholder: "tennis",
          },
        ],
      },

      // ----------------------------------
      //   Player: Get Events
      // ----------------------------------
      {
        displayName: "Filters",
        name: "playerEventsFilters",
        type: "collection",
        placeholder: "Add Filter",
        default: {},
        displayOptions: {
          show: { resource: ["player"], operation: ["events"] },
        },
        options: [
          {
            displayName: "After ID",
            name: "after_id",
            type: "number",
            default: 0,
            description:
              "Cursor pagination: last event ID from the previous page (next_after_id)",
          },
          {
            displayName: "From Date",
            name: "from",
            type: "string",
            default: "",
            placeholder: "2026-08-01",
          },
          {
            displayName: "Limit",
            name: "limit",
            type: "number",
            default: 50,
            typeOptions: { minValue: 1, maxValue: 100 },
            description: "Max number of results to return",
          },
          {
            displayName: "Status",
            name: "status",
            type: "options",
            options: [
              { name: "Any", value: "" },
              { name: "Final", value: "final" },
              { name: "In Progress", value: "inprogress" },
              { name: "Scheduled", value: "scheduled" },
            ],
            default: "",
          },
          {
            displayName: "To Date",
            name: "to",
            type: "string",
            default: "",
            placeholder: "2026-08-07",
          },
        ],
      },

      // ----------------------------------
      //   Split Into Items (list-like ops)
      // ----------------------------------
      {
        displayName: "Split Into Items",
        name: "splitIntoItems",
        type: "boolean",
        default: false,
        displayOptions: {
          show: {
            resource: ["sport", "event", "team", "player"],
            operation: [
              "listSports",
              "listSeasons",
              "list",
              "batch",
              "query",
              "events",
            ],
          },
        },
        description:
          "Whether to emit one n8n item per row (event/team/player/sport/season) instead of the full API envelope. Leave off when you need next_after_id / has_more for pagination",
      },
    ],
  };

  async execute(this: IExecuteFunctions): Promise<INodeExecutionData[][]> {
    const items = this.getInputData();
    const returnData: INodeExecutionData[] = [];

    const resource = this.getNodeParameter("resource", 0) as string;
    const operation = this.getNodeParameter("operation", 0) as string;

    for (let i = 0; i < items.length; i++) {
      try {
        let responseData: unknown;
        let splitIntoItems = false;

        const wantsSplit =
          (resource === "sport" &&
            (operation === "listSports" || operation === "listSeasons")) ||
          (resource === "event" &&
            (operation === "list" ||
              operation === "batch" ||
              operation === "query")) ||
          (resource === "team" && operation === "list") ||
          (resource === "player" &&
            (operation === "list" || operation === "events"));

        if (wantsSplit) {
          splitIntoItems = this.getNodeParameter(
            "splitIntoItems",
            i,
            false,
          ) as boolean;
        }

        if (resource === "sport") {
          if (operation === "listSports") {
            responseData = await apiRequest(this, "GET", "/v1/sports", {
              itemIndex: i,
            });
          } else if (operation === "listSeasons") {
            const sportSlug = this.getNodeParameter(
              "sportSlug",
              i,
              "",
            ) as string;
            const currentOnly = this.getNodeParameter(
              "currentOnly",
              i,
              false,
            ) as boolean;
            responseData = await apiRequest(this, "GET", "/v1/seasons", {
              qs: withDefinedValues({
                sport: sportSlug,
                current_only: currentOnly || undefined,
              }),
              itemIndex: i,
            });
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown sport operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else if (resource === "event") {
          if (operation === "list") {
            const filters = this.getNodeParameter(
              "eventListFilters",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(this, "GET", "/v1/events", {
              qs: withDefinedValues(filters),
              itemIndex: i,
            });
          } else if (operation === "get") {
            const eventId = this.getNodeParameter("eventId", i);
            try {
              validatePositiveId(eventId, "Event ID");
            } catch (err) {
              throw new NodeOperationError(
                this.getNode(),
                (err as Error).message,
                { itemIndex: i },
              );
            }
            const options = this.getNodeParameter(
              "eventGetOptions",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/events/${eventId}`,
              {
                qs: withDefinedValues(options),
                itemIndex: i,
              },
            );
          } else if (operation === "batch") {
            const eventIdsRaw = this.getNodeParameter("eventIds", i) as string;
            let eventIds: number[];
            try {
              eventIds = validateBatchIds(parseIdList(eventIdsRaw));
            } catch (err) {
              throw new NodeOperationError(
                this.getNode(),
                (err as Error).message,
                { itemIndex: i },
              );
            }
            const batchOptions = this.getNodeParameter(
              "eventBatchOptions",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(this, "POST", "/v1/events/batch", {
              body: withDefinedValues({
                event_ids: eventIds,
                ...batchOptions,
              }),
              itemIndex: i,
            });
          } else if (operation === "query") {
            const query = this.getNodeParameter("queryText", i) as string;
            const limit = this.getNodeParameter("queryLimit", i, 25) as number;
            responseData = await apiRequest(this, "POST", "/v1/query", {
              body: withDefinedValues({ query, limit }),
              itemIndex: i,
            });
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown event operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else if (resource === "odds") {
          const eventId = this.getNodeParameter("eventId", i);
          try {
            validatePositiveId(eventId, "Event ID");
          } catch (err) {
            throw new NodeOperationError(
              this.getNode(),
              (err as Error).message,
              { itemIndex: i },
            );
          }
          if (operation === "get") {
            const bookmaker = this.getNodeParameter(
              "oddsBookmaker",
              i,
              "",
            ) as string;
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/events/${eventId}/odds`,
              {
                qs: withDefinedValues({ bookmaker }),
                itemIndex: i,
              },
            );
          } else if (operation === "history") {
            const bookmaker = this.getNodeParameter(
              "oddsBookmaker",
              i,
              "",
            ) as string;
            const limit = this.getNodeParameter(
              "oddsHistoryLimit",
              i,
              50,
            ) as number;
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/events/${eventId}/odds/history`,
              {
                qs: withDefinedValues({ bookmaker, limit }),
                itemIndex: i,
              },
            );
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown odds operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else if (resource === "score") {
          const eventId = this.getNodeParameter("eventId", i);
          try {
            validatePositiveId(eventId, "Event ID");
          } catch (err) {
            throw new NodeOperationError(
              this.getNode(),
              (err as Error).message,
              { itemIndex: i },
            );
          }
          responseData = await apiRequest(
            this,
            "GET",
            `/v1/events/${eventId}/score`,
            { itemIndex: i },
          );
        } else if (resource === "intelligence") {
          const eventId = this.getNodeParameter("eventId", i);
          try {
            validatePositiveId(eventId, "Event ID");
          } catch (err) {
            throw new NodeOperationError(
              this.getNode(),
              (err as Error).message,
              { itemIndex: i },
            );
          }
          if (operation === "get") {
            const bookmaker = this.getNodeParameter(
              "intelligenceBookmaker",
              i,
              "",
            ) as string;
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/events/${eventId}/intelligence`,
              {
                qs: withDefinedValues({ bookmaker }),
                itemIndex: i,
              },
            );
          } else if (operation === "splits") {
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/events/${eventId}/splits`,
              { itemIndex: i },
            );
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown intelligence operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else if (resource === "team") {
          if (operation === "list") {
            const filters = this.getNodeParameter(
              "teamListFilters",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(this, "GET", "/v1/teams", {
              qs: withDefinedValues(filters),
              itemIndex: i,
            });
          } else if (operation === "get") {
            const teamId = this.getNodeParameter("teamId", i);
            try {
              validatePositiveId(teamId, "Team ID");
            } catch (err) {
              throw new NodeOperationError(
                this.getNode(),
                (err as Error).message,
                { itemIndex: i },
              );
            }
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/teams/${teamId}`,
              { itemIndex: i },
            );
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown team operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else if (resource === "player") {
          if (operation === "list") {
            const filters = this.getNodeParameter(
              "playerListFilters",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(this, "GET", "/v1/players", {
              qs: withDefinedValues(filters),
              itemIndex: i,
            });
          } else if (operation === "get") {
            const playerId = this.getNodeParameter("playerId", i);
            try {
              validatePositiveId(playerId, "Player ID");
            } catch (err) {
              throw new NodeOperationError(
                this.getNode(),
                (err as Error).message,
                { itemIndex: i },
              );
            }
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/players/${playerId}`,
              { itemIndex: i },
            );
          } else if (operation === "events") {
            const playerId = this.getNodeParameter("playerId", i);
            try {
              validatePositiveId(playerId, "Player ID");
            } catch (err) {
              throw new NodeOperationError(
                this.getNode(),
                (err as Error).message,
                { itemIndex: i },
              );
            }
            const filters = this.getNodeParameter(
              "playerEventsFilters",
              i,
              {},
            ) as IDataObject;
            responseData = await apiRequest(
              this,
              "GET",
              `/v1/players/${playerId}/events`,
              {
                qs: withDefinedValues(filters),
                itemIndex: i,
              },
            );
          } else {
            throw new NodeOperationError(
              this.getNode(),
              `Unknown player operation: ${operation}`,
              { itemIndex: i },
            );
          }
        } else {
          throw new NodeOperationError(
            this.getNode(),
            `Unknown resource: ${resource}`,
            { itemIndex: i },
          );
        }

        pushResponse(returnData, responseData, i, splitIntoItems);
      } catch (error) {
        if (this.continueOnFail()) {
          returnData.push({
            json: { error: (error as Error).message },
            pairedItem: { item: i },
          });
          continue;
        }
        throw new NodeApiError(this.getNode(), error as JsonObject, {
          itemIndex: i,
        });
      }
    }

    return [returnData];
  }
}
