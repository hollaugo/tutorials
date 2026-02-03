#!/bin/bash
# Start MCP Inspector to test the server
# Usage: ./scripts/inspect.sh [stdio|http]

cd "$(dirname "$0")/.."

TRANSPORT=${1:-stdio}

if [ "$TRANSPORT" = "http" ]; then
    PORT=${MCP_PORT:-8000}
    echo "Opening MCP Inspector for HTTP server at http://localhost:$PORT/mcp"
    echo "Make sure the server is running: ./scripts/start-http.sh"
    npx @modelcontextprotocol/inspector
else
    echo "Starting MCP Inspector with STDIO transport..."
    npx @modelcontextprotocol/inspector python server.py stdio
fi
