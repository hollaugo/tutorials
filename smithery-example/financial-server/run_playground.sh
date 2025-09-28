#!/bin/bash
# Run the financial MCP server playground

cd "$(dirname "$0")"
uv run python -m smithery.cli.playground financial_server.server:create_server
