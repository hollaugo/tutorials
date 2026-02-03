#!/bin/bash
# Start the MCP server with Streamable HTTP transport

cd "$(dirname "$0")/.."

PORT=${MCP_PORT:-8000}
echo "Starting Stock Research Server on http://localhost:$PORT"
python server.py http
