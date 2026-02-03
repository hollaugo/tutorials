#!/bin/bash
# Start the MCP server with STDIO transport

cd "$(dirname "$0")/.."
python server.py stdio
