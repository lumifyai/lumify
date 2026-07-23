import type {
  ICredentialDataDecryptedObject,
  ICredentialTestRequest,
  ICredentialType,
  IHttpRequestOptions,
  INodeProperties,
  Icon,
} from "n8n-workflow";

import {
  BASE_URL_DEFAULT,
  INSTANT_KEY_URL,
  clientHeaders,
  normalizeApiKey,
} from "../nodes/Lumify/helpers";

export class LumifyApi implements ICredentialType {
  name = "lumifyApi";

  displayName = "Lumify API";

  icon: Icon = "file:lumify.svg";

  documentationUrl = "https://lumify.ai/docs/ai";

  properties: INodeProperties[] = [
    {
      displayName: "API Key",
      name: "apiKey",
      type: "string",
      typeOptions: {
        password: true,
      },
      default: "",
      required: true,
      description: `Your Lumify API key (format: lmfy-xxxxx). Paste the key only — do not include a "Bearer " prefix. Grab a free instant key in seconds — no signup, email, or card — at <a href="${INSTANT_KEY_URL}" target="_blank">lumify.ai/docs/ai</a>, or create a persistent account key at <a href="https://lumify.ai/api-keys" target="_blank">lumify.ai/api-keys</a>.`,
    },
    {
      displayName: "Base URL",
      name: "baseUrl",
      type: "string",
      default: BASE_URL_DEFAULT,
      description:
        "Override only for local/staging. Production default is https://lumify.ai.",
    },
  ];

  // Function form so we can strip a pasted "Bearer " prefix and attach client
  // identity headers on every request (including the credential test).
  authenticate = async (
    credentials: ICredentialDataDecryptedObject,
    requestOptions: IHttpRequestOptions,
  ): Promise<IHttpRequestOptions> => {
    const apiKey = normalizeApiKey(credentials.apiKey);
    if (!apiKey) {
      throw new Error(
        `Lumify API key is required. Grab a free instant key at ${INSTANT_KEY_URL}.`,
      );
    }
    requestOptions.headers = {
      ...requestOptions.headers,
      ...clientHeaders(),
      Authorization: `Bearer ${apiKey}`,
    };
    return requestOptions;
  };

  test: ICredentialTestRequest = {
    request: {
      baseURL: "={{$credentials.baseUrl || 'https://lumify.ai'}}",
      url: "/v1/sports",
      method: "GET",
    },
  };
}
