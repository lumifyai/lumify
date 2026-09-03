# Self-Hosting

> **Lumify is a fully managed API.** There is no self-hosted distribution.

Lumify runs as a managed cloud service (Google Cloud Run + Cloud SQL) at
[https://lumify.ai](https://lumify.ai). You do not need to provision or operate any
infrastructure — sign up, create an API key, and start making requests. See the
[Quick Start Guide](quick-start.md).

## Why there is no self-hosted build

The Lumify Sports Intelligence API depends on a continuously running ingest and
analysis platform — scheduled data ingest jobs, live-score pollers, odds/splits
feeds, and an LLM-backed analysis pipeline — plus several third-party data
subscriptions. These are operated centrally and are not packaged for on-premise
deployment.

## Enterprise & dedicated deployments

For enterprise requirements such as dedicated capacity, custom rate limits, private
networking, data residency, or volume/historical data access, contact
[enterprise@lumify.ai](mailto:enterprise@lumify.ai).

## Next Steps

- [Quick Start Guide](quick-start.md) — make your first API call
- [API Reference](https://lumify.ai/docs) — full endpoint documentation
