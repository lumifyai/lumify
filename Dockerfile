# Glama server-listing build recipe.
#
# Runs the @lumifyai/mcp stdio bridge, which proxies MCP JSON-RPC to the hosted
# Lumify server at https://lumify.ai/mcp. The bridge has zero runtime
# dependencies (Node built-ins only), so there is no install/build step.
#
# During indexing, Glama starts this container and speaks the MCP stdio
# transport. The handshake, tools/list, resources/list, and prompts/list all
# work without an API key, so Glama can introspect the full capability surface
# (tools, resources, prompts) unauthenticated. Provide LUMIFY_API_KEY at runtime
# only if you want tools/call to execute live requests.
FROM node:20-slim

WORKDIR /app

COPY clients/lumify-mcp/ ./clients/lumify-mcp/

# Speaks MCP over stdin/stdout; diagnostics go to stderr.
ENTRYPOINT ["node", "clients/lumify-mcp/bin/lumify-mcp.js"]
