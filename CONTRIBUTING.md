# Contributing

Thanks for your interest in Lumify's client libraries.

## How this repository is maintained

This repo is the public home for Lumify's client SDKs (`@lumifyai/sdk`,
`lumify-sdk`), the MCP stdio bridge (`@lumifyai/mcp`), and developer docs.
The Lumify team maintains the canonical source and publishes updates here
alongside each npm/PyPI release. The published packages track this repo, so
`clients/**` here matches what you install from the registries.

## Reporting issues

Bug reports and feature requests are very welcome —
[open an issue](https://github.com/lumifyai/lumify/issues). Please include:

- the package and version (`@lumifyai/sdk@x.y.z`, `lumify-sdk==x.y.z`, …),
- your runtime version (Node, Python),
- a minimal reproduction, and
- what you expected vs. what happened.

**Never paste your API key** (`lmfy-...`) or any `Authorization` header into an
issue, log, or reproduction.

## Pull requests

Small, focused PRs — bug fixes, docs corrections, examples — are welcome.
Before starting anything substantial, please open an issue first so we can
align on the approach: some generated files (e.g. the SDK model types) come
from an internal source of truth, so certain changes are easier to land when
we coordinate up front. By submitting a PR you agree your contribution is
licensed under the [MIT License](./LICENSE).

## Security

Please do **not** open public issues for security vulnerabilities. Email
**security@lumify.ai** (or dev@lumify.ai) with details and we'll respond
promptly.
