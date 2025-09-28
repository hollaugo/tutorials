#!/bin/bash
# Run the financial MCP server playground

cd "$(dirname "$0")"
uv run python -m smithery.cli.playground server:create_server
