#!/bin/bash
# Run the financial MCP server playground

cd "$(dirname "$0")"
export PYTHONPATH=src
uv run python -m smithery.cli.playground financial_server.server:create_server
